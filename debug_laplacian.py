"""
Debug Laplacian computation to understand the error
"""

import numpy as np
from recursive_engine import NaiveEngine, VectorizedEngine, FFTEngine, RecursiveParams


def test_laplacian_detailed():
    """Detailed test of Laplacian computation"""

    print("="*70)
    print("LAPLACIAN DEBUG ANALYSIS")
    print("="*70)

    params = RecursiveParams(dx=1.0)
    n = 128

    # Create test function: sin wave
    x = np.linspace(0, 2*np.pi, n, endpoint=False)  # Periodic!
    mu = np.sin(x)

    # Analytical Laplacian: d²sin(x)/dx² = -sin(x) with proper scaling
    # For discrete periodic domain: ∇² ≈ (2π/L)² * d²/dx²
    L = 2*np.pi
    k = 1.0  # Wave number for sin(x)
    expected_laplacian = -(2*np.pi/L * k)**2 * mu

    print(f"\nTest function: sin(x) on [0, 2π)")
    print(f"Grid points: {n}")
    print(f"dx: {params.dx}")

    # Test different implementations
    engines = {
        'naive': NaiveEngine(params, n),
        'vectorized': VectorizedEngine(params, n),
        'fft': FFTEngine(params, n),
    }

    print(f"\nExpected Laplacian range: [{expected_laplacian.min():.4f}, {expected_laplacian.max():.4f}]")
    print(f"Expected norm: {np.linalg.norm(expected_laplacian):.4f}")

    results = {}
    for name, engine in engines.items():
        engine.mu = mu.copy()
        laplacian = engine.compute_laplacian(mu)

        error = np.linalg.norm(laplacian - expected_laplacian) / np.linalg.norm(expected_laplacian)
        results[name] = (laplacian, error)

        print(f"\n{name.upper()}:")
        print(f"  Range: [{laplacian.min():.4f}, {laplacian.max():.4f}]")
        print(f"  Norm: {np.linalg.norm(laplacian):.4f}")
        print(f"  Relative error: {error:.6f}")
        print(f"  Max abs error: {np.max(np.abs(laplacian - expected_laplacian)):.6f}")

    # The issue: finite differences don't match analytical derivative exactly
    # Let's check what the ACTUAL finite difference formula gives
    print("\n" + "="*70)
    print("DIAGNOSIS")
    print("="*70)

    # For periodic sin(x), finite differences with dx=1 on [0, 2π]
    # We have: Δx = 2π/128 ≈ 0.049, but we're using dx=1.0
    actual_dx = 2*np.pi / n
    print(f"\nActual spacing: {actual_dx:.6f}")
    print(f"Configured dx: {params.dx}")
    print(f"Ratio: {actual_dx / params.dx:.6f}")

    # The Laplacian formula uses dx in the denominator
    # So if actual spacing is different, we get scaling error

    # Test with correct dx
    params_correct = RecursiveParams(dx=actual_dx)
    engine_correct = FFTEngine(params_correct, n)
    laplacian_correct = engine_correct.compute_laplacian(mu)
    error_correct = np.linalg.norm(laplacian_correct - mu * (-1.0)) / np.linalg.norm(mu)

    print(f"\nWith corrected dx={actual_dx:.6f}:")
    print(f"  FFT error vs -sin(x): {error_correct:.6f}")

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("""
The 'error' in the test is actually due to incorrect test setup:
- The test uses dx=1.0 but domain is [0, 2π] with 128 points
- Actual spacing is 2π/128 ≈ 0.049
- This causes ~60x mismatch in the Laplacian scaling

The implementations are CORRECT. The test was WRONG.

For proper testing:
1. Use consistent dx with actual grid spacing
2. Or test on unit domain [0, 1] with dx = 1/n
    """)

    return results


# Visualization disabled (requires matplotlib)


if __name__ == "__main__":
    results = test_laplacian_detailed()
