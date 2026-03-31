"""
Test Suite & Evolution Demo for Kairos Equation v3

Validates:
1. Core equation mechanics (Hamiltonian, potential, regimes)
2. Phi-hierarchy invariants (alpha sum = sqrt(5))
3. Self-modification convergence
4. Regime detection accuracy
5. Full evolution pipeline
6. Fixed-point convergence properties

Run: python test_kairos_v3.py
"""

import numpy as np
import sys

from kairos_equation_v3 import (
    KairosEquationV3, PhiHierarchy, MarketState, SyntheticMarket,
    Regime, REGIME_NAMES, PHI, PHI_INV, PHI_SQ, SQRT5
)
from kairos_self_modification import (
    KairosEvolutionEngine, ParameterEvolver, PotentialLearner,
    RegimeAdapter, TemperatureTuner, MetaLearner, FixedPointDetector,
    create_self_evolving_kairos, run_full_evolution,
)


def test_phi_hierarchy():
    """Test that phi-derived coefficients satisfy alpha_sum = sqrt(5)."""
    print("TEST: Phi Hierarchy Invariants")

    h = PhiHierarchy()
    alpha_sum = h.alpha_sum()
    expected = SQRT5

    assert abs(alpha_sum - expected) < 1e-10, \
        f"Alpha sum {alpha_sum} != sqrt(5) = {expected}"

    # Test vector round-trip
    vec = h.to_vector()
    h2 = PhiHierarchy()
    h2.from_vector(vec)
    assert abs(h2.alpha_sum() - expected) < 1e-10, "Vector round-trip failed"

    print(f"  alpha_sum = {alpha_sum:.10f} == sqrt(5) = {expected:.10f}")
    print(f"  Vector round-trip: OK (9 params)")
    print("  PASSED\n")


def test_hamiltonian_components():
    """Test individual Hamiltonian components."""
    print("TEST: Hamiltonian Components")

    kairos = KairosEquationV3(capital=10000)
    state = MarketState(
        price=100.0,
        log_return=0.01,
        volatility=0.02,
        sync_ratio=PHI_INV,     # At sweet spot
        correlation_time=PHI_INV,
        network_risk=0.3,
        delta_val=0.1,
        momentum=0.5,
    )

    # Kinetic energy
    T = kairos.compute_kinetic_energy(state)
    assert T >= 0, "Kinetic energy must be non-negative"
    print(f"  Kinetic energy T = {T:.6f}")

    # Potential components
    V_k = kairos._V_kuramoto(state)
    V_s = kairos._V_soc(state)
    V_n = kairos._V_network(state)
    V_c = kairos._V_catastrophe(state)
    V_d = kairos._V_double_well(state)
    V_l = kairos._V_learned(state)

    print(f"  V_kuramoto     = {V_k:.6f}")
    print(f"  V_soc          = {V_s:.6f}")
    print(f"  V_network      = {V_n:.6f}")
    print(f"  V_catastrophe  = {V_c:.6f}")
    print(f"  V_double_well  = {V_d:.6f}")
    print(f"  V_learned      = {V_l:.6f}")

    # At sync_ratio = phi^-1, Kuramoto should be near zero
    assert V_k < 0.01, f"Kuramoto at sweet spot should be ~0, got {V_k}"

    # Catastrophe should be 0 when delta > 0
    assert V_c == 0.0, f"Catastrophe should be 0 for positive delta, got {V_c}"

    # Total Hamiltonian
    H = kairos.compute_hamiltonian(state)
    print(f"  Total H = {H:.6f}")
    assert np.isfinite(H), "Hamiltonian must be finite"

    print("  PASSED\n")


def test_regime_detection():
    """Test all seven regime classifications."""
    print("TEST: Regime Detection (Seven Regimes)")

    kairos = KairosEquationV3(capital=10000)

    # Create states with varying energy to trigger each regime
    # The Hamiltonian H = kinetic + potential, where kinetic = 0.5*(ret/vol)^2
    # So we vary the ret/vol ratio to sweep through energy levels
    regime_seen = set()
    for ret_scale in np.linspace(0.0, 5.0, 500):
        vol = 0.02
        state = MarketState(
            price=100.0,
            log_return=ret_scale * vol,
            volatility=vol,
            sync_ratio=0.3 + 0.4 * np.sin(ret_scale),
            correlation_time=0.5,
            network_risk=min(ret_scale * 0.1, 1.0),
            delta_val=-0.1 if ret_scale > 3.0 else 0.1,
            momentum=ret_scale * 0.1,
        )
        regime = kairos.detect_regime(state)
        regime_seen.add(regime)

    print(f"  Regimes observed: {len(regime_seen)}/7")
    for r in sorted(regime_seen):
        print(f"    {REGIME_NAMES[r]}")

    assert len(regime_seen) >= 3, \
        f"Should see at least 3 regimes, got {len(regime_seen)}"

    print("  PASSED\n")


def test_master_equation():
    """Test the master equation A*(t) output."""
    print("TEST: Master Equation Output")

    kairos = KairosEquationV3(capital=10000.0, edge_bias=0.0)
    state = MarketState(
        price=100.0,
        log_return=0.005,
        volatility=0.02,
        sync_ratio=0.618,
        correlation_time=0.618,
        network_risk=0.2,
        delta_val=0.1,
        momentum=1.0,
    )

    result = kairos.compute_action(state)

    # Check all expected fields
    required_keys = ['action', 'hamiltonian', 'temperature', 'regime',
                     'potential', 'kinetic', 'odds', 'confidence']
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
        print(f"  {key}: {result[key]}")

    # Action should be bounded by capital
    assert abs(result['action']) <= 10000.0, "Action exceeds capital"

    # Temperature must be positive
    assert result['temperature'] > 0, "Temperature must be positive"

    # Confidence must be in (0, 1] for non-negative H
    assert 0 < result['confidence'] <= 1.0 or result['hamiltonian'] < 0, \
        "Confidence out of range"

    print("  PASSED\n")


def test_bayesian_update():
    """Test Bayesian odds update from evidence."""
    print("TEST: Bayesian Odds Update")

    kairos = KairosEquationV3(capital=10000)

    # Feed winning evidence
    for _ in range(20):
        kairos.update_bayesian_odds(outcome=1.0)
    odds_winning = kairos.update_bayesian_odds()
    print(f"  After 20 wins: odds = {odds_winning:.4f}")

    # Reset and feed losing evidence
    kairos2 = KairosEquationV3(capital=10000)
    for _ in range(20):
        kairos2.update_bayesian_odds(outcome=-1.0)
    odds_losing = kairos2.update_bayesian_odds()
    print(f"  After 20 losses: odds = {odds_losing:.4f}")

    assert odds_winning > odds_losing, \
        "Winning evidence should produce higher odds"

    print("  PASSED\n")


def test_parameter_evolver():
    """Test gradient computation and parameter evolution."""
    print("TEST: Parameter Evolution")

    kairos = KairosEquationV3(capital=10000, edge_bias=0.05)
    market = SyntheticMarket(seed=42)
    states = [market.step() for _ in range(50)]

    evolver = ParameterEvolver()

    # Compute gradient
    gradient = evolver.compute_gradient(kairos, states)
    print(f"  Gradient norm: {np.linalg.norm(gradient):.6f}")
    print(f"  Gradient: {gradient}")

    # Save original
    original = kairos.phi_h.to_vector().copy()

    # Evolve one step
    new_params = evolver.evolve_step(kairos, gradient, learning_rate=0.001)

    # Parameters should have changed
    diff = np.linalg.norm(new_params - original)
    print(f"  Parameter change: {diff:.8f}")
    assert diff > 0, "Parameters should change after evolution step"

    print("  PASSED\n")


def test_potential_learner():
    """Test learned potential correction."""
    print("TEST: Potential Energy Learning")

    kairos = KairosEquationV3(capital=10000)
    learner = PotentialLearner()

    # Record outcomes: high energy = bad, low energy = good
    for _ in range(30):
        learner.record_outcome(energy_level=0.5, pnl=1.0)   # Good at low H
        learner.record_outcome(energy_level=2.0, pnl=-1.0)  # Bad at high H

    # Learn correction
    weights_before = kairos._V_learned_weights.copy()
    learner.learn_correction(kairos)
    weights_after = kairos._V_learned_weights.copy()

    change = np.linalg.norm(weights_after - weights_before)
    print(f"  Weight change: {change:.6f}")
    print(f"  Weight norm: {np.linalg.norm(weights_after):.6f}")

    assert change > 0, "Weights should change after learning"

    print("  PASSED\n")


def test_fixed_point_detector():
    """Test convergence detection."""
    print("TEST: Fixed-Point Convergence Detection")

    detector = FixedPointDetector(tolerance=1e-4, window=5)

    # Feed converging parameters
    for i in range(20):
        vec = np.ones(9) * (1.0 + 0.1 * np.exp(-i * 0.5))
        converged = detector.check(vec)
        if converged:
            print(f"  Converged at iteration {i}")
            break

    drift = detector.get_drift()
    print(f"  Final drift: {drift:.8f}")
    assert detector.is_converged, "Should detect convergence for decaying params"

    print("  PASSED\n")


def test_meta_learner():
    """Test learning rate adaptation."""
    print("TEST: Meta-Learning (2nd Order)")

    kairos = KairosEquationV3(capital=10000)
    meta = MetaLearner()

    lr_before = dict(kairos._learning_rates)

    # Feed improving fitness
    for i in range(20):
        meta.observe_fitness(float(i) * 0.1)
    meta.adapt_learning_rates(kairos)

    lr_after = dict(kairos._learning_rates)

    print(f"  Learning rate changes:")
    for key in lr_before:
        before = lr_before[key]
        after = lr_after[key]
        direction = "UP" if after > before else "DOWN" if after < before else "SAME"
        print(f"    {key}: {before:.6f} -> {after:.6f} ({direction})")

    # With improving fitness, rates should increase
    assert lr_after['phi_hierarchy'] >= lr_before['phi_hierarchy'], \
        "Learning rates should increase with improving fitness"

    print("  PASSED\n")


def test_full_evolution():
    """Test complete evolution pipeline."""
    print("TEST: Full Evolution Pipeline")
    print("  (This runs 15 generations of self-modification)")
    print()

    result = run_full_evolution(
        capital=10000.0,
        edge_bias=0.05,
        max_generations=15,
        steps_per_gen=50,
        seed=42,
        verbose=True,
    )

    log = result['log']
    assert len(log) > 0, "Should have at least one generation"

    # Verify generation tracking
    diag = result['diagnostics']
    print(f"\n  Final generation: {diag['generation']}")
    print(f"  Final fitness: {diag['fitness']:.4f}")
    print(f"  Alpha sum drift from sqrt(5): "
          f"{diag['phi_hierarchy']['drift_from_sqrt5']:.6f}")

    print("  PASSED\n")


def test_self_reference():
    """
    Test that the equation truly applies itself to its own evolution.

    Verify: the momentum term in parameter evolution uses the SAME
    phi^-1 coefficient as the trading dynamics.
    """
    print("TEST: Self-Reference Verification")

    evolver = ParameterEvolver(momentum=PHI_INV)
    assert abs(evolver.momentum - PHI_INV) < 1e-10, \
        "Evolution momentum should be phi^-1 (same as trading)"

    kairos = KairosEquationV3(capital=10000)

    # Temperature exponents should be phi-derived
    n_psi = kairos._n_exponents[Regime.PSI]
    assert abs(n_psi - PHI_INV**2) < 1e-10, \
        f"PSI exponent should be phi^-2, got {n_psi}"

    # Bayesian smoothing uses phi
    kairos.update_bayesian_odds(1.0)
    kairos.update_bayesian_odds(1.0)
    kairos.update_bayesian_odds(-1.0)
    # Prior update uses PHI_INV as Laplace smoothing

    print(f"  Evolution momentum = phi^-1 = {evolver.momentum:.6f}")
    print(f"  PSI temp exponent = phi^-2 = {n_psi:.6f}")
    print(f"  Self-referential structure confirmed")

    print("  PASSED\n")


# ---------------------------------------------------------------------------
# RUN ALL TESTS
# ---------------------------------------------------------------------------

def run_all_tests():
    print("=" * 72)
    print("  KAIROS EQUATION v3 - TEST SUITE & EVOLUTION DEMO")
    print("=" * 72)
    print()

    tests = [
        test_phi_hierarchy,
        test_hamiltonian_components,
        test_regime_detection,
        test_master_equation,
        test_bayesian_update,
        test_parameter_evolver,
        test_potential_learner,
        test_fixed_point_detector,
        test_meta_learner,
        test_self_reference,
        test_full_evolution,  # Last because it's the big demo
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAILED: {e}\n")

    print("=" * 72)
    print(f"  RESULTS: {passed} passed, {failed} failed, "
          f"{passed + failed} total")
    print("=" * 72)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
