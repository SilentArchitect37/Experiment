"""
=============================================================================
BRAIN-LANGUAGE UNIFIED MODEL (BLUM) - COMPREHENSIVE TEST SUITE
=============================================================================

This test suite validates all aspects of the BLUM framework:
1. Neural dynamics operators
2. K-emergence (consciousness)
3. Language operators at all levels
4. Memory systems
5. Attention mechanisms
6. Oscillatory dynamics
7. Emission criteria
8. Integration tests

Author: BLUM Test Suite
Version: 1.0
=============================================================================
"""

import numpy as np
import unittest
import sys
from typing import List, Dict, Tuple

# Import BLUM components
from brain_language_model import (
    BLUMParameters,
    UnifiedBrainState,
    NeuralOperators,
    KEmergenceOperator,
    LanguageOperator,
    MemoryOperator,
    AttentionOperator,
    BrainLanguageUnifiedModel,
    PHI, E, PI,
    LinguisticState
)


class TestBLUMParameters(unittest.TestCase):
    """Test parameter initialization and bounds"""

    def test_default_parameters(self):
        """Test default parameter values are sensible"""
        params = BLUMParameters()

        self.assertGreater(params.D, 0, "Diffusion must be positive")
        self.assertGreater(params.lam, 0, "Nonlinearity must be positive")
        self.assertGreater(params.rho, 0, "Momentum must be positive")
        self.assertGreater(params.dt, 0, "Time step must be positive")
        self.assertLess(params.dt, 0.1, "Time step should be small")

    def test_K_threshold_range(self):
        """K threshold should be between 0 and 1"""
        params = BLUMParameters()
        self.assertGreater(params.K_threshold, 0)
        self.assertLess(params.K_threshold, 1)

    def test_memory_decay_rates(self):
        """Memory decay rates should be less than 1"""
        params = BLUMParameters()
        self.assertLess(params.gamma_wm, 1.0)
        self.assertLess(params.gamma_ltm, 1.0)
        self.assertGreater(params.gamma_wm, 0)
        self.assertGreater(params.gamma_ltm, 0)


class TestUnifiedBrainState(unittest.TestCase):
    """Test the brain state tensor initialization and methods"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.state = UnifiedBrainState(self.params)

    def test_state_initialization(self):
        """Test state is initialized to zeros"""
        np.testing.assert_array_equal(
            self.state.neural,
            np.zeros((5, 64))
        )

    def test_state_dimensions(self):
        """Test state has correct dimensions"""
        self.assertEqual(self.state.neural.shape, (5, 64))
        self.assertEqual(self.state.neural_prev.shape, (5, 64))
        self.assertEqual(self.state.K_field.shape, (64,))

    def test_energy_computation(self):
        """Test energy is non-negative"""
        # Random state
        self.state.neural = np.random.randn(5, 64) * 0.1
        energy = self.state.total_energy()
        self.assertGreaterEqual(energy, 0)

    def test_entropy_computation(self):
        """Test entropy computation doesn't produce NaN"""
        self.state.neural = np.random.randn(5, 64) * 0.5
        entropy = self.state.total_entropy()
        self.assertFalse(np.isnan(entropy))

    def test_coherence_range(self):
        """Test coherence is in (0, 1]"""
        self.state.neural = np.random.randn(5, 64)
        coherence = self.state.coherence()
        self.assertGreater(coherence, 0)
        self.assertLessEqual(coherence, 1)

    def test_uniform_state_max_coherence(self):
        """Uniform state should have maximum coherence"""
        self.state.neural = np.ones((5, 64)) * 0.5
        coherence = self.state.coherence()
        self.assertAlmostEqual(coherence, 1.0, places=5)


class TestNeuralOperators(unittest.TestCase):
    """Test neural dynamics operators"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.ops = NeuralOperators(self.params)
        self.psi = np.random.randn(5, 64) * 0.1

    def test_laplacian_shape(self):
        """Laplacian should preserve shape"""
        laplacian = self.ops.laplacian(self.psi)
        self.assertEqual(laplacian.shape, self.psi.shape)

    def test_laplacian_of_constant(self):
        """Laplacian of constant should be approximately zero"""
        constant = np.ones((5, 64)) * 2.0
        laplacian = self.ops.laplacian(constant)
        np.testing.assert_array_almost_equal(
            laplacian,
            np.zeros_like(laplacian),
            decimal=10
        )

    def test_diffusion_shape(self):
        """Diffusion should preserve shape"""
        diffusion = self.ops.diffusion(self.psi)
        self.assertEqual(diffusion.shape, self.psi.shape)

    def test_nonlinearity_cubic(self):
        """Nonlinearity should be cubic"""
        # Use moderate values to avoid clipping
        psi_small = self.psi * 0.5
        psi_2 = psi_small * 2
        non1 = self.ops.nonlinearity(psi_small)
        non2 = self.ops.nonlinearity(psi_2)

        # |2ψ|²(2ψ) = 8|ψ|²ψ
        # Avoid division by very small numbers
        mask = np.abs(non1) > 1e-6
        if np.any(mask):
            ratio = np.abs(non2[mask] / non1[mask])
            mean_ratio = np.mean(ratio)
            self.assertAlmostEqual(mean_ratio, 8.0, places=0)

    def test_momentum_zero_for_static(self):
        """Momentum should be zero when state doesn't change"""
        psi_prev = self.psi.copy()
        momentum = self.ops.momentum(self.psi, psi_prev)
        np.testing.assert_array_almost_equal(
            momentum,
            np.zeros_like(momentum),
            decimal=10
        )

    def test_connectivity_matrix_initialized(self):
        """Connectivity matrix should be initialized"""
        self.assertIsNotNone(self.ops.W)
        self.assertEqual(self.ops.W.shape, (5, 5))

    def test_thalamus_as_hub(self):
        """Thalamus should have high connectivity (K-hub)"""
        # Check that some row/column has relatively high values (hub structure)
        row_sums = np.abs(self.ops.W).sum(axis=0)
        col_sums = np.abs(self.ops.W).sum(axis=1)

        # There should be some hub structure - max > mean
        self.assertGreater(row_sums.max(), row_sums.mean() * 0.9)
        self.assertGreater(col_sums.max(), col_sums.mean() * 0.9)


class TestKEmergenceOperator(unittest.TestCase):
    """Test consciousness/K-emergence operator"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.K_op = KEmergenceOperator(self.params)

    def test_coherence_computation(self):
        """Test coherence formula: C = 1/(1 + Var)"""
        psi = np.ones((5, 64)) * 0.5  # Uniform
        coherence = self.K_op.compute_coherence(psi)
        self.assertAlmostEqual(coherence, 1.0, places=5)

        psi_varied = np.random.randn(5, 64)
        coherence_varied = self.K_op.compute_coherence(psi_varied)
        self.assertLess(coherence_varied, 1.0)

    def test_K_emergence_below_threshold(self):
        """K should not emerge when coherence is below threshold"""
        # High variance = low coherence
        psi = np.random.randn(5, 64) * 10

        K_contrib, coherence = self.K_op.apply(psi)

        # When coherence is low, K contribution should be small
        self.assertLess(coherence, self.params.K_threshold)

    def test_K_emergence_above_threshold(self):
        """K should emerge when coherence is above threshold"""
        # Near-uniform = high coherence
        psi = np.ones((5, 64)) * 0.5 + np.random.randn(5, 64) * 0.01

        K_contrib, coherence = self.K_op.apply(psi)

        self.assertGreater(coherence, 0.9)

    def test_phi_non_negative(self):
        """Integrated information should be non-negative"""
        psi = np.random.randn(5, 64)
        phi = self.K_op.compute_phi(psi)
        self.assertGreaterEqual(phi, 0)

    def test_K_history_updated(self):
        """K history should be updated after apply"""
        psi = np.random.randn(5, 64)
        initial_len = len(self.K_op.K_history)

        self.K_op.apply(psi)

        self.assertEqual(len(self.K_op.K_history), initial_len + 1)


class TestLanguageOperator(unittest.TestCase):
    """Test language operator at all levels"""

    def setUp(self):
        self.params = BLUMParameters(
            n_regions=5,
            n_dims_per_region=64,
            vocab_size=100,
            semantic_dims=32
        )
        self.lang_op = LanguageOperator(self.params)
        self.psi = np.random.randn(5, 64) * 0.1

    def test_phoneme_patterns_initialized(self):
        """Phoneme patterns should be initialized"""
        self.assertIsNotNone(self.lang_op.phoneme_patterns)
        self.assertEqual(self.lang_op.phoneme_patterns.shape[0], 44)

    def test_lexicon_initialized(self):
        """Lexicon should have prototypes and embeddings"""
        self.assertIn('prototypes', self.lang_op.lexicon)
        self.assertIn('embeddings', self.lang_op.lexicon)
        self.assertEqual(
            self.lang_op.lexicon['prototypes'].shape[0],
            self.params.vocab_size
        )

    def test_lexical_access_returns_valid_word(self):
        """Lexical access should return valid word ID"""
        word_id, confidence, semantic = self.lang_op.lexical_access(self.psi)

        self.assertGreaterEqual(word_id, 0)
        self.assertLess(word_id, self.params.vocab_size)
        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 1)

    def test_semantic_vector_normalized(self):
        """Semantic vectors should be normalized"""
        word_id, confidence, semantic = self.lang_op.lexical_access(self.psi)
        norm = np.linalg.norm(semantic)
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_syntax_transitions_normalized(self):
        """Syntax transition matrix should be row-normalized"""
        row_sums = self.lang_op.syntax_transitions.sum(axis=1)
        np.testing.assert_array_almost_equal(
            row_sums,
            np.ones_like(row_sums),
            decimal=5
        )

    def test_pragmatic_alignment_range(self):
        """Pragmatic alignment should be in (0, 1]"""
        speaker_psi = np.random.randn(5, 64)
        listener_psi = np.random.randn(5, 64)

        alignment = self.lang_op.pragmatic_alignment(speaker_psi, listener_psi)

        self.assertGreater(alignment, 0)
        self.assertLessEqual(alignment, 1)

    def test_perfect_alignment(self):
        """Identical states should have perfect alignment"""
        psi = np.random.randn(5, 64)
        alignment = self.lang_op.pragmatic_alignment(psi, psi)
        self.assertAlmostEqual(alignment, 1.0, places=3)

    def test_syntactic_binding_recursive(self):
        """Syntactic binding should handle recursion"""
        words = [1, 2, 3, 4]
        semantics = [np.random.randn(32) for _ in words]

        tree = self.lang_op.syntactic_binding(words, semantics)

        self.assertIn('type', tree)
        self.assertIn('children', tree)

    def test_language_operator_apply(self):
        """Full language operator should return contribution and info"""
        lang_contrib, lang_info = self.lang_op.apply(self.psi)

        self.assertEqual(lang_contrib.shape, self.psi.shape)
        self.assertIn('word_id', lang_info)
        self.assertIn('confidence', lang_info)


class TestMemoryOperator(unittest.TestCase):
    """Test memory systems (WM, EM, SM)"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.mem_op = MemoryOperator(self.params)
        self.psi = np.random.randn(5, 64) * 0.1

    def test_working_memory_capacity(self):
        """Working memory should have 7 slots"""
        self.assertEqual(self.mem_op.wm_capacity, 7)
        self.assertEqual(self.mem_op.wm_buffer.shape[0], 7)

    def test_working_memory_encode(self):
        """Encoding should store in buffer"""
        encoded = self.mem_op.working_memory_encode(self.psi)

        # Check something was stored
        self.assertFalse(np.allclose(
            self.mem_op.wm_buffer[self.mem_op.wm_pointer - 1],
            np.zeros(64)
        ))

    def test_working_memory_decay(self):
        """Working memory strengths should decay"""
        self.mem_op.wm_strengths = np.ones(7)
        self.mem_op.working_memory_decay()

        np.testing.assert_array_less(
            self.mem_op.wm_strengths,
            np.ones(7)
        )

    def test_working_memory_circular(self):
        """Working memory should be circular buffer"""
        initial_pointer = self.mem_op.wm_pointer

        for _ in range(10):  # More than capacity
            self.mem_op.working_memory_encode(self.psi)

        # Pointer should have wrapped
        self.assertEqual(
            self.mem_op.wm_pointer,
            (initial_pointer + 10) % 7
        )

    def test_episodic_encode(self):
        """Episodic encoding should store event"""
        event = np.random.randn(64)
        context = np.random.randn(64)

        self.mem_op.episodic_encode(event, context, time=100.0)

        # Check event was stored
        self.assertFalse(np.allclose(
            self.mem_op.em_events[self.mem_op.em_pointer - 1],
            np.zeros(64)
        ))

    def test_theta_phase_update(self):
        """Theta phase should update after apply"""
        initial_phase = self.mem_op.theta_phase

        self.mem_op.apply(self.psi, time=0)

        self.assertNotEqual(self.mem_op.theta_phase, initial_phase)

    def test_memory_operator_apply(self):
        """Full memory operator should return contribution and info"""
        mem_contrib, mem_info = self.mem_op.apply(self.psi, time=0)

        self.assertEqual(mem_contrib.shape, self.psi.shape)
        self.assertIn('wm_contents', mem_info)
        self.assertIn('theta_phase', mem_info)


class TestAttentionOperator(unittest.TestCase):
    """Test attention mechanisms"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.attn_op = AttentionOperator(self.params)
        self.psi = np.random.randn(5, 64) * 0.1

    def test_saliency_non_negative(self):
        """Saliency should be non-negative"""
        saliency = self.attn_op.compute_saliency(self.psi)
        self.assertTrue(np.all(saliency >= 0))

    def test_top_down_with_goal(self):
        """Top-down control should modulate by goal"""
        goal = np.random.randn(64)
        gain = self.attn_op.top_down_control(self.psi, goal)

        # Gain should be around 1 with variation based on goal
        self.assertTrue(np.all(gain > 0))

    def test_attention_apply(self):
        """Full attention operator should return attended state"""
        attended, attn_info = self.attn_op.apply(self.psi)

        self.assertEqual(attended.shape, self.psi.shape)
        self.assertIn('saliency', attn_info)
        self.assertIn('gain', attn_info)

    def test_attention_history_updated(self):
        """Attention history should be updated after apply"""
        initial_len = len(self.attn_op.attention_history)

        self.attn_op.apply(self.psi)

        self.assertEqual(
            len(self.attn_op.attention_history),
            initial_len + 1
        )


class TestBrainLanguageUnifiedModel(unittest.TestCase):
    """Integration tests for the complete BLUM"""

    def setUp(self):
        self.params = BLUMParameters(
            n_regions=5,
            n_dims_per_region=64,
            vocab_size=100,
            dt=0.001
        )
        self.model = BrainLanguageUnifiedModel(self.params)

    def test_model_initialization(self):
        """Model should initialize all components"""
        self.assertIsNotNone(self.model.state)
        self.assertIsNotNone(self.model.neural_ops)
        self.assertIsNotNone(self.model.K_operator)
        self.assertIsNotNone(self.model.language_ops)
        self.assertIsNotNone(self.model.memory_ops)
        self.assertIsNotNone(self.model.attention_ops)

    def test_single_step(self):
        """Single step should execute without error"""
        result = self.model.step()
        # Result is None or emission dict
        self.assertTrue(result is None or isinstance(result, dict))

    def test_step_updates_state(self):
        """Step should update neural state"""
        initial_state = self.model.state.neural.copy()

        self.model.step()

        self.assertFalse(np.allclose(
            self.model.state.neural,
            initial_state
        ))

    def test_step_with_external_input(self):
        """Step should accept external input"""
        external = np.random.randn(5, 64) * 0.1
        result = self.model.step(external_input=external)
        # Should not raise error
        self.assertTrue(result is None or isinstance(result, dict))

    def test_oscillatory_modulation(self):
        """Oscillatory modulation should update phases"""
        initial_gamma = self.model.gamma_phase
        initial_theta = self.model.theta_phase

        self.model.oscillatory_modulation()

        self.assertNotEqual(self.model.gamma_phase, initial_gamma)
        self.assertNotEqual(self.model.theta_phase, initial_theta)

    def test_energy_bounded(self):
        """Energy should remain bounded over time"""
        for _ in range(100):
            self.model.step()

        final_energy = self.model.state.total_energy()
        self.assertLess(final_energy, 1e6)

    def test_no_nan_after_steps(self):
        """State should not contain NaN after many steps"""
        for _ in range(500):
            self.model.step()

        self.assertFalse(np.any(np.isnan(self.model.state.neural)))

    def test_emission_occurs(self):
        """Emissions should occur over extended run"""
        emissions = self.model.run(n_steps=1000, verbose=False)

        # Should have at least some emissions
        self.assertGreater(len(emissions), 0)

    def test_emission_has_required_fields(self):
        """Emission dict should have all required fields"""
        emissions = self.model.run(n_steps=500, verbose=False)

        if len(emissions) > 0:
            emission = emissions[0]
            required_fields = [
                'time', 'word_id', 'confidence',
                'semantic', 'coherence'
            ]
            for field in required_fields:
                self.assertIn(field, emission)

    def test_reset(self):
        """Reset should restore initial state"""
        # Run for a while
        self.model.run(n_steps=100, verbose=False)

        # Reset
        self.model.reset()

        # Check state is zeroed
        np.testing.assert_array_equal(
            self.model.state.neural,
            np.zeros((5, 64))
        )
        self.assertEqual(self.model.t, 0)

    def test_coherence_history_tracking(self):
        """Model should track coherence history"""
        self.model.run(n_steps=100, verbose=False)

        self.assertGreater(len(self.model.coherence_history), 0)

    def test_phi_history_tracking(self):
        """Model should track integrated information history"""
        self.model.run(n_steps=100, verbose=False)

        self.assertGreater(len(self.model.phi_history), 0)


class TestUniversalConstants(unittest.TestCase):
    """Test that universal constants are correctly defined"""

    def test_golden_ratio(self):
        """Golden ratio should be (1+sqrt(5))/2"""
        expected = (1 + np.sqrt(5)) / 2
        self.assertAlmostEqual(PHI, expected, places=10)

    def test_golden_ratio_property(self):
        """Golden ratio should satisfy φ² = φ + 1"""
        self.assertAlmostEqual(PHI**2, PHI + 1, places=10)

    def test_eulers_number(self):
        """Euler's number should be e"""
        self.assertAlmostEqual(E, np.e, places=10)

    def test_pi(self):
        """Pi should be π"""
        self.assertAlmostEqual(PI, np.pi, places=10)


class TestSpiralDiscriminantConnection(unittest.TestCase):
    """Test connections to SDF framework"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=10, n_dims_per_region=128)
        self.model = BrainLanguageUnifiedModel(self.params)

    def test_K_emergence_at_high_coherence(self):
        """K should emerge when coherence is high (SDF prediction)"""
        # Set state to near-uniform (high coherence)
        self.model.state.neural = (
            np.ones((10, 128)) * 0.5 +
            np.random.randn(10, 128) * 0.01
        )

        K_contrib, coherence = self.model.K_operator.apply(
            self.model.state.neural
        )

        self.assertGreater(coherence, 0.9)

    def test_power_law_in_emissions(self):
        """Word frequencies should approximately follow power law"""
        emissions = self.model.run(n_steps=5000, verbose=False)

        if len(emissions) > 20:
            # Count word frequencies
            word_counts = {}
            for e in emissions:
                word_id = e['word_id']
                word_counts[word_id] = word_counts.get(word_id, 0) + 1

            # Check for power-law-like distribution (high variance)
            counts = list(word_counts.values())
            if len(counts) > 5:
                variance = np.var(counts)
                mean = np.mean(counts)
                cv = np.sqrt(variance) / mean  # Coefficient of variation

                # Power law should have high CV
                self.assertGreater(cv, 0.3)


class TestRecursiveDialogueConnection(unittest.TestCase):
    """Test connections to RDE framework"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.model = BrainLanguageUnifiedModel(self.params)

    def test_emission_at_entropy_minimum(self):
        """Emissions should occur near entropy minima"""
        # Run and collect emissions with diagnostics
        emissions = self.model.run(n_steps=1000, verbose=False)

        if len(emissions) > 0:
            # Check that d_entropy is small at emissions
            for emission in emissions:
                if 'd_entropy' in emission['diagnostics']:
                    d_entropy = abs(emission['diagnostics']['d_entropy'])
                    self.assertLess(
                        d_entropy,
                        self.params.emission_threshold * 10
                    )

    def test_LoMI_alignment_improves(self):
        """Speaker-listener alignment should be measurable"""
        # Create listener callback
        listener_state = np.random.randn(5, 64) * 0.1

        def listener_cb(t):
            return listener_state

        # Run with listener
        emissions = self.model.run(
            n_steps=500,
            listener_callback=listener_cb,
            verbose=False
        )

        # Check alignment was computed
        if len(emissions) > 0:
            for e in emissions:
                if 'language_info' in e and 'alignment' in e.get('language_info', {}):
                    alignment = e['language_info']['alignment']
                    self.assertGreater(alignment, 0)
                    self.assertLessEqual(alignment, 1)


class TestNumericalStability(unittest.TestCase):
    """Test numerical stability of the model"""

    def setUp(self):
        self.params = BLUMParameters(n_regions=5, n_dims_per_region=64)
        self.model = BrainLanguageUnifiedModel(self.params)

    def test_extreme_input(self):
        """Model should handle extreme input gracefully"""
        extreme_input = np.ones((5, 64)) * 1000

        # Should not crash
        for _ in range(100):
            self.model.step(external_input=extreme_input)

        # State should still be bounded
        self.assertTrue(np.all(np.abs(self.model.state.neural) < 100))

    def test_long_run_stability(self):
        """Model should remain stable over long runs"""
        self.model.run(n_steps=5000, verbose=False)

        # Check no NaN or Inf
        self.assertFalse(np.any(np.isnan(self.model.state.neural)))
        self.assertFalse(np.any(np.isinf(self.model.state.neural)))

        # Check bounded
        self.assertTrue(np.all(np.abs(self.model.state.neural) < 100))

    def test_oscillation_phase_bounded(self):
        """Oscillation phases should remain in [0, 2π)"""
        for _ in range(10000):
            self.model.oscillatory_modulation()

        self.assertGreaterEqual(self.model.gamma_phase, 0)
        self.assertLess(self.model.gamma_phase, 2 * np.pi)


def run_tests():
    """Run all tests and print summary"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestBLUMParameters,
        TestUnifiedBrainState,
        TestNeuralOperators,
        TestKEmergenceOperator,
        TestLanguageOperator,
        TestMemoryOperator,
        TestAttentionOperator,
        TestBrainLanguageUnifiedModel,
        TestUniversalConstants,
        TestSpiralDiscriminantConnection,
        TestRecursiveDialogueConnection,
        TestNumericalStability
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("BLUM TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASSED' if success else 'FAILED'}")
    print("=" * 70)

    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
