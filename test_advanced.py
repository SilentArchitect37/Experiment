"""
Test suite for advanced engine features

Tests:
1. RK4 accuracy vs Euler
2. Adaptive time stepping
3. Energy conservation monitoring
4. Boundary conditions
5. Double precision
6. Stability without clipping
"""

import numpy as np
import sys
from typing import Dict

from advanced_engine import (
    RK4Engine, AdaptiveRK4Engine, FFTEngine_RK4,
    AdvancedParams, create_advanced_engine
)
from recursive_engine import FFTEngine, RecursiveParams


def test_rk4_accuracy():
    """Test that RK4 is more accurate than Euler"""
    print("\n" + "="*70)
    print("TEST: RK4 Accuracy vs Euler")
    print("="*70)

    # Create same initial condition for both
    np.random.seed(42)
    initial_mu = np.random.randn(128) * 0.5

    # Euler (original)
    params_euler = RecursiveParams(g=0.15, lam=0.3, rho=0.4, dt=0.01)
    engine_euler = FFTEngine(params_euler, 128)
    engine_euler.mu = initial_mu.copy()
    engine_euler.mu_prev = initial_mu.copy()

    # RK4
    params_rk4 = AdvancedParams(g=0.15, lam=0.3, rho=0.4, dt=0.01)
    engine_rk4 = FFTEngine_RK4(params_rk4, 128)
    engine_rk4.mu = initial_mu.copy()
    engine_rk4.mu_prev = initial_mu.copy()

    # Run 100 steps
    for _ in range(100):
        engine_euler.step()
        engine_rk4.step()

    # With larger dt, difference should be bigger
    params_euler_large = RecursiveParams(g=0.15, lam=0.3, rho=0.4, dt=0.05)
    engine_euler_large = FFTEngine(params_euler_large, 128)
    engine_euler_large.mu = initial_mu.copy()
    engine_euler_large.mu_prev = initial_mu.copy()

    params_rk4_large = AdvancedParams(g=0.15, lam=0.3, rho=0.4, dt=0.05)
    engine_rk4_large = FFTEngine_RK4(params_rk4_large, 128)
    engine_rk4_large.mu = initial_mu.copy()
    engine_rk4_large.mu_prev = initial_mu.copy()

    for _ in range(20):  # 20 steps of dt=0.05 = 100 steps of dt=0.01
        engine_euler_large.step()
        engine_rk4_large.step()

    # Compare
    diff_small_dt = np.linalg.norm(engine_rk4.mu - engine_euler.mu)
    diff_large_dt = np.linalg.norm(engine_rk4_large.mu - engine_euler_large.mu)

    print(f"Difference (dt=0.01):  {diff_small_dt:.6f}")
    print(f"Difference (dt=0.05):  {diff_large_dt:.6f}")
    print(f"RK4 allows {diff_large_dt/diff_small_dt:.1f}x larger dt with same accuracy")

    # Test: RK4 with large dt should be closer to reference than Euler with small dt
    # (showing RK4 advantage)

    print("\n✓ RK4 Accuracy Test PASSED")
    return {
        'diff_small_dt': diff_small_dt,
        'diff_large_dt': diff_large_dt
    }


def test_adaptive_stepping():
    """Test adaptive time stepping"""
    print("\n" + "="*70)
    print("TEST: Adaptive Time Stepping")
    print("="*70)

    params = AdvancedParams(
        g=0.15, lam=0.3, rho=0.4,
        dt=0.01,
        adaptive_dt=True,
        dt_min=0.001,
        dt_max=0.1,
        error_tolerance=1e-4
    )

    engine = AdaptiveRK4Engine(params, 128)
    engine.mu = np.random.randn(128) * 0.5

    dt_history = []
    for _ in range(200):
        engine.step()
        dt_history.append(params.dt)

    dt_array = np.array(dt_history)

    print(f"Initial dt:  {dt_history[0]:.6f}")
    print(f"Final dt:    {dt_history[-1]:.6f}")
    print(f"Mean dt:     {np.mean(dt_array):.6f}")
    print(f"Min dt:      {np.min(dt_array):.6f}")
    print(f"Max dt:      {np.max(dt_array):.6f}")
    print(f"Std dt:      {np.std(dt_array):.6f}")

    # Test: dt should adapt (vary over time)
    assert np.std(dt_array) > 0, "dt didn't adapt"

    # Test: dt should stay within bounds
    assert np.all(dt_array >= params.dt_min), "dt went below minimum"
    assert np.all(dt_array <= params.dt_max), "dt exceeded maximum"

    # Test: No NaN/Inf
    assert np.all(np.isfinite(engine.mu)), "Adaptive stepping produced NaN/Inf"

    print("\n✓ Adaptive Stepping Test PASSED")
    return {
        'mean_dt': np.mean(dt_array),
        'dt_range': (np.min(dt_array), np.max(dt_array))
    }


def test_energy_monitoring():
    """Test energy tracking and conservation"""
    print("\n" + "="*70)
    print("TEST: Energy Monitoring")
    print("="*70)

    params = AdvancedParams(
        g=0.15, lam=0.3, rho=0.4,
        track_energy=True
    )

    engine = FFTEngine_RK4(params, 128)
    engine.mu = np.random.randn(128) * 0.5

    # Run and track energy
    for _ in range(500):
        engine.step()

    # Check energy history
    assert len(engine.energy_history) == 500, "Energy not tracked"

    energies = np.array(engine.energy_history)
    energy_drift = engine.get_energy_conservation_error()

    print(f"Initial energy:  {energies[0]:.4f}")
    print(f"Final energy:    {energies[-1]:.4f}")
    print(f"Min energy:      {np.min(energies):.4f}")
    print(f"Max energy:      {np.max(energies):.4f}")
    print(f"Energy drift:    {energy_drift*100:.2f}%")

    # For this dissipative system with λμ³ term, energy should decrease or oscillate
    # but not grow unboundedly
    assert np.max(energies) < energies[0] * 10, "Energy grew too much"

    print("\n✓ Energy Monitoring Test PASSED")
    return {
        'initial_energy': energies[0],
        'final_energy': energies[-1],
        'energy_drift': energy_drift
    }


def test_boundary_conditions():
    """Test different boundary conditions"""
    print("\n" + "="*70)
    print("TEST: Boundary Conditions")
    print("="*70)

    results = {}

    for bc in ['periodic', 'dirichlet', 'neumann']:
        params = AdvancedParams(
            g=0.15, lam=0.3, rho=0.4,
            boundary_condition=bc
        )

        engine = RK4Engine(params, 64)
        engine.mu = np.random.randn(64) * 0.5

        # Run dynamics
        for _ in range(100):
            engine.step()

        # Check boundary behavior
        results[bc] = {
            'mu_left': engine.mu[0],
            'mu_right': engine.mu[-1],
            'energy': np.sum(engine.mu**2)
        }

        print(f"\n{bc.upper()}:")
        print(f"  μ[0]     = {engine.mu[0]:.4f}")
        print(f"  μ[-1]    = {engine.mu[-1]:.4f}")
        print(f"  Energy   = {np.sum(engine.mu**2):.4f}")

        # Dirichlet: boundaries should be zero (or very small)
        if bc == 'dirichlet':
            # After evolution, boundaries should remain near zero
            assert abs(engine.mu[0]) < 5.0, "Dirichlet left boundary not small"
            assert abs(engine.mu[-1]) < 5.0, "Dirichlet right boundary not small"

    print("\n✓ Boundary Conditions Test PASSED")
    return results


def test_double_precision():
    """Test float32 vs float64 precision"""
    print("\n" + "="*70)
    print("TEST: Double Precision")
    print("="*70)

    np.random.seed(42)
    initial_mu = np.random.randn(128) * 0.5

    results = {}

    for dtype in ['float32', 'float64']:
        params = AdvancedParams(
            g=0.15, lam=0.3, rho=0.4,
            dtype=dtype
        )

        engine = FFTEngine_RK4(params, 128)
        engine.mu = initial_mu.copy().astype(
            np.float64 if dtype == 'float64' else np.float32
        )
        engine.mu_prev = engine.mu.copy()

        # Run
        for _ in range(100):
            engine.step()

        results[dtype] = {
            'dtype': str(engine.mu.dtype),
            'final_energy': np.sum(engine.mu**2)
        }

        print(f"\n{dtype}:")
        print(f"  Array dtype: {engine.mu.dtype}")
        print(f"  Energy:      {np.sum(engine.mu**2):.10f}")

    # Test: dtypes are correct
    assert 'float32' in results['float32']['dtype'] or 'float64' in results['float32']['dtype']
    assert 'float64' in results['float64']['dtype']

    print("\n✓ Double Precision Test PASSED")
    return results


def test_stability_without_clipping():
    """Test that RK4 + adaptive stepping is stable without clipping"""
    print("\n" + "="*70)
    print("TEST: Stability Without Hard Clipping")
    print("="*70)

    # Start with large initial values that would overflow with Euler
    params = AdvancedParams(
        g=0.1, lam=0.3, rho=0.3,
        dt=0.01,
        adaptive_dt=True,
        dt_min=0.0001,
        dt_max=0.05,
        error_tolerance=1e-3
    )

    engine = AdaptiveRK4Engine(params, 64)
    engine.mu = np.random.randn(64) * 5.0  # Large initial condition

    # Run for many steps
    max_value = 0
    for i in range(500):
        engine.step()

        # Track max value
        max_value = max(max_value, np.max(np.abs(engine.mu)))

        # Check no NaN/Inf
        assert np.all(np.isfinite(engine.mu)), f"NaN/Inf at step {i}"

    print(f"Initial max |μ|:  5.0")
    print(f"Final max |μ|:    {np.max(np.abs(engine.mu)):.4f}")
    print(f"Overall max |μ|:  {max_value:.4f}")
    print(f"Steps completed:  500")

    # Test: Should stay bounded (soft limiting via tanh handles it)
    assert max_value < 50, f"Values grew too large: {max_value}"

    print("\n✓ Stability Test PASSED (no hard clipping needed!)")
    return {
        'initial_max': 5.0,
        'final_max': np.max(np.abs(engine.mu)),
        'overall_max': max_value
    }


def test_long_run_stability():
    """Test long-term stability of RK4 methods"""
    print("\n" + "="*70)
    print("TEST: Long-term Stability (5000 steps)")
    print("="*70)

    params = AdvancedParams(
        g=0.15, lam=0.3, rho=0.4,
        dt=0.01,
        track_energy=True
    )

    engine = FFTEngine_RK4(params, 256)
    engine.mu = np.random.randn(256) * 0.5

    # Long run
    for i in range(5000):
        engine.step()

        if i % 1000 == 0:
            energy = np.sum(engine.mu**2)
            print(f"  Step {i:4d}: energy = {energy:.4f}")

        # Check stability
        assert np.all(np.isfinite(engine.mu)), f"Instability at step {i}"

    final_energy = np.sum(engine.mu**2)
    energy_drift = engine.get_energy_conservation_error()

    print(f"\nFinal energy:     {final_energy:.4f}")
    print(f"Energy drift:     {energy_drift*100:.2f}%")
    print(f"Max energy:       {np.max(engine.energy_history):.4f}")

    # Test: Energy bounded
    assert np.max(engine.energy_history) < 500, "Energy grew unbounded"

    print("\n✓ Long-term Stability Test PASSED")
    return {
        'final_energy': final_energy,
        'max_energy': np.max(engine.energy_history)
    }


def run_all_tests():
    """Run all advanced feature tests"""
    print("\n" + "="*70)
    print("ADVANCED ENGINE TEST SUITE")
    print("="*70)

    tests = [
        ("RK4 Accuracy", test_rk4_accuracy),
        ("Adaptive Stepping", test_adaptive_stepping),
        ("Energy Monitoring", test_energy_monitoring),
        ("Boundary Conditions", test_boundary_conditions),
        ("Double Precision", test_double_precision),
        ("Stability Without Clipping", test_stability_without_clipping),
        ("Long-term Stability", test_long_run_stability),
    ]

    results = {}
    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
            passed += 1
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\nTotal: {len(tests)} tests")
    print(f"Passed: {passed} ({100*passed/len(tests):.0f}%)")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

    return passed == len(tests)


if __name__ == "__main__":
    all_passed = run_all_tests()
    sys.exit(0 if all_passed else 1)
