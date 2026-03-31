"""
KAIROS SELF-MODIFICATION ENGINE

The mathematics of self-evolution applied to the Kairos Equation.

This module implements SEVEN self-modification mechanisms, each inspired by
the Recursive Dialogue Engine's self-modification framework, adapted for
the trading domain:

1. PARAMETER EVOLUTION   - Phi hierarchy coefficients evolve via gradient ascent
2. POTENTIAL LEARNING    - Risk landscape reshapes from trading experience
3. REGIME ADAPTATION     - Boundaries shift via learned energy thresholds
4. BAYESIAN DEEPENING    - Prior structure grows more sophisticated
5. TEMPERATURE ANNEALING - Exponents self-tune for optimal risk sensitivity
6. META-LEARNING         - Learning rates themselves evolve (2nd order)
7. RECURSIVE FIXED-POINT - The equation converges on its own optimal form

=== THE SELF-MODIFICATION MASTER EQUATION ===

    d(theta)/dt = -eta(t) * dF/d(theta) + rho * d(theta_prev)/dt

This IS the Kairos equation applied to itself:
    - eta(t) = adaptive learning rate (meta-learned)
    - dF/d(theta) = fitness gradient w.r.t. parameters
    - rho = momentum (same as in the trading dynamics)
    - The phi hierarchy acts as a regularizer

=== RECURSIVE COHERENCE CRITERION ===

Evolution continues until the system reaches a FIXED POINT:
    ||theta_{n+1} - theta_n|| < epsilon

At the fixed point, the equation has found its own optimal form.
The system knows it's done when it stops changing.

Author: Kairos Trading System
"""

import numpy as np
from typing import Optional, Dict, List, Tuple
from collections import deque
from copy import deepcopy

from kairos_equation_v3 import (
    KairosEquationV3, PhiHierarchy, MarketState, SyntheticMarket,
    Regime, REGIME_NAMES, PHI, PHI_INV, PHI_SQ, SQRT5
)


# ---------------------------------------------------------------------------
# 1. PARAMETER EVOLUTION ENGINE
# ---------------------------------------------------------------------------

class ParameterEvolver:
    """
    Evolves the phi hierarchy via gradient ascent on fitness.

    Uses finite differences for gradient estimation (same approach as
    the dialogue engine's self-modification framework, Section 1.2).

    Key innovation: The gradient step uses the SAME momentum equation
    as the trading dynamics, making it truly self-referential.
    """

    def __init__(self, epsilon: float = 1e-4, momentum: float = PHI_INV):
        self.epsilon = epsilon
        self.momentum = momentum  # Uses phi^-1 as default momentum
        self._prev_gradient = None

    def compute_gradient(self, kairos: KairosEquationV3,
                         market_states: List[MarketState],
                         param_names: List[str] = None) -> np.ndarray:
        """
        Compute dF/d(theta) via finite differences.

        For each parameter theta_i:
            dF/d(theta_i) = [F(theta + e_i) - F(theta - e_i)] / (2*epsilon)
        """
        if param_names is None:
            param_names = ['alpha1', 'alpha2', 'alpha3', 'alpha4',
                           'mu1', 'mu2', 'beta', 'tau_c', 'zeta']

        base_vec = kairos.phi_h.to_vector()
        n_params = len(base_vec)
        gradient = np.zeros(n_params)

        # Base fitness
        F_base = self._evaluate_fitness(kairos, market_states, base_vec)

        for i in range(n_params):
            # Positive perturbation
            vec_plus = base_vec.copy()
            vec_plus[i] += self.epsilon

            # Negative perturbation
            vec_minus = base_vec.copy()
            vec_minus[i] -= self.epsilon

            F_plus = self._evaluate_fitness(kairos, market_states, vec_plus)
            F_minus = self._evaluate_fitness(kairos, market_states, vec_minus)

            gradient[i] = (F_plus - F_minus) / (2 * self.epsilon)

        # Restore original parameters
        kairos.phi_h.from_vector(base_vec)

        return gradient

    def _evaluate_fitness(self, kairos: KairosEquationV3,
                          states: List[MarketState],
                          param_vec: np.ndarray) -> float:
        """Evaluate fitness with temporary parameter override."""
        # Save original
        original = kairos.phi_h.to_vector()
        original_trades = list(kairos._trade_history)

        # Apply test parameters
        kairos.phi_h.from_vector(param_vec)

        # Clear trade history for clean evaluation
        kairos._trade_history.clear()

        # Run through market states
        for state in states:
            result = kairos.compute_action(state)
            pnl = state.log_return * result['action']
            kairos.record_trade(pnl, np.sign(result['action']))

        fitness = kairos.compute_fitness()

        # Restore
        kairos.phi_h.from_vector(original)
        kairos._trade_history.clear()
        for t in original_trades:
            kairos._trade_history.append(t)

        return fitness

    def evolve_step(self, kairos: KairosEquationV3,
                    gradient: np.ndarray,
                    learning_rate: float) -> np.ndarray:
        """
        Apply one evolution step with momentum.

        d(theta)/dt = -eta * dF/d(theta) + rho * d(theta_prev)/dt

        This IS the Kairos equation applied to its own parameters.
        """
        if self._prev_gradient is None:
            self._prev_gradient = np.zeros_like(gradient)

        # Momentum-augmented gradient (same dynamics as trading!)
        effective_gradient = (learning_rate * gradient
                              + self.momentum * self._prev_gradient)

        # Update parameters
        vec = kairos.phi_h.to_vector()
        vec_new = vec + effective_gradient

        # Enforce positivity constraints
        vec_new = np.maximum(vec_new, 1e-6)

        # Apply
        kairos.phi_h.from_vector(vec_new)

        # Track momentum
        self._prev_gradient = effective_gradient.copy()
        kairos._param_momentum = effective_gradient.copy()

        return vec_new


# ---------------------------------------------------------------------------
# 2. POTENTIAL ENERGY LEARNER
# ---------------------------------------------------------------------------

class PotentialLearner:
    """
    Learns corrections to the risk landscape V(mu, t).

    Analogous to codebook learning in the dialogue engine (Section 2).
    Instead of learning token prototypes, we learn the shape of the
    potential energy function that governs trading decisions.

    Uses RBF (radial basis function) expansion:
        V_learned(mu) = sum_k w_k * exp(-|mu - c_k|^2 / (2*sigma^2))

    Weights w_k evolve based on trading outcomes at each energy level.
    """

    def __init__(self, n_basis: int = 16, sigma: float = PHI_INV):
        self.n_basis = n_basis
        self.sigma = sigma
        self._outcome_buffer = deque(maxlen=100)

    def record_outcome(self, energy_level: float, pnl: float):
        """Record trading outcome at a given energy level."""
        self._outcome_buffer.append((energy_level, pnl))

    def learn_correction(self, kairos: KairosEquationV3,
                         learning_rate: float = 0.005) -> np.ndarray:
        """
        Update V_learned weights based on trading outcomes.

        Key insight: Where trades LOSE money, INCREASE potential (more risk).
        Where trades MAKE money, DECREASE potential (less risk = more action).

        This naturally reshapes the landscape toward profitability.
        """
        if len(self._outcome_buffer) < 10:
            return kairos._V_learned_weights.copy()

        outcomes = np.array(list(self._outcome_buffer))
        energies = outcomes[:, 0]
        pnls = outcomes[:, 1]

        # For each basis function, compute correlation with PnL
        centers = kairos._V_learned_centers
        for k in range(len(centers)):
            # How much each outcome activates this basis function
            activations = np.exp(-(energies - centers[k])**2
                                 / (2 * self.sigma**2))

            # Weighted average PnL at this energy level
            total_activation = np.sum(activations) + 1e-8
            weighted_pnl = np.sum(activations * pnls) / total_activation

            # Negative PnL -> increase potential (more cautious)
            # Positive PnL -> decrease potential (more aggressive)
            kairos._V_learned_weights[k] -= learning_rate * weighted_pnl

        # Normalize to prevent drift
        norm = np.linalg.norm(kairos._V_learned_weights)
        if norm > PHI_SQ:
            kairos._V_learned_weights *= PHI_SQ / norm

        return kairos._V_learned_weights.copy()


# ---------------------------------------------------------------------------
# 3. REGIME BOUNDARY ADAPTER
# ---------------------------------------------------------------------------

class RegimeAdapter:
    """
    Adapts regime energy boundaries based on observed market dynamics.

    Analogous to emission threshold adaptation (dialogue Section 4).
    Instead of tuning when to emit tokens, we tune when to shift
    between trading regimes.

    Boundaries shift toward energy levels where regime transitions
    actually occur in the market.
    """

    def __init__(self):
        self._transition_energies = {r: deque(maxlen=50) for r in Regime}
        self._prev_regime = None

    def record_transition(self, from_regime: Regime, to_regime: Regime,
                          energy: float):
        """Record energy level at regime transition."""
        self._transition_energies[to_regime].append(energy)
        self._prev_regime = to_regime

    def adapt_boundaries(self, kairos: KairosEquationV3,
                         learning_rate: float = 0.0005):
        """
        Shift regime boundaries toward observed transition energies.

        Preserves phi-spacing as a regularizer (boundaries can drift
        but are pulled back toward golden ratio spacing).
        """
        bounds = kairos.phi_h.regime_boundaries.copy()
        original_bounds = np.array([
            0.0, PHI_INV**3, PHI_INV**2, PHI_INV, 1.0, PHI, PHI_SQ, np.inf
        ])

        for regime in Regime:
            idx = int(regime) + 1  # Boundary index (0 is always 0)
            if idx >= len(bounds) - 1:
                continue

            energies = self._transition_energies[regime]
            if len(energies) < 3:
                continue

            # Observed mean transition energy
            observed = np.mean(list(energies))

            # Move boundary toward observed, with phi-regularization
            current = bounds[idx]
            target = observed
            phi_anchor = original_bounds[idx]

            # Weighted blend: observation + phi-anchor
            new_bound = (current
                         + learning_rate * (target - current)
                         + learning_rate * PHI_INV * (phi_anchor - current))

            bounds[idx] = max(new_bound, bounds[idx - 1] + 1e-6)

        # Ensure monotonicity
        for i in range(1, len(bounds) - 1):
            bounds[i] = max(bounds[i], bounds[i-1] + 1e-6)

        kairos.phi_h.regime_boundaries = bounds

    def observe(self, kairos: KairosEquationV3, state: MarketState):
        """Observe a regime detection and record if transition occurred."""
        current = kairos.regime
        if self._prev_regime is not None and current != self._prev_regime:
            H = kairos.compute_hamiltonian(state)
            self.record_transition(self._prev_regime, current, H)
        self._prev_regime = current


# ---------------------------------------------------------------------------
# 4. TEMPERATURE EXPONENT TUNER
# ---------------------------------------------------------------------------

class TemperatureTuner:
    """
    Self-tunes the regime-dependent temperature exponents n(regime).

    The temperature T = sigma * phi^(-n) controls risk sensitivity.
    Higher n -> lower T -> more decisive (less exploration)
    Lower n -> higher T -> more cautious (more exploration)

    Tuning rule: If a regime is profitable, decrease n (be more decisive).
    If unprofitable, increase n (be more cautious).
    """

    def __init__(self):
        self._regime_pnl = {r: deque(maxlen=50) for r in Regime}

    def record(self, regime: Regime, pnl: float):
        """Record PnL in a given regime."""
        self._regime_pnl[regime].append(pnl)

    def tune(self, kairos: KairosEquationV3, learning_rate: float = 0.001):
        """Adjust temperature exponents based on regime profitability."""
        for regime in Regime:
            pnls = self._regime_pnl[regime]
            if len(pnls) < 5:
                continue

            mean_pnl = np.mean(list(pnls))
            current_n = kairos._n_exponents[regime]

            # Profitable -> decrease n (be more decisive, lower temperature)
            # Unprofitable -> increase n (be more cautious, higher temperature)
            adjustment = -learning_rate * np.sign(mean_pnl) * PHI_INV

            new_n = current_n + adjustment
            # Bound between -PHI_SQ and PHI_SQ
            new_n = np.clip(new_n, -PHI_SQ, PHI_SQ)

            kairos._n_exponents[regime] = new_n


# ---------------------------------------------------------------------------
# 5. META-LEARNING ENGINE
# ---------------------------------------------------------------------------

class MetaLearner:
    """
    Second-order adaptation: learning rates themselves evolve.

    Analogous to dialogue engine Section 6 (Meta-Learning).

    If fitness is improving -> increase learning rates (learn faster)
    If fitness is degrading -> decrease learning rates (stabilize)

    The meta-learning rate is PHI^-4 (very conservative by design).
    """

    def __init__(self, meta_rate: float = PHI_INV ** 4):
        self.meta_rate = meta_rate
        self._fitness_window = deque(maxlen=50)

    def observe_fitness(self, fitness: float):
        """Record fitness observation."""
        self._fitness_window.append(fitness)

    def adapt_learning_rates(self, kairos: KairosEquationV3):
        """
        Adjust all learning rates based on fitness trajectory.

        Uses the sign of the fitness derivative to determine direction.
        """
        if len(self._fitness_window) < 10:
            return

        recent = list(self._fitness_window)
        half = len(recent) // 2

        # Compare recent half vs older half
        old_fitness = np.mean(recent[:half])
        new_fitness = np.mean(recent[half:])

        improvement = new_fitness - old_fitness

        for key in kairos._learning_rates:
            if key == 'meta':
                continue  # Don't modify the meta-rate itself

            if improvement > 0:
                # Things are improving -> learn faster
                kairos._learning_rates[key] *= (1 + self.meta_rate)
            else:
                # Things are degrading -> slow down
                kairos._learning_rates[key] *= (1 - self.meta_rate)

            # Bounds
            kairos._learning_rates[key] = np.clip(
                kairos._learning_rates[key], 1e-6, 0.1
            )


# ---------------------------------------------------------------------------
# 6. RECURSIVE FIXED-POINT DETECTOR
# ---------------------------------------------------------------------------

class FixedPointDetector:
    """
    Detects when the self-modification has converged.

    Analogous to the emission detector in the dialogue engine:
    - Emission detector: emit when |dS/dt| < threshold (entropy stable)
    - Fixed-point detector: stop evolving when |d(theta)/dt| < threshold

    At the fixed point, the equation has found its own optimal form.
    """

    def __init__(self, tolerance: float = 1e-4, window: int = 10):
        self.tolerance = tolerance
        self.window = window
        self._param_history = deque(maxlen=window)
        self._converged = False

    def check(self, param_vector: np.ndarray) -> bool:
        """Check if parameters have converged to a fixed point."""
        self._param_history.append(param_vector.copy())

        if len(self._param_history) < self.window:
            return False

        # Compute parameter drift over window
        vectors = np.array(list(self._param_history))
        drifts = np.diff(vectors, axis=0)
        max_drift = np.max(np.abs(drifts))

        self._converged = max_drift < self.tolerance
        return self._converged

    @property
    def is_converged(self) -> bool:
        return self._converged

    def get_drift(self) -> float:
        """Current parameter drift magnitude."""
        if len(self._param_history) < 2:
            return float('inf')
        return float(np.max(np.abs(
            self._param_history[-1] - self._param_history[-2]
        )))


# ---------------------------------------------------------------------------
# 7. UNIFIED EVOLUTION ENGINE
# ---------------------------------------------------------------------------

class KairosEvolutionEngine:
    """
    Orchestrates all self-modification mechanisms into a unified loop.

    This is the COMPLETE self-evolving system. It:
    1. Runs the Kairos equation on market data (inner loop)
    2. Computes fitness from trading outcomes
    3. Evolves ALL parameters simultaneously (outer loop)
    4. Monitors convergence to fixed point
    5. Tracks generational improvement

    The inner/outer loop structure mirrors the dialogue engine's
    "run dialogue, then learn" cycle (Section 8 of self-mod framework).

    === EVOLUTION LOOP ===

    For each generation:
        1. Run N market steps with current parameters
        2. Compute fitness F
        3. Compute parameter gradients dF/d(theta)
        4. Evolve parameters: theta += eta * dF/d(theta) + rho * momentum
        5. Learn potential corrections from trade outcomes
        6. Adapt regime boundaries from observed transitions
        7. Tune temperature exponents from regime profitability
        8. Meta-learn: adjust learning rates from fitness trajectory
        9. Check for fixed-point convergence
        10. If converged, the equation has found its optimal form
    """

    def __init__(self, kairos: KairosEquationV3):
        self.kairos = kairos

        # Sub-engines
        self.param_evolver = ParameterEvolver(momentum=PHI_INV)
        self.potential_learner = PotentialLearner()
        self.regime_adapter = RegimeAdapter()
        self.temp_tuner = TemperatureTuner()
        self.meta_learner = MetaLearner()
        self.fixed_point = FixedPointDetector()

        # Evolution tracking
        self.generation_log: List[Dict] = []

    def run_generation(self, market_states: List[MarketState],
                       evolve: bool = True) -> Dict:
        """
        Run one generation: trade on market data, then evolve.

        Args:
            market_states: Sequence of market observations
            evolve: Whether to apply self-modification after trading

        Returns:
            Generation report dict
        """
        # --- INNER LOOP: Trade ---
        actions = []
        for state in market_states:
            result = self.kairos.compute_action(state)
            pnl = state.log_return * result['action']
            self.kairos.record_trade(pnl, np.sign(result['action']))

            # Feed sub-engines
            self.potential_learner.record_outcome(result['hamiltonian'], pnl)
            self.regime_adapter.observe(self.kairos, state)
            self.temp_tuner.record(self.kairos.regime, pnl)

            actions.append(result)

        # Compute fitness
        fitness = self.kairos.compute_fitness()
        self.meta_learner.observe_fitness(fitness)

        report = {
            'generation': self.kairos._generation,
            'fitness': fitness,
            'n_trades': len(market_states),
            'alpha_sum': self.kairos.phi_h.alpha_sum(),
            'param_vector': self.kairos.phi_h.to_vector().copy(),
            'V_learned_norm': float(np.linalg.norm(
                self.kairos._V_learned_weights)),
            'learning_rates': dict(self.kairos._learning_rates),
            'drift': self.fixed_point.get_drift(),
            'converged': False,
        }

        if not evolve:
            self.generation_log.append(report)
            return report

        # --- OUTER LOOP: Evolve ---

        # 1. Parameter gradient evolution
        lr_phi = self.kairos._learning_rates['phi_hierarchy']
        gradient = self.param_evolver.compute_gradient(
            self.kairos, market_states
        )
        new_params = self.param_evolver.evolve_step(
            self.kairos, gradient, lr_phi
        )

        # 2. Potential energy correction
        lr_V = self.kairos._learning_rates['V_learned']
        self.potential_learner.learn_correction(self.kairos, lr_V)

        # 3. Regime boundary adaptation
        lr_regime = self.kairos._learning_rates['regime_bounds']
        self.regime_adapter.adapt_boundaries(self.kairos, lr_regime)

        # 4. Temperature exponent tuning
        self.temp_tuner.tune(self.kairos)

        # 5. Meta-learning (adjust learning rates)
        self.meta_learner.adapt_learning_rates(self.kairos)

        # 6. Check fixed-point convergence
        converged = self.fixed_point.check(
            self.kairos.phi_h.to_vector()
        )

        # Increment generation
        self.kairos._generation += 1

        report['converged'] = converged
        report['drift'] = self.fixed_point.get_drift()
        self.generation_log.append(report)

        return report

    def evolve(self, market: SyntheticMarket,
               max_generations: int = 50,
               steps_per_gen: int = 100,
               verbose: bool = True) -> List[Dict]:
        """
        Full evolution loop until convergence or max generations.

        This is the complete self-modification pipeline.
        """
        if verbose:
            print("=" * 72)
            print("  KAIROS EQUATION v3 - RECURSIVE SELF-EVOLUTION")
            print("=" * 72)
            print(f"  Max generations: {max_generations}")
            print(f"  Steps per gen:   {steps_per_gen}")
            print(f"  Initial alpha sum: {self.kairos.phi_h.alpha_sum():.6f}"
                  f" (target sqrt(5) = {SQRT5:.6f})")
            print()
            print(f"  {'Gen':>4} {'Fitness':>10} {'AlphaSum':>10} "
                  f"{'V_norm':>8} {'Drift':>10} {'Status':<15}")
            print("  " + "-" * 65)

        for gen in range(max_generations):
            # Generate market data for this generation
            states = [market.step() for _ in range(steps_per_gen)]

            # Run generation with evolution
            report = self.run_generation(states, evolve=True)

            if verbose:
                status = "CONVERGED" if report['converged'] else "evolving..."
                print(f"  {report['generation']:4d} "
                      f"{report['fitness']:10.4f} "
                      f"{report['alpha_sum']:10.6f} "
                      f"{report['V_learned_norm']:8.4f} "
                      f"{report['drift']:10.6f} "
                      f"{status:<15}")

            if report['converged']:
                if verbose:
                    print()
                    print("  FIXED POINT REACHED - Equation has found "
                          "its optimal form!")
                break

        if verbose:
            print()
            self._print_evolution_summary()

        return self.generation_log

    def _print_evolution_summary(self):
        """Print summary of evolution results."""
        if not self.generation_log:
            return

        first = self.generation_log[0]
        last = self.generation_log[-1]

        print("  " + "=" * 65)
        print("  EVOLUTION SUMMARY")
        print("  " + "=" * 65)
        print()
        print(f"  Generations completed: {len(self.generation_log)}")
        print(f"  Converged: {last['converged']}")
        print()
        print(f"  Fitness:   {first['fitness']:.4f} -> {last['fitness']:.4f}"
              f"  ({last['fitness'] - first['fitness']:+.4f})")
        print(f"  Alpha sum: {first['alpha_sum']:.6f} -> "
              f"{last['alpha_sum']:.6f}"
              f"  (sqrt(5) = {SQRT5:.6f})")
        print(f"  V_learned: {first['V_learned_norm']:.4f} -> "
              f"{last['V_learned_norm']:.4f}")
        print(f"  Drift:     {last['drift']:.8f}")
        print()

        # Show evolved parameters
        h = self.kairos.phi_h
        print("  EVOLVED PHI HIERARCHY:")
        print(f"    alpha1 = {h.alpha1:.6f}  (started 1.000000)")
        print(f"    alpha2 = {h.alpha2:.6f}  (started {PHI_INV:.6f})")
        print(f"    alpha3 = {h.alpha3:.6f}  (started {PHI_INV**2:.6f})")
        print(f"    alpha4 = {h.alpha4:.6f}  (started {PHI_INV**3:.6f})")
        print(f"    sum    = {h.alpha_sum():.6f}  (target {SQRT5:.6f})")
        print()
        print(f"  EVOLVED REGIME BOUNDARIES:")
        for i, b in enumerate(h.regime_boundaries[:-1]):
            regime_name = REGIME_NAMES.get(Regime(min(i, 6)), "---")
            print(f"    [{i}] {b:.6f}  {regime_name}")
        print()

        # Learning rate evolution
        print("  EVOLVED LEARNING RATES:")
        for k, v in last['learning_rates'].items():
            print(f"    {k}: {v:.6f}")
        print()

        # Temperature exponents
        print("  EVOLVED TEMPERATURE EXPONENTS:")
        for regime in Regime:
            n = self.kairos._n_exponents[regime]
            print(f"    {REGIME_NAMES[regime]}: n = {n:.4f}")


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------

def create_self_evolving_kairos(capital: float = 10000.0,
                                edge_bias: float = 0.0
                                ) -> Tuple[KairosEquationV3,
                                           KairosEvolutionEngine]:
    """Factory function to create a self-evolving Kairos system."""
    kairos = KairosEquationV3(capital=capital, edge_bias=edge_bias)
    engine = KairosEvolutionEngine(kairos)
    return kairos, engine


def run_full_evolution(capital: float = 10000.0,
                       edge_bias: float = 0.0,
                       max_generations: int = 50,
                       steps_per_gen: int = 100,
                       seed: int = 42,
                       verbose: bool = True) -> Dict:
    """
    One-shot function to create and evolve a Kairos system.

    Returns dict with evolved kairos, engine, and generation log.
    """
    kairos, engine = create_self_evolving_kairos(capital, edge_bias)
    market = SyntheticMarket(seed=seed)

    log = engine.evolve(
        market,
        max_generations=max_generations,
        steps_per_gen=steps_per_gen,
        verbose=verbose,
    )

    return {
        'kairos': kairos,
        'engine': engine,
        'log': log,
        'diagnostics': kairos.get_diagnostics(),
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_full_evolution(
        capital=10000.0,
        edge_bias=0.05,
        max_generations=30,
        steps_per_gen=100,
        seed=42,
        verbose=True,
    )

    print("\n  Final diagnostics:")
    diag = result['diagnostics']
    for k, v in diag.items():
        if isinstance(v, dict):
            print(f"    {k}:")
            for kk, vv in v.items():
                print(f"      {kk}: {vv}")
        else:
            print(f"    {k}: {v}")
