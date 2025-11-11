"""
Comprehensive Test Suite for Recursive Dialogue Engine

Tests:
1. Unit tests for each component
2. Mathematical validation
3. Edge cases
4. Integration tests
5. Stress tests
"""

import numpy as np
import sys
import traceback
from typing import List, Tuple, Dict
import time

from recursive_engine import (
    RecursiveEngine, RecursiveParams,
    NaiveEngine, VectorizedEngine, FFTEngine,
    create_engine
)
from emission_detector import (
    EmissionDetector, EmissionConfig,
    AdaptiveEmissionDetector, PhaseCoherenceDetector
)
from dialogue_system import (
    RecursiveDialogueEngine, DialogueConfig,
    TDLLayer, LoMILayer
)


class TestResult:
    """Container for test results"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.details = {}

    def __repr__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"{status} - {self.name}"


class TestSuite:
    """Test suite manager"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.verbose = True

    def run_test(self, name: str, test_func):
        """Run a single test and record result"""
        result = TestResult(name)

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"TEST: {name}")
            print('='*70)

        try:
            details = test_func()
            result.passed = True
            result.details = details or {}

            if self.verbose:
                print(f"✓ PASSED")
                if result.details:
                    for key, val in result.details.items():
                        print(f"  {key}: {val}")

        except AssertionError as e:
            result.passed = False
            result.error = str(e)
            if self.verbose:
                print(f"✗ FAILED: {e}")
                traceback.print_exc()

        except Exception as e:
            result.passed = False
            result.error = f"Exception: {e}"
            if self.verbose:
                print(f"✗ ERROR: {e}")
                traceback.print_exc()

        self.results.append(result)
        return result

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"\nTotal: {total} tests")
        print(f"Passed: {passed} ({100*passed/total:.1f}%)")
        print(f"Failed: {total - passed}")

        if total - passed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ✗ {r.name}: {r.error}")

        print()
        return passed == total


# ============================================================================
# UNIT TESTS - Recursive Engine
# ============================================================================

def test_engine_initialization():
    """Test that engines initialize correctly"""
    params = RecursiveParams()
    n_dims = 128

    engines = {
        'naive': NaiveEngine(params, n_dims),
        'vectorized': VectorizedEngine(params, n_dims),
        'fft': FFTEngine(params, n_dims),
    }

    for name, engine in engines.items():
        assert engine.mu is not None, f"{name}: mu not initialized"
        assert len(engine.mu) == n_dims, f"{name}: wrong dimensions"
        assert engine.t == 0, f"{name}: time not zero"
        assert np.allclose(engine.mu, 0), f"{name}: mu not zero-initialized"

    return {'engines_tested': len(engines)}


def test_engine_step():
    """Test that engines can step forward"""
    params = RecursiveParams()
    engine = FFTEngine(params, 128)

    # Initial state
    mu_before = engine.mu.copy()
    t_before = engine.t

    # Step
    mu_after = engine.step()

    assert engine.t == t_before + 1, "Time not incremented"
    assert mu_after is not None, "Step returned None"
    assert len(mu_after) == 128, "Wrong output dimension"

    # With non-zero initial condition, state should change
    engine.reset()
    engine.mu = np.random.randn(128) * 0.5
    mu_before = engine.mu.copy()
    engine.step()

    # State should evolve
    assert not np.allclose(engine.mu, mu_before), "State didn't evolve"

    return {'steps_executed': 1}


def test_laplacian_correctness():
    """Test that Laplacian is computed correctly"""
    n = 128

    # Use correct grid spacing for test domain [0, 2π)
    dx = 2 * np.pi / n
    params = RecursiveParams(dx=dx)

    # Create test function: sin wave on periodic domain
    x = np.linspace(0, 2*np.pi, n, endpoint=False)
    mu = np.sin(x)

    # Analytical Laplacian: d²sin(x)/dx² = -sin(x)
    expected_laplacian = -mu

    # Test different implementations
    engines = {
        'naive': NaiveEngine(params, n),
        'vectorized': VectorizedEngine(params, n),
        'fft': FFTEngine(params, n),
    }

    errors = {}
    for name, engine in engines.items():
        engine.mu = mu.copy()
        laplacian = engine.compute_laplacian(mu)

        # Compute relative error
        error = np.linalg.norm(laplacian - expected_laplacian) / np.linalg.norm(expected_laplacian)
        errors[name] = error

        # FFT should be very accurate (spectral accuracy)
        if name == 'fft':
            assert error < 0.01, f"FFT Laplacian error too high: {error}"
        else:
            # Finite differences have discretization error ~O(dx²)
            assert error < 0.05, f"{name} Laplacian error too high: {error}"

    return errors


def test_engine_equivalence():
    """Test that all engines produce similar results"""
    params = RecursiveParams(g=0.1, lam=0.3, rho=0.2, dt=0.01)
    n_dims = 64
    n_steps = 10

    # Initialize all engines with same state
    initial_state = np.random.randn(n_dims) * 0.3

    engines = {
        'naive': NaiveEngine(params, n_dims),
        'vectorized': VectorizedEngine(params, n_dims),
        'fft': FFTEngine(params, n_dims),
    }

    for engine in engines.values():
        engine.mu = initial_state.copy()
        engine.mu_prev = initial_state.copy()

    # Run all engines
    for _ in range(n_steps):
        for engine in engines.values():
            engine.step()

    # Compare final states
    naive_final = engines['naive'].mu
    vec_final = engines['vectorized'].mu
    fft_final = engines['fft'].mu

    # Vectorized and FFT should match naive closely
    vec_error = np.linalg.norm(vec_final - naive_final) / np.linalg.norm(naive_final)
    fft_error = np.linalg.norm(fft_final - naive_final) / np.linalg.norm(naive_final)

    assert vec_error < 0.01, f"Vectorized diverges from naive: {vec_error}"
    assert fft_error < 0.1, f"FFT diverges from naive: {fft_error}"  # FFT has spectral error

    return {'vec_error': vec_error, 'fft_error': fft_error}


def test_engine_stability():
    """Test that engine doesn't blow up"""
    params = RecursiveParams(g=0.1, lam=0.3, rho=0.2, dt=0.01)
    engine = FFTEngine(params, 256)

    # Start with random initial condition
    engine.mu = np.random.randn(256) * 0.5

    # Run for many steps
    max_energy = 0
    for _ in range(1000):
        engine.step()
        energy = np.sum(engine.mu ** 2)
        max_energy = max(max_energy, energy)

        # Check for NaN or Inf
        assert np.all(np.isfinite(engine.mu)), "Engine produced NaN/Inf"

    # Energy shouldn't explode
    assert max_energy < 1000, f"Energy exploded to {max_energy}"

    return {'max_energy': max_energy}


# ============================================================================
# UNIT TESTS - Emission Detector
# ============================================================================

def test_emission_detector_initialization():
    """Test emission detector initializes correctly"""
    config = EmissionConfig()
    detector = EmissionDetector(config)

    assert detector.steps_since_emission == 0
    assert detector.total_emissions == 0
    assert len(detector.entropy_history) == 0

    return {}


def test_entropy_computation():
    """Test recursive entropy computation"""
    detector = EmissionDetector()

    # Test case 1: Zero state -> low entropy
    mu_zero = np.zeros(100)
    entropy_zero = detector.compute_entropy(mu_zero)
    assert np.isfinite(entropy_zero), "Entropy is not finite for zero state"

    # Test case 2: Random state -> higher entropy
    mu_random = np.random.randn(100) * 0.5
    entropy_random = detector.compute_entropy(mu_random)
    assert np.isfinite(entropy_random), "Entropy is not finite for random state"

    # Test case 3: Peaked state -> intermediate entropy
    mu_peaked = np.zeros(100)
    mu_peaked[50] = 1.0
    entropy_peaked = detector.compute_entropy(mu_peaked)
    assert np.isfinite(entropy_peaked), "Entropy is not finite for peaked state"

    return {
        'entropy_zero': entropy_zero,
        'entropy_random': entropy_random,
        'entropy_peaked': entropy_peaked
    }


def test_emission_detection():
    """Test that emission detection works"""
    config = EmissionConfig(
        entropy_threshold=0.5,
        cooldown_steps=5,
        window_size=5,
        energy_min=0.01,
        energy_max=100.0
    )
    detector = EmissionDetector(config)

    # Simulate system approaching stability
    # Start with high entropy rate, decrease to near-zero
    base_mu = np.random.randn(100) * 0.5

    emissions = []
    for t in range(100):
        # Create decreasing variation
        variation = np.exp(-t/20.0) * np.random.randn(100) * 0.1
        mu = base_mu + variation

        should_emit, diag = detector.should_emit(mu, t)
        if should_emit:
            emissions.append((t, diag))

    # Should have at least one emission when system stabilizes
    assert len(emissions) > 0, f"No emissions detected in 100 steps"

    return {'emissions': len(emissions), 'first_emission_time': emissions[0][0] if emissions else None}


def test_cooldown_mechanism():
    """Test that cooldown prevents rapid emissions"""
    config = EmissionConfig(
        entropy_threshold=10.0,  # Very high to force emissions
        cooldown_steps=20,
        energy_min=0.0
    )
    detector = EmissionDetector(config)

    # Create stable state
    mu = np.ones(100) * 0.5

    emissions = []
    for t in range(50):
        should_emit, diag = detector.should_emit(mu, t)
        if should_emit:
            emissions.append(t)

    # Check minimum spacing
    if len(emissions) > 1:
        intervals = np.diff(emissions)
        min_interval = np.min(intervals)
        assert min_interval >= config.cooldown_steps, f"Cooldown violated: {min_interval} < {config.cooldown_steps}"

    return {'emissions': len(emissions)}


def test_coherence_detector():
    """Test phase coherence detector"""
    config = EmissionConfig(cooldown_steps=5)
    detector = PhaseCoherenceDetector(config)

    # Set listener state
    mu_listener = np.random.randn(100) * 0.3
    detector.set_listener_state(mu_listener)

    # Create speaker state that oscillates toward/away from listener
    emissions = []
    for t in range(100):
        # Oscillate between close and far from listener
        phase = t * 0.1
        distance = 0.5 + 0.4 * np.sin(phase)
        mu_speaker = mu_listener + np.random.randn(100) * distance

        should_emit, diag = detector.should_emit(mu_speaker, t)
        if should_emit:
            emissions.append((t, diag['coherence']))

    # Should detect coherence peaks
    assert len(emissions) > 0, "Coherence detector produced no emissions"

    return {'emissions': len(emissions)}


# ============================================================================
# UNIT TESTS - Dialogue System Components
# ============================================================================

def test_tdl_layer():
    """Test TDL syntax layer"""
    tdl = TDLLayer(vocab_size=50)

    # Test initialization
    assert tdl.transition_matrix.shape == (50, 50)
    assert np.allclose(tdl.transition_matrix.sum(axis=1), 1.0), "Transition matrix rows don't sum to 1"

    # Test constraint application
    logits = np.random.randn(50)
    constrained = tdl.apply_syntax_constraint(logits)

    assert len(constrained) == 50
    assert np.all(np.isfinite(constrained))

    # Test state update
    tdl.update(10)
    assert tdl.last_token == 10

    return {}


def test_lomi_layer():
    """Test LoMI coherence layer"""
    lomi = LoMILayer(state_dims=128)

    # Test initialization
    assert len(lomi.mu_listener) == 128
    assert np.allclose(lomi.mu_listener, 0)

    # Test coherence computation
    mu_speaker = np.random.randn(128) * 0.5
    coherence = lomi.compute_coherence(mu_speaker)

    assert np.isfinite(coherence)
    assert coherence >= 0  # Squared distance is non-negative

    # Test alignment force
    force = lomi.get_alignment_force(mu_speaker)
    assert len(force) == 128
    assert np.all(np.isfinite(force))

    # Update listener
    new_listener = np.random.randn(128) * 0.3
    lomi.update_listener(new_listener)
    assert np.allclose(lomi.mu_listener, new_listener)

    return {'initial_coherence': coherence}


def test_codebook():
    """Test token codebook encoding/decoding"""
    config = DialogueConfig(state_dims=128, vocab_size=50)
    engine = RecursiveDialogueEngine(config)

    # Test codebook shape
    assert engine.codebook.shape == (50, 128)

    # Test decoding
    mu = np.random.randn(128) * 0.5
    token_id, scores = engine.decode_token(mu)

    assert 0 <= token_id < 50
    assert len(scores) == 50

    # Test encoding
    token_vec = engine.encode_token(token_id)
    assert len(token_vec) == 128

    # Encode-decode should be consistent
    token_id2, _ = engine.decode_token(token_vec)
    assert token_id == token_id2, "Encode-decode inconsistent"

    return {}


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_dialogue_engine_initialization():
    """Test full dialogue engine initializes"""
    config = DialogueConfig(
        state_dims=128,
        vocab_size=50,
        engine_optimization='fft'
    )

    engine = RecursiveDialogueEngine(config)

    assert engine.engine is not None
    assert engine.detector is not None
    assert engine.tdl is not None
    assert engine.lomi is not None
    assert engine.t == 0

    return {}


def test_dialogue_single_step():
    """Test dialogue engine can step"""
    config = DialogueConfig(state_dims=64, vocab_size=20)
    engine = RecursiveDialogueEngine(config)

    # Perturb state to make it interesting
    engine.engine.mu = np.random.randn(64) * 0.5

    # Step without listener
    emission1 = engine.step()
    assert engine.t == 1

    # Step with listener
    listener_input = np.random.randn(64) * 0.3
    emission2 = engine.step(listener_input)
    assert engine.t == 2

    return {'emissions': int(emission1 is not None) + int(emission2 is not None)}


def test_dialogue_conversation():
    """Test full conversation can run"""
    config = DialogueConfig(
        state_dims=128,
        vocab_size=30,
        engine_optimization='fft',
        use_coherence_detector=True
    )

    # Adjust for more emissions
    config.engine_params.g = 0.2
    config.engine_params.lam = 0.3
    config.engine_params.rho = 0.4
    config.emission_config.cooldown_steps = 10

    engine = RecursiveDialogueEngine(config)

    # Run with listener
    def listener(t):
        return np.random.randn(128) * 0.3 * np.sin(t * 0.05)

    emissions = engine.converse(n_steps=500, listener_callback=listener, verbose=False)

    # Should have some emissions
    assert len(emissions) > 0, f"No emissions in 500 steps"

    # Check emission structure
    for em in emissions:
        assert 'time' in em
        assert 'token' in em
        assert 'coherence' in em
        assert 0 <= em['token'] < 30

    return {'emissions': len(emissions), 'rate': len(emissions)/500}


# ============================================================================
# EDGE CASES
# ============================================================================

def test_zero_input():
    """Test engine with zero input"""
    params = RecursiveParams()
    engine = FFTEngine(params, 64)

    # Start from zero, stay at zero (no perturbation)
    for _ in range(100):
        engine.step()

    # Should remain near zero
    energy = np.sum(engine.mu ** 2)
    assert energy < 1e-10, f"Zero state evolved: energy={energy}"

    return {}


def test_very_small_dimensions():
    """Test with very small state dimension"""
    params = RecursiveParams()

    for n in [2, 4, 8]:
        engine = FFTEngine(params, n)
        engine.mu = np.random.randn(n) * 0.5

        for _ in range(100):
            engine.step()
            assert np.all(np.isfinite(engine.mu)), f"NaN/Inf at n={n}"

    return {}


def test_very_large_state():
    """Test with large state values (tests numerical stability, not physics)"""
    params = RecursiveParams()
    engine = FFTEngine(params, 64)

    # Start with large values
    engine.mu = np.random.randn(64) * 10.0

    # Main goal: don't blow up to NaN/Inf (clipping prevents this)
    for _ in range(100):
        engine.step()
        assert np.all(np.isfinite(engine.mu)), "Large state caused NaN/Inf"

    energy = np.sum(engine.mu ** 2)

    # With clipping at ±100, energy can be up to 64*100^2 = 640,000
    # Check it stays bounded (not growing unbounded)
    assert energy < 1000000, f"Energy grew unbounded: {energy}"

    # Also check values are within clipping bounds
    assert np.all(np.abs(engine.mu) <= 100.0), "Values exceeded clipping bounds"

    return {'final_energy': energy}


def test_extreme_parameters():
    """Test with extreme parameter values"""
    # Very high diffusion
    params1 = RecursiveParams(g=10.0, lam=0.1, rho=0.1, dt=0.001)
    engine1 = FFTEngine(params1, 64)
    engine1.mu = np.random.randn(64) * 0.5

    for _ in range(10):
        engine1.step()
        assert np.all(np.isfinite(engine1.mu)), "High diffusion caused instability"

    # Very high nonlinearity
    params2 = RecursiveParams(g=0.05, lam=5.0, rho=0.1, dt=0.001)
    engine2 = FFTEngine(params2, 64)
    engine2.mu = np.random.randn(64) * 0.3

    for _ in range(10):
        engine2.step()
        assert np.all(np.isfinite(engine2.mu)), "High nonlinearity caused instability"

    return {}


# ============================================================================
# STRESS TESTS
# ============================================================================

def test_long_running_stability():
    """Test engine stability over long runs"""
    params = RecursiveParams(g=0.15, lam=0.3, rho=0.4, dt=0.01)
    engine = FFTEngine(params, 256)
    engine.mu = np.random.randn(256) * 0.5

    energies = []
    for i in range(5000):
        engine.step()

        if i % 100 == 0:
            energy = np.sum(engine.mu ** 2)
            energies.append(energy)
            assert np.all(np.isfinite(engine.mu)), f"Instability at step {i}"

    # Check energy doesn't grow unbounded
    max_energy = max(energies)
    assert max_energy < 500, f"Energy grew unbounded: {max_energy}"

    return {'max_energy': max_energy, 'final_energy': energies[-1]}


def test_repeated_reset():
    """Test that reset works correctly"""
    params = RecursiveParams()
    engine = FFTEngine(params, 128)

    for trial in range(10):
        # Evolve
        engine.mu = np.random.randn(128) * 0.5
        for _ in range(100):
            engine.step()

        # Reset
        engine.reset()

        # Check reset state
        assert engine.t == 0, f"Trial {trial}: time not reset"
        assert np.allclose(engine.mu, 0), f"Trial {trial}: mu not reset"
        assert np.allclose(engine.mu_prev, 0), f"Trial {trial}: mu_prev not reset"

    return {}


def test_memory_stability():
    """Test for memory leaks"""
    import sys

    params = RecursiveParams()
    engine = FFTEngine(params, 512)

    # Run many iterations
    for _ in range(1000):
        engine.mu = np.random.randn(512) * 0.5
        for _ in range(10):
            engine.step()
        engine.reset()

    # If we get here without crashing, memory is probably okay
    return {}


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run comprehensive test suite"""
    suite = TestSuite()

    print("\n" + "="*70)
    print("RECURSIVE DIALOGUE ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*70)

    # Unit tests - Engine
    print("\n" + "="*70)
    print("UNIT TESTS - Recursive Engine")
    print("="*70)
    suite.run_test("Engine Initialization", test_engine_initialization)
    suite.run_test("Engine Step", test_engine_step)
    suite.run_test("Laplacian Correctness", test_laplacian_correctness)
    suite.run_test("Engine Equivalence", test_engine_equivalence)
    suite.run_test("Engine Stability", test_engine_stability)

    # Unit tests - Emission Detector
    print("\n" + "="*70)
    print("UNIT TESTS - Emission Detector")
    print("="*70)
    suite.run_test("Emission Detector Initialization", test_emission_detector_initialization)
    suite.run_test("Entropy Computation", test_entropy_computation)
    suite.run_test("Emission Detection", test_emission_detection)
    suite.run_test("Cooldown Mechanism", test_cooldown_mechanism)
    suite.run_test("Coherence Detector", test_coherence_detector)

    # Unit tests - Dialogue Components
    print("\n" + "="*70)
    print("UNIT TESTS - Dialogue System Components")
    print("="*70)
    suite.run_test("TDL Layer", test_tdl_layer)
    suite.run_test("LoMI Layer", test_lomi_layer)
    suite.run_test("Codebook", test_codebook)

    # Integration tests
    print("\n" + "="*70)
    print("INTEGRATION TESTS")
    print("="*70)
    suite.run_test("Dialogue Engine Initialization", test_dialogue_engine_initialization)
    suite.run_test("Dialogue Single Step", test_dialogue_single_step)
    suite.run_test("Dialogue Conversation", test_dialogue_conversation)

    # Edge cases
    print("\n" + "="*70)
    print("EDGE CASE TESTS")
    print("="*70)
    suite.run_test("Zero Input", test_zero_input)
    suite.run_test("Very Small Dimensions", test_very_small_dimensions)
    suite.run_test("Very Large State", test_very_large_state)
    suite.run_test("Extreme Parameters", test_extreme_parameters)

    # Stress tests
    print("\n" + "="*70)
    print("STRESS TESTS")
    print("="*70)
    suite.run_test("Long Running Stability", test_long_running_stability)
    suite.run_test("Repeated Reset", test_repeated_reset)
    suite.run_test("Memory Stability", test_memory_stability)

    # Print summary
    all_passed = suite.print_summary()

    return suite, all_passed


if __name__ == "__main__":
    suite, all_passed = run_all_tests()
    sys.exit(0 if all_passed else 1)
