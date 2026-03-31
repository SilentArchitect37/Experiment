"""
THE KAIROS EQUATION v3 - Self-Evolving Unified Trading Algorithm

Evolution: v2 (static phi-derived) -> v3 (recursive self-modification)

The core insight: apply the equation TO ITSELF. The Hamiltonian that governs
trading decisions also governs its own parameter evolution. The system doesn't
just trade - it recursively improves its own mathematics.

=== THE MASTER EQUATION (v3 - Self-Referential) ===

    A*(t) = C * exp[-H(t) / T(t)] * P(win|E) / P(loss|E)

Where T(t) is now ADAPTIVE temperature:
    T(t) = sigma * phi^(-n(t))  where n(t) evolves

=== THE SELF-MODIFYING HAMILTONIAN ===

    H = (1/2)|grad(log S)|^2 + V(mu, t) + V_learned(mu, t)

V_learned is a potential energy correction that the system learns from its
own trading history, creating a feedback loop:

    dV_learned/dt = -alpha * dF/dV  (gradient descent on fitness)

=== RECURSIVE PARAMETER EVOLUTION ===

    d(theta)/dt = -eta * dH/d(theta) + rho * d(theta_prev)/dt

Parameters evolve under the SAME dynamical equation as the trading state,
creating true self-reference. The phi-hierarchy itself is subject to
recursive refinement.

=== FREE PARAMETERS: Still 2 (capital, edge_bias) ===
=== EVOLVED PARAMETERS: Everything else, recursively ===

Author: Kairos Trading System
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Callable
from collections import deque
from enum import IntEnum
import warnings


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1 + np.sqrt(5)) / 2          # Golden ratio 1.618033...
PHI_INV = PHI - 1                    # 1/phi = 0.618033...
PHI_SQ = PHI ** 2                    # phi^2 = 2.618033...
SQRT5 = np.sqrt(5)                   # sqrt(5) = alpha sum


# ---------------------------------------------------------------------------
# Market Regimes (Greek Letters)
# ---------------------------------------------------------------------------

class Regime(IntEnum):
    """Seven market regimes with phi-spaced energy boundaries."""
    OMEGA = 0   # Quiet / low volatility
    DELTA = 1   # Emerging pattern
    TAU   = 2   # Trend forming
    PSI   = 3   # Sweet spot - ACT
    SIGMA = 4   # Strong trend
    XI    = 5   # Threshold - EXIT
    KAPPA = 6   # Crash / extreme


# Regime names for display
REGIME_NAMES = {
    Regime.OMEGA: "OMEGA (quiet)",
    Regime.DELTA: "DELTA (emerging)",
    Regime.TAU:   "TAU (forming)",
    Regime.PSI:   "PSI (sweet-spot)",
    Regime.SIGMA: "SIGMA (trending)",
    Regime.XI:    "XI (threshold)",
    Regime.KAPPA: "KAPPA (crash)",
}


# ---------------------------------------------------------------------------
# Phi-Derived Parameter Hierarchy
# ---------------------------------------------------------------------------

@dataclass
class PhiHierarchy:
    """
    All coefficients derived from golden ratio.
    In v3, these are INITIAL values that evolve recursively.

    alpha1 + alpha2 + alpha3 + alpha4 = 1 + phi^-1 + phi^-2 + phi^-3
                                       = sqrt(5) (!)
    """
    alpha1: float = 1.0               # Kuramoto coupling
    alpha2: float = PHI_INV           # SOC criticality = phi^-1
    alpha3: float = PHI_INV ** 2      # Network risk = phi^-2
    alpha4: float = PHI_INV ** 3      # Catastrophe = phi^-3

    # Regime energy boundaries (phi-spaced)
    regime_boundaries: np.ndarray = field(default_factory=lambda: np.array([
        0.0,
        PHI_INV ** 3,    # 0.236
        PHI_INV ** 2,    # 0.382
        PHI_INV,         # 0.618  (sweet spot entry)
        1.0,             # 1.000
        PHI,             # 1.618  (exit threshold)
        PHI_SQ,          # 2.618  (crash zone)
        np.inf
    ]))

    # Double-well positions
    mu1: float = PHI_INV              # 0.618
    mu2: float = PHI                  # 1.618

    # SOC criticality parameters
    beta: float = PHI                 # Decay rate
    tau_c: float = PHI_INV            # Critical correlation time

    # Bifurcation threshold
    zeta: float = PHI_INV ** 2        # Double-well strength

    def alpha_sum(self) -> float:
        return self.alpha1 + self.alpha2 + self.alpha3 + self.alpha4

    def to_vector(self) -> np.ndarray:
        """Flatten hierarchy to parameter vector for gradient computation."""
        return np.array([
            self.alpha1, self.alpha2, self.alpha3, self.alpha4,
            self.mu1, self.mu2, self.beta, self.tau_c, self.zeta
        ])

    def from_vector(self, vec: np.ndarray):
        """Restore from parameter vector."""
        self.alpha1, self.alpha2, self.alpha3, self.alpha4 = vec[0:4]
        self.mu1, self.mu2 = vec[4], vec[5]
        self.beta, self.tau_c, self.zeta = vec[6], vec[7], vec[8]


# ---------------------------------------------------------------------------
# Market State
# ---------------------------------------------------------------------------

@dataclass
class MarketState:
    """Observable market state at time t."""
    price: float = 0.0                # Current price S(t)
    log_return: float = 0.0           # log(S/S_prev)
    volatility: float = 0.01          # sigma (realized vol)
    sync_ratio: float = 0.0           # r - Kuramoto sync (0..1)
    correlation_time: float = 0.0     # tau - SOC correlation
    network_risk: float = 0.0         # rho - systemic risk
    delta_val: float = 0.0            # Delta for catastrophe
    volume: float = 0.0               # Normalized volume
    momentum: float = 0.0             # Price momentum


# ---------------------------------------------------------------------------
# THE KAIROS EQUATION v3 - Core
# ---------------------------------------------------------------------------

class KairosEquationV3:
    """
    Self-Evolving Kairos Equation.

    The equation applies its own dynamics to evolve its parameters.
    True self-reference: H governs both trading AND its own evolution.

    Free parameters: 2 (capital, edge_bias)
    Everything else derives from phi and then EVOLVES.
    """

    def __init__(self, capital: float = 10000.0, edge_bias: float = 0.0):
        # === FREE PARAMETERS (only 2) ===
        self.capital = capital
        self.edge_bias = edge_bias

        # === PHI-DERIVED (initial, will evolve) ===
        self.phi_h = PhiHierarchy()

        # === ADAPTIVE STATE ===
        self.regime = Regime.OMEGA
        self.regime_history = deque(maxlen=500)
        self.t = 0

        # Temperature exponent (regime-dependent, evolves)
        self._n_exponents = {
            Regime.OMEGA: 0.0,
            Regime.DELTA: 1.0,
            Regime.TAU:   PHI_INV,
            Regime.PSI:   PHI_INV ** 2,
            Regime.SIGMA: -PHI_INV,
            Regime.XI:    -1.0,
            Regime.KAPPA: -PHI,
        }

        # === BAYESIAN STATE ===
        self.prior_win = 0.5
        self.prior_loss = 0.5
        self.evidence_history = deque(maxlen=200)

        # === SELF-MODIFICATION STATE ===
        # Learned potential correction (starts at zero)
        self._V_learned_weights = np.zeros(16)  # Basis function weights
        self._V_learned_centers = np.linspace(0, PHI_SQ, 16)

        # Parameter evolution momentum (for recursive dynamics)
        self._param_momentum = np.zeros(9)

        # Performance tracking for fitness
        self._trade_history = deque(maxlen=500)
        self._fitness_history = deque(maxlen=200)
        self._hamiltonian_history = deque(maxlen=200)

        # Meta-learning rates (also evolve!)
        self._learning_rates = {
            'phi_hierarchy': 0.001,
            'V_learned': 0.005,
            'bayesian': 0.01,
            'regime_bounds': 0.0005,
            'meta': 0.0001,     # Learning rate of learning rates
        }

        # Snapshot for self-comparison
        self._generation = 0
        self._generation_fitness = []

    # -------------------------------------------------------------------
    # POTENTIAL ENERGY (Risk Landscape)
    # -------------------------------------------------------------------

    def _V_kuramoto(self, state: MarketState) -> float:
        """Kuramoto synchronization sweet-spot potential.
        V1 = alpha1 * (r - phi^-1)^2
        Minimum at r = 0.618 (golden ratio sweet spot).
        """
        return self.phi_h.alpha1 * (state.sync_ratio - PHI_INV) ** 2

    def _V_soc(self, state: MarketState) -> float:
        """Self-organized criticality potential.
        V2 = alpha2 * exp(-beta * |tau - tau_c|)
        Peaks when correlation time hits critical threshold.
        """
        return self.phi_h.alpha2 * np.exp(
            -self.phi_h.beta * abs(state.correlation_time - self.phi_h.tau_c)
        )

    def _V_network(self, state: MarketState) -> float:
        """Network systemic risk potential.
        V3 = alpha3 * rho
        Linear in systemic risk - simple and direct.
        """
        return self.phi_h.alpha3 * state.network_risk

    def _V_catastrophe(self, state: MarketState) -> float:
        """Catastrophe bifurcation potential.
        V4 = alpha4 * Theta(-Delta)
        Activates only when delta goes negative (crash signal).
        """
        theta = 1.0 if state.delta_val < 0 else 0.0
        return self.phi_h.alpha4 * theta

    def _V_double_well(self, state: MarketState) -> float:
        """Double-well potential at phi-derived positions.
        V5 = zeta * (mu - mu1)^2 * (mu - mu2)^2
        Creates energy barriers between regime states.
        """
        mu = state.sync_ratio * PHI_SQ  # Scale to phi range
        return self.phi_h.zeta * (mu - self.phi_h.mu1)**2 * (mu - self.phi_h.mu2)**2

    def _V_learned(self, state: MarketState) -> float:
        """LEARNED potential correction (v3 innovation).
        Uses radial basis functions centered along the energy axis.
        The system learns to reshape its own risk landscape.
        """
        mu = state.sync_ratio * PHI_SQ
        # RBF expansion
        dists = (mu - self._V_learned_centers) ** 2
        basis = np.exp(-dists / (2 * PHI_INV ** 2))
        return float(np.dot(self._V_learned_weights, basis))

    def compute_potential(self, state: MarketState) -> float:
        """Total potential energy V = sum of all components + learned correction."""
        V = (self._V_kuramoto(state)
             + self._V_soc(state)
             + self._V_network(state)
             + self._V_catastrophe(state)
             + self._V_double_well(state)
             + self._V_learned(state))
        return V

    # -------------------------------------------------------------------
    # HAMILTONIAN
    # -------------------------------------------------------------------

    def compute_kinetic_energy(self, state: MarketState) -> float:
        """Kinetic energy: T = (1/2)|grad(log S)|^2
        The price gradient term - measures how fast price is moving.
        """
        grad_log_S = state.log_return / max(state.volatility, 1e-8)
        return 0.5 * grad_log_S ** 2

    def compute_hamiltonian(self, state: MarketState) -> float:
        """H = T + V (total system energy)."""
        T = self.compute_kinetic_energy(state)
        V = self.compute_potential(state)
        return T + V

    # -------------------------------------------------------------------
    # REGIME DETECTION
    # -------------------------------------------------------------------

    def detect_regime(self, state: MarketState) -> Regime:
        """Classify market regime based on Hamiltonian energy level.
        Energy boundaries are phi-spaced and EVOLVE via self-modification.
        """
        H = self.compute_hamiltonian(state)
        bounds = self.phi_h.regime_boundaries

        for i in range(len(bounds) - 1):
            if bounds[i] <= H < bounds[i + 1]:
                regime = Regime(min(i, Regime.KAPPA))
                break
        else:
            regime = Regime.KAPPA

        self.regime = regime
        self.regime_history.append(regime)
        return regime

    # -------------------------------------------------------------------
    # ADAPTIVE TEMPERATURE
    # -------------------------------------------------------------------

    def compute_temperature(self, state: MarketState) -> float:
        """Adaptive temperature: T(t) = sigma * phi^(-n(t))
        n(t) is regime-dependent and evolves.
        """
        n = self._n_exponents.get(self.regime, 0.0)
        return max(state.volatility * PHI ** (-n), 1e-10)

    # -------------------------------------------------------------------
    # BAYESIAN ODDS
    # -------------------------------------------------------------------

    def update_bayesian_odds(self, outcome: Optional[float] = None) -> float:
        """Update P(win|E)/P(loss|E) from evidence.
        Uses recursive Bayesian update with phi-derived prior decay.

        Returns: odds ratio
        """
        if outcome is not None:
            self.evidence_history.append(outcome)

        if len(self.evidence_history) < 2:
            return 1.0 + self.edge_bias

        recent = np.array(list(self.evidence_history))

        # Exponentially weighted with phi-decay
        n = len(recent)
        weights = np.array([PHI_INV ** (n - 1 - i) for i in range(n)])
        weights /= weights.sum()

        # Weighted win/loss rates
        wins = np.sum(weights * (recent > 0))
        losses = np.sum(weights * (recent <= 0))

        # Bayesian update with Laplace smoothing
        self.prior_win = (wins + PHI_INV) / (1 + 2 * PHI_INV)
        self.prior_loss = (losses + PHI_INV) / (1 + 2 * PHI_INV)

        # Odds ratio
        odds = self.prior_win / max(self.prior_loss, 1e-8)

        # Apply edge bias (free parameter)
        odds *= (1 + self.edge_bias)

        return odds

    # -------------------------------------------------------------------
    # THE MASTER EQUATION
    # -------------------------------------------------------------------

    def compute_action(self, state: MarketState) -> Dict:
        """
        A*(t) = C * exp[-H(t) / T(t)] * P(win|E) / P(loss|E)

        Returns dict with:
            - action: optimal allocation A* (can be negative for short)
            - hamiltonian: H(t)
            - temperature: T(t)
            - regime: current regime
            - potential: V(t)
            - kinetic: kinetic energy
            - odds: Bayesian odds ratio
            - confidence: exp[-H/T] (Boltzmann factor)
        """
        # Detect regime
        regime = self.detect_regime(state)

        # Compute components
        H = self.compute_hamiltonian(state)
        T = self.compute_temperature(state)
        odds = self.update_bayesian_odds()

        # Boltzmann factor (confidence)
        boltzmann = np.exp(-H / T)

        # Master equation
        A_star = self.capital * boltzmann * odds

        # Direction from momentum
        if state.momentum < 0:
            A_star = -A_star

        # Regime-based constraints
        if regime == Regime.KAPPA:
            A_star *= PHI_INV ** 3   # Minimal exposure in crash
        elif regime == Regime.XI:
            A_star *= PHI_INV        # Reduce at threshold
        elif regime == Regime.PSI:
            A_star *= PHI            # Amplify at sweet spot

        # Track
        self._hamiltonian_history.append(H)
        self.t += 1

        return {
            'action': float(np.clip(A_star, -self.capital, self.capital)),
            'hamiltonian': H,
            'temperature': T,
            'regime': regime,
            'regime_name': REGIME_NAMES[regime],
            'potential': self.compute_potential(state),
            'kinetic': self.compute_kinetic_energy(state),
            'odds': odds,
            'confidence': boltzmann,
            'generation': self._generation,
            't': self.t,
        }

    # -------------------------------------------------------------------
    # FITNESS FUNCTION (for self-modification)
    # -------------------------------------------------------------------

    def compute_fitness(self) -> float:
        """
        F = risk_adjusted_return * regime_accuracy * information_ratio

        Multi-objective fitness that drives self-modification.
        """
        if len(self._trade_history) < 5:
            return 0.0

        trades = np.array(list(self._trade_history))
        returns = trades[:, 0]  # PnL
        predictions = trades[:, 1]  # Predicted direction

        # Risk-adjusted return (Sharpe-like)
        mean_ret = np.mean(returns)
        std_ret = np.std(returns) + 1e-8
        sharpe = mean_ret / std_ret

        # Regime accuracy (did we act correctly per regime?)
        correct_dir = np.sum(np.sign(returns) == np.sign(predictions))
        accuracy = correct_dir / len(returns)

        # Information ratio (consistency)
        if len(returns) > 10:
            rolling_mean = np.convolve(returns, np.ones(10)/10, mode='valid')
            info_ratio = np.mean(rolling_mean) / (np.std(rolling_mean) + 1e-8)
        else:
            info_ratio = sharpe

        # Combined fitness with phi-weighting
        fitness = (sharpe * 1.0
                   + accuracy * PHI_INV
                   + info_ratio * PHI_INV ** 2)

        self._fitness_history.append(fitness)
        return fitness

    def record_trade(self, pnl: float, predicted_direction: float):
        """Record trade outcome for fitness computation."""
        self._trade_history.append([pnl, predicted_direction])
        self.update_bayesian_odds(pnl)

    # -------------------------------------------------------------------
    # DIAGNOSTICS
    # -------------------------------------------------------------------

    def get_diagnostics(self) -> Dict:
        """Full system diagnostic snapshot."""
        phi_vec = self.phi_h.to_vector()
        return {
            'generation': self._generation,
            'regime': self.regime,
            'regime_name': REGIME_NAMES.get(self.regime, "UNKNOWN"),
            'phi_hierarchy': {
                'alpha1': self.phi_h.alpha1,
                'alpha2': self.phi_h.alpha2,
                'alpha3': self.phi_h.alpha3,
                'alpha4': self.phi_h.alpha4,
                'alpha_sum': self.phi_h.alpha_sum(),
                'alpha_sum_target': SQRT5,
                'drift_from_sqrt5': abs(self.phi_h.alpha_sum() - SQRT5),
            },
            'V_learned_norm': float(np.linalg.norm(self._V_learned_weights)),
            'bayesian': {
                'prior_win': self.prior_win,
                'prior_loss': self.prior_loss,
                'odds': self.prior_win / max(self.prior_loss, 1e-8),
            },
            'learning_rates': dict(self._learning_rates),
            'fitness': self.compute_fitness(),
            'n_trades': len(self._trade_history),
            'param_momentum_norm': float(np.linalg.norm(self._param_momentum)),
        }


# ---------------------------------------------------------------------------
# MARKET STATE GENERATOR (for simulation / testing)
# ---------------------------------------------------------------------------

class SyntheticMarket:
    """Generate synthetic market states for testing the equation."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.price = 100.0
        self.t = 0
        self._regime_phase = 0.0

    def step(self) -> MarketState:
        """Generate next market state with regime-cycling dynamics."""
        self.t += 1
        self._regime_phase += 0.01

        # Regime-cycling volatility
        base_vol = 0.02 + 0.03 * abs(np.sin(self._regime_phase * PHI))

        # Price dynamics (geometric Brownian with regime shifts)
        drift = 0.0001 * np.sin(self._regime_phase * PHI_INV)
        shock = self.rng.randn() * base_vol
        ret = drift + shock
        self.price *= np.exp(ret)

        # Synthetic observables
        sync = 0.5 + 0.4 * np.sin(self._regime_phase * 2)
        corr_time = PHI_INV + 0.3 * np.cos(self._regime_phase * PHI)
        net_risk = max(0, 0.3 + 0.5 * np.sin(self._regime_phase * 3))
        delta = np.sin(self._regime_phase * PHI) * 0.5

        return MarketState(
            price=self.price,
            log_return=ret,
            volatility=base_vol,
            sync_ratio=np.clip(sync, 0, 1),
            correlation_time=max(0, corr_time),
            network_risk=np.clip(net_risk, 0, 1),
            delta_val=delta,
            volume=0.5 + 0.5 * self.rng.rand(),
            momentum=ret * 10,
        )


if __name__ == "__main__":
    print("=" * 70)
    print("  THE KAIROS EQUATION v3 - Self-Evolving Trading Algorithm")
    print("=" * 70)
    print()

    # Create equation with only 2 free parameters
    kairos = KairosEquationV3(capital=10000.0, edge_bias=0.05)
    market = SyntheticMarket(seed=42)

    print("Running 100 market steps (pre-evolution)...")
    print(f"{'t':>4} {'Regime':<22} {'H':>8} {'T':>8} {'Action':>10} {'Conf':>6}")
    print("-" * 65)

    for i in range(100):
        state = market.step()
        result = kairos.compute_action(state)

        # Record synthetic trade outcome
        pnl = state.log_return * result['action']
        kairos.record_trade(pnl, np.sign(result['action']))

        if i % 10 == 0:
            print(f"{result['t']:4d} {result['regime_name']:<22} "
                  f"{result['hamiltonian']:8.4f} {result['temperature']:8.4f} "
                  f"{result['action']:10.2f} {result['confidence']:6.4f}")

    print()
    diag = kairos.get_diagnostics()
    print(f"Alpha sum: {diag['phi_hierarchy']['alpha_sum']:.6f} "
          f"(target sqrt(5) = {SQRT5:.6f})")
    print(f"Fitness: {diag['fitness']:.4f}")
    print(f"Generation: {diag['generation']}")
    print()
    print("v3 core ready. Self-modification engine in kairos_self_modification.py")
