"""
Optimized Recursive Dialogue Engine Core
Based on: μ_{t+1} = μ_t + g∇²μ_t - λμ_t³ + ρ(μt - μ{t-1}) + η·x_t

Optimization levels:
1. Naive: Direct implementation with loops
2. Vectorized: NumPy operations
3. FFT: Spectral Laplacian for O(n log n) complexity
4. GPU: PyTorch GPU acceleration
"""

import numpy as np
from typing import Optional, Tuple, Literal
from dataclasses import dataclass
import time

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. GPU acceleration disabled.")


@dataclass
class RecursiveParams:
    """Parameters for the recursive dynamics equation"""
    g: float = 0.1        # Diffusion coefficient (Laplacian weight)
    lam: float = 0.5      # Cubic nonlinearity strength
    rho: float = 0.3      # Momentum coefficient
    eta: float = 0.05     # Input coupling strength
    dt: float = 0.01      # Time step

    # Grid parameters
    dx: float = 1.0       # Spatial discretization


class RecursiveEngine:
    """Base class for recursive dynamics computation"""

    def __init__(self, params: RecursiveParams, n_dims: int = 256):
        self.params = params
        self.n_dims = n_dims

        # State variables
        self.mu = None
        self.mu_prev = None
        self.t = 0

        self.reset()

    def reset(self):
        """Initialize state"""
        self.mu = np.zeros(self.n_dims, dtype=np.float32)
        self.mu_prev = np.zeros(self.n_dims, dtype=np.float32)
        self.t = 0

    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        """Single time step - to be overridden by subclasses"""
        raise NotImplementedError

    def compute_recursive_entropy(self, mu: np.ndarray) -> float:
        """S_R = -k_R Σ μ² ln(μ² + ε)"""
        eps = 1e-8
        mu_sq = mu * mu
        entropy = -np.sum(mu_sq * np.log(mu_sq + eps))
        return entropy


class NaiveEngine(RecursiveEngine):
    """Naive implementation with explicit loops - O(n²) for Laplacian"""

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """Finite difference Laplacian: ∇²μ ≈ (μ[i+1] - 2μ[i] + μ[i-1]) / dx²"""
        n = len(mu)
        laplacian = np.zeros_like(mu)
        dx2 = self.params.dx ** 2

        for i in range(n):
            # Periodic boundary conditions
            left = mu[(i - 1) % n]
            center = mu[i]
            right = mu[(i + 1) % n]
            laplacian[i] = (left - 2 * center + right) / dx2

        return laplacian

    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        p = self.params

        # Compute terms
        laplacian = self.compute_laplacian(self.mu)
        cubic = self.mu ** 3
        momentum = self.mu - self.mu_prev

        # Input perturbation
        input_term = 0.0
        if input_vec is not None:
            input_term = p.eta * input_vec

        # Update: μ_{t+1} = μ_t + g∇²μ_t - λμ_t³ + ρ(μt - μ{t-1}) + η·x_t
        mu_new = (self.mu +
                  p.dt * p.g * laplacian -
                  p.dt * p.lam * cubic +
                  p.dt * p.rho * momentum +
                  p.dt * input_term)

        # Update state
        self.mu_prev = self.mu.copy()
        self.mu = mu_new
        self.t += 1

        return self.mu


class VectorizedEngine(RecursiveEngine):
    """Vectorized NumPy implementation - still O(n) Laplacian via rolls"""

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """Vectorized Laplacian using np.roll"""
        dx2 = self.params.dx ** 2
        laplacian = (np.roll(mu, 1) - 2 * mu + np.roll(mu, -1)) / dx2
        return laplacian

    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        p = self.params

        # All operations vectorized
        laplacian = self.compute_laplacian(self.mu)

        # Input perturbation
        input_term = 0.0 if input_vec is None else p.eta * input_vec

        # Single vectorized update
        mu_new = (self.mu +
                  p.dt * (p.g * laplacian -
                          p.lam * self.mu**3 +
                          p.rho * (self.mu - self.mu_prev)) +
                  p.dt * input_term)

        self.mu_prev = self.mu
        self.mu = mu_new
        self.t += 1

        return self.mu


class FFTEngine(RecursiveEngine):
    """FFT-based Laplacian - O(n log n) spectral method"""

    def __init__(self, params: RecursiveParams, n_dims: int = 256):
        super().__init__(params, n_dims)

        # Precompute wavenumbers for spectral Laplacian
        # k = [0, 1, 2, ..., n/2-1, -n/2, ..., -1] * 2π/L
        k = np.fft.fftfreq(n_dims, d=params.dx) * 2 * np.pi
        self.k_squared = -(k ** 2)  # Laplacian in Fourier space is -k²

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """Spectral Laplacian via FFT: ∇²μ = ℱ⁻¹[-k² ℱ[μ]]"""
        mu_hat = np.fft.fft(mu)
        laplacian_hat = self.k_squared * mu_hat
        laplacian = np.fft.ifft(laplacian_hat).real
        return laplacian

    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        p = self.params

        # FFT-based Laplacian (most efficient for periodic BC)
        laplacian = self.compute_laplacian(self.mu)

        input_term = 0.0 if input_vec is None else p.eta * input_vec

        # Update
        mu_new = (self.mu +
                  p.dt * (p.g * laplacian -
                          p.lam * self.mu**3 +
                          p.rho * (self.mu - self.mu_prev)) +
                  p.dt * input_term)

        self.mu_prev = self.mu
        self.mu = mu_new
        self.t += 1

        return self.mu


if TORCH_AVAILABLE:
    class GPUEngine(RecursiveEngine):
        """GPU-accelerated implementation using PyTorch"""

        def __init__(self, params: RecursiveParams, n_dims: int = 256,
                     device: str = 'cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu'):
            self.device = device
            super().__init__(params, n_dims)

            # Precompute wavenumbers for GPU
            k = np.fft.fftfreq(n_dims, d=params.dx) * 2 * np.pi
            k_squared = -(k ** 2)
            self.k_squared = torch.tensor(k_squared, dtype=torch.float32, device=device)

        def reset(self):
            """Initialize state on GPU"""
            self.mu = torch.zeros(self.n_dims, dtype=torch.float32, device=self.device)
            self.mu_prev = torch.zeros(self.n_dims, dtype=torch.float32, device=self.device)
            self.t = 0

        def compute_laplacian(self, mu: torch.Tensor) -> torch.Tensor:
            """FFT-based Laplacian on GPU"""
            mu_hat = torch.fft.fft(mu)
            laplacian_hat = self.k_squared * mu_hat
            laplacian = torch.fft.ifft(laplacian_hat).real
            return laplacian

        def step(self, input_vec: Optional[torch.Tensor] = None) -> torch.Tensor:
            p = self.params

            laplacian = self.compute_laplacian(self.mu)

            input_term = 0.0
            if input_vec is not None:
                if isinstance(input_vec, np.ndarray):
                    input_term = p.eta * torch.tensor(input_vec, dtype=torch.float32, device=self.device)
                else:
                    input_term = p.eta * input_vec

            # All operations on GPU
            mu_new = (self.mu +
                      p.dt * (p.g * laplacian -
                              p.lam * self.mu**3 +
                              p.rho * (self.mu - self.mu_prev)) +
                      p.dt * input_term)

            self.mu_prev = self.mu.clone()
            self.mu = mu_new
            self.t += 1

            return self.mu

        def compute_recursive_entropy(self, mu: torch.Tensor) -> float:
            """GPU-accelerated entropy computation"""
            eps = 1e-8
            mu_sq = mu * mu
            entropy = -(mu_sq * torch.log(mu_sq + eps)).sum()
            return entropy.item()

        def to_numpy(self) -> np.ndarray:
            """Convert current state to numpy for compatibility"""
            return self.mu.cpu().numpy()


def create_engine(optimization: Literal['naive', 'vectorized', 'fft', 'gpu'] = 'fft',
                  params: Optional[RecursiveParams] = None,
                  n_dims: int = 256) -> RecursiveEngine:
    """Factory function to create the appropriate engine"""

    if params is None:
        params = RecursiveParams()

    if optimization == 'naive':
        return NaiveEngine(params, n_dims)
    elif optimization == 'vectorized':
        return VectorizedEngine(params, n_dims)
    elif optimization == 'fft':
        return FFTEngine(params, n_dims)
    elif optimization == 'gpu':
        if not TORCH_AVAILABLE:
            print("Warning: PyTorch not available, falling back to FFT")
            return FFTEngine(params, n_dims)
        return GPUEngine(params, n_dims)
    else:
        raise ValueError(f"Unknown optimization level: {optimization}")


# Benchmark utility
def benchmark_engine(engine: RecursiveEngine, n_steps: int = 1000) -> Tuple[float, float]:
    """Benchmark an engine for n_steps"""
    engine.reset()

    # Warm-up
    for _ in range(10):
        engine.step()

    # Benchmark
    start = time.perf_counter()
    for _ in range(n_steps):
        engine.step()
    elapsed = time.perf_counter() - start

    steps_per_sec = n_steps / elapsed

    return elapsed, steps_per_sec


if __name__ == "__main__":
    print("=== Recursive Engine Benchmark ===\n")

    params = RecursiveParams()
    n_dims = 512
    n_steps = 1000

    engines = {
        'Naive': create_engine('naive', params, n_dims),
        'Vectorized': create_engine('vectorized', params, n_dims),
        'FFT': create_engine('fft', params, n_dims),
    }

    if TORCH_AVAILABLE:
        engines['GPU'] = create_engine('gpu', params, n_dims)

    print(f"Dimensions: {n_dims}")
    print(f"Steps: {n_steps}\n")

    results = {}
    for name, engine in engines.items():
        elapsed, steps_per_sec = benchmark_engine(engine, n_steps)
        results[name] = steps_per_sec
        print(f"{name:12s}: {elapsed:.3f}s ({steps_per_sec:.1f} steps/sec)")

    # Speedup comparison
    if 'Naive' in results:
        print("\nSpeedup vs Naive:")
        baseline = results['Naive']
        for name, sps in results.items():
            if name != 'Naive':
                speedup = sps / baseline
                print(f"{name:12s}: {speedup:.1f}x faster")
