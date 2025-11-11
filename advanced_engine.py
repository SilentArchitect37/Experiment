"""
Advanced Recursive Engine with Improved Numerical Methods

Addresses limitations:
1. RK4 integration (4th order vs 1st order Euler)
2. Adaptive time stepping (removes need for clipping)
3. Energy monitoring and conservation tracking
4. Multiple boundary condition options
5. Double precision option
"""

import numpy as np
from typing import Optional, Tuple, Literal
from dataclasses import dataclass
from recursive_engine import RecursiveEngine, RecursiveParams


@dataclass
class AdvancedParams(RecursiveParams):
    """Extended parameters for advanced methods"""
    # Numerical method
    integration_method: str = 'rk4'  # 'euler', 'rk4', 'adaptive_rk4'

    # Adaptive stepping
    adaptive_dt: bool = False
    dt_min: float = 0.001
    dt_max: float = 0.1
    error_tolerance: float = 1e-4

    # Precision
    dtype: str = 'float64'  # 'float32' or 'float64'

    # Boundary conditions
    boundary_condition: str = 'periodic'  # 'periodic', 'dirichlet', 'neumann'

    # Energy monitoring
    track_energy: bool = True
    energy_warning_threshold: float = 10.0  # Warn if energy grows by this factor


class RK4Engine(RecursiveEngine):
    """
    4th-order Runge-Kutta integration

    Much more accurate than Euler (O(dt^4) vs O(dt))
    Better stability allows larger time steps
    """

    def __init__(self, params: AdvancedParams, n_dims: int = 256):
        self.advanced_params = params

        # Set dtype before calling super().__init__ (which calls reset())
        self.dtype = np.float64 if params.dtype == 'float64' else np.float32

        # Energy tracking
        self.energy_history = []
        self.initial_energy = None

        super().__init__(params, n_dims)

    def reset(self):
        """Initialize with specified dtype"""
        self.mu = np.zeros(self.n_dims, dtype=self.dtype)
        self.mu_prev = np.zeros(self.n_dims, dtype=self.dtype)
        self.t = 0
        self.energy_history.clear()
        self.initial_energy = None

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """
        Laplacian with multiple boundary conditions
        """
        params = self.advanced_params
        dx2 = params.dx ** 2

        if params.boundary_condition == 'periodic':
            # Periodic BC (original method)
            laplacian = (np.roll(mu, 1) - 2 * mu + np.roll(mu, -1)) / dx2

        elif params.boundary_condition == 'dirichlet':
            # Zero BC at boundaries: μ(0) = μ(n-1) = 0
            laplacian = np.zeros_like(mu)
            laplacian[1:-1] = (mu[:-2] - 2*mu[1:-1] + mu[2:]) / dx2
            # Boundaries stay zero

        elif params.boundary_condition == 'neumann':
            # Zero derivative at boundaries: dμ/dx|boundary = 0
            laplacian = np.zeros_like(mu)
            laplacian[1:-1] = (mu[:-2] - 2*mu[1:-1] + mu[2:]) / dx2
            # Forward/backward differences at boundaries
            laplacian[0] = (-2*mu[0] + 2*mu[1]) / dx2
            laplacian[-1] = (2*mu[-2] - 2*mu[-1]) / dx2

        return laplacian

    def compute_rhs(self, mu: np.ndarray, mu_prev: np.ndarray,
                    input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Compute right-hand side: dμ/dt = F(μ)

        F(μ) = g∇²μ - λμ³ + ρ(μ - μ_prev)
        """
        p = self.params

        laplacian = self.compute_laplacian(mu)

        # No clipping in RHS computation - RK4 handles stability
        # But add soft limiting for extreme values
        mu_limited = np.tanh(mu / 10.0) * 10.0  # Soft limit around ±10
        cubic = mu_limited ** 3

        momentum = mu - mu_prev

        input_term = 0.0
        if input_vec is not None:
            input_term = p.eta * input_vec

        rhs = p.g * laplacian - p.lam * cubic + p.rho * momentum + input_term

        return rhs

    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        """
        RK4 integration step

        k1 = f(t, y)
        k2 = f(t + dt/2, y + dt*k1/2)
        k3 = f(t + dt/2, y + dt*k2/2)
        k4 = f(t + dt, y + dt*k3)
        y_new = y + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        """
        p = self.params
        mu = self.mu

        # k1
        k1 = self.compute_rhs(mu, self.mu_prev, input_vec)

        # k2
        mu_temp = mu + p.dt * k1 / 2
        k2 = self.compute_rhs(mu_temp, self.mu_prev, input_vec)

        # k3
        mu_temp = mu + p.dt * k2 / 2
        k3 = self.compute_rhs(mu_temp, self.mu_prev, input_vec)

        # k4
        mu_temp = mu + p.dt * k3
        k4 = self.compute_rhs(mu_temp, self.mu_prev, input_vec)

        # Combine
        mu_new = mu + p.dt / 6.0 * (k1 + 2*k2 + 2*k3 + k4)

        # Track energy
        if self.advanced_params.track_energy:
            self._update_energy(mu_new)

        # Update state
        self.mu_prev = self.mu.copy()
        self.mu = mu_new
        self.t += 1

        return self.mu

    def _update_energy(self, mu: np.ndarray):
        """Track energy and warn if growing unbounded"""
        energy = np.sum(mu ** 2)
        self.energy_history.append(energy)

        if self.initial_energy is None:
            self.initial_energy = energy

        # Check for energy growth
        if len(self.energy_history) > 10:
            current = self.energy_history[-1]
            if self.initial_energy > 0:
                ratio = current / self.initial_energy
                if ratio > self.advanced_params.energy_warning_threshold:
                    import warnings
                    warnings.warn(
                        f"Energy grew by {ratio:.1f}x from initial value. "
                        f"Consider reducing dt or checking parameters."
                    )

    def get_energy_conservation_error(self) -> float:
        """
        Compute relative energy drift

        For conservative systems, this should be small.
        For our dissipative system, energy should decrease.
        """
        if len(self.energy_history) < 2:
            return 0.0

        initial = self.energy_history[0]
        final = self.energy_history[-1]

        if initial > 0:
            return abs(final - initial) / initial
        return 0.0


class AdaptiveRK4Engine(RK4Engine):
    """
    RK4 with adaptive time stepping

    Automatically adjusts dt based on local error estimates.
    Removes need for hard clipping by preventing instability.
    """

    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Adaptive RK4 step with error control

        Takes two steps: one full step and two half steps
        Estimates error from difference
        Adjusts dt accordingly
        """
        p = self.advanced_params

        # Maximum iterations to find good dt
        max_iterations = 10

        for iteration in range(max_iterations):
            # Try full step with current dt
            mu_full = self._rk4_step(self.mu, self.mu_prev, p.dt, input_vec)

            # Try two half steps
            mu_half1 = self._rk4_step(self.mu, self.mu_prev, p.dt/2, input_vec)
            mu_half2 = self._rk4_step(mu_half1, self.mu_prev, p.dt/2, input_vec)

            # Estimate error (Richardson extrapolation)
            error = np.max(np.abs(mu_half2 - mu_full))

            # If error acceptable, accept step
            if error < p.error_tolerance:
                self.mu_prev = self.mu.copy()
                self.mu = mu_half2  # Use more accurate half-step result
                self.t += 1

                # Track energy
                if p.track_energy:
                    self._update_energy(self.mu)

                # Increase dt for next step (but not too much)
                if error < p.error_tolerance / 10 and p.dt < p.dt_max:
                    p.dt = min(p.dt * 1.2, p.dt_max)

                return self.mu

            # Error too large, reduce dt
            p.dt = max(p.dt * 0.5, p.dt_min)

            if p.dt <= p.dt_min:
                # At minimum dt, accept anyway
                self.mu_prev = self.mu.copy()
                self.mu = mu_half2
                self.t += 1

                if p.track_energy:
                    self._update_energy(self.mu)

                import warnings
                warnings.warn(f"Adaptive stepping at minimum dt={p.dt_min}")

                return self.mu

        raise RuntimeError("Adaptive stepping failed to converge")

    def _rk4_step(self, mu: np.ndarray, mu_prev: np.ndarray,
                  dt: float, input_vec: Optional[np.ndarray]) -> np.ndarray:
        """Single RK4 step with specified dt"""
        # Temporarily override dt
        original_dt = self.params.dt
        self.params.dt = dt

        # k1
        k1 = self.compute_rhs(mu, mu_prev, input_vec)

        # k2
        mu_temp = mu + dt * k1 / 2
        k2 = self.compute_rhs(mu_temp, mu_prev, input_vec)

        # k3
        mu_temp = mu + dt * k2 / 2
        k3 = self.compute_rhs(mu_temp, mu_prev, input_vec)

        # k4
        mu_temp = mu + dt * k3
        k4 = self.compute_rhs(mu_temp, mu_prev, input_vec)

        # Combine
        mu_new = mu + dt / 6.0 * (k1 + 2*k2 + 2*k3 + k4)

        # Restore dt
        self.params.dt = original_dt

        return mu_new


class FFTEngine_RK4(RK4Engine):
    """
    RK4 with FFT-based Laplacian

    Combines best of both: spectral accuracy + high-order time integration
    """

    def __init__(self, params: AdvancedParams, n_dims: int = 256):
        super().__init__(params, n_dims)

        # Precompute wavenumbers for spectral Laplacian
        k = np.fft.fftfreq(n_dims, d=params.dx) * 2 * np.pi
        self.k_squared = -(k ** 2)

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """FFT-based spectral Laplacian (only for periodic BC)"""
        if self.advanced_params.boundary_condition != 'periodic':
            # Fall back to finite differences for non-periodic
            return super().compute_laplacian(mu)

        # Spectral Laplacian
        mu_hat = np.fft.fft(mu)
        laplacian_hat = self.k_squared * mu_hat
        laplacian = np.fft.ifft(laplacian_hat).real

        return laplacian


def create_advanced_engine(
    optimization: Literal['rk4', 'adaptive_rk4', 'fft_rk4'] = 'fft_rk4',
    params: Optional[AdvancedParams] = None,
    n_dims: int = 256
) -> RK4Engine:
    """Factory function for advanced engines"""

    if params is None:
        params = AdvancedParams()

    if optimization == 'rk4':
        return RK4Engine(params, n_dims)
    elif optimization == 'adaptive_rk4':
        params.adaptive_dt = True
        return AdaptiveRK4Engine(params, n_dims)
    elif optimization == 'fft_rk4':
        return FFTEngine_RK4(params, n_dims)
    else:
        raise ValueError(f"Unknown optimization: {optimization}")


if __name__ == "__main__":
    print("=== Advanced Engine Demo ===\n")

    # Test RK4 vs Euler accuracy
    print("1. RK4 vs Euler Accuracy Test")
    print("-" * 50)

    from recursive_engine import FFTEngine, RecursiveParams

    # Standard Euler
    params_euler = RecursiveParams(g=0.15, lam=0.3, rho=0.4, dt=0.01)
    engine_euler = FFTEngine(params_euler, 128)
    engine_euler.mu = np.random.randn(128) * 0.5

    # RK4 with same dt
    params_rk4 = AdvancedParams(g=0.15, lam=0.3, rho=0.4, dt=0.01)
    engine_rk4 = FFTEngine_RK4(params_rk4, 128)
    engine_rk4.mu = engine_euler.mu.copy()

    # Run 100 steps
    for _ in range(100):
        engine_euler.step()
        engine_rk4.step()

    # Compare
    diff = np.linalg.norm(engine_rk4.mu - engine_euler.mu)
    print(f"Difference after 100 steps: {diff:.6f}")
    print(f"RK4 energy: {np.sum(engine_rk4.mu**2):.4f}")
    print(f"Euler energy: {np.sum(engine_euler.mu**2):.4f}")

    # Test adaptive stepping
    print("\n2. Adaptive Time Stepping Test")
    print("-" * 50)

    params_adaptive = AdvancedParams(
        g=0.15, lam=0.3, rho=0.4,
        dt=0.01,
        adaptive_dt=True,
        dt_min=0.001,
        dt_max=0.05,
        error_tolerance=1e-4
    )

    engine_adaptive = AdaptiveRK4Engine(params_adaptive, 128)
    engine_adaptive.mu = np.random.randn(128) * 0.5

    dt_history = []
    for i in range(100):
        engine_adaptive.step()
        dt_history.append(params_adaptive.dt)

    print(f"Initial dt: {dt_history[0]:.6f}")
    print(f"Final dt: {dt_history[-1]:.6f}")
    print(f"Mean dt: {np.mean(dt_history):.6f}")
    print(f"Min dt: {np.min(dt_history):.6f}")
    print(f"Max dt: {np.max(dt_history):.6f}")

    # Test boundary conditions
    print("\n3. Boundary Condition Test")
    print("-" * 50)

    for bc in ['periodic', 'dirichlet', 'neumann']:
        params_bc = AdvancedParams(g=0.15, lam=0.3, rho=0.4,
                                   boundary_condition=bc)
        engine = RK4Engine(params_bc, 64)
        engine.mu = np.random.randn(64) * 0.5

        for _ in range(50):
            engine.step()

        print(f"{bc:10s}: μ[0]={engine.mu[0]:.4f}, μ[-1]={engine.mu[-1]:.4f}, "
              f"energy={np.sum(engine.mu**2):.4f}")

    # Test double precision
    print("\n4. Precision Test")
    print("-" * 50)

    for dtype in ['float32', 'float64']:
        params_prec = AdvancedParams(g=0.15, lam=0.3, rho=0.4, dtype=dtype)
        engine = FFTEngine_RK4(params_prec, 128)
        engine.mu = np.random.randn(128).astype(
            np.float64 if dtype == 'float64' else np.float32
        ) * 0.5

        for _ in range(100):
            engine.step()

        print(f"{dtype}: {engine.mu.dtype}, final energy={np.sum(engine.mu**2):.10f}")

    print("\n=== Tests Complete ===")
