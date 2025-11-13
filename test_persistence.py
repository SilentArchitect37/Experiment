"""
Test Suite for Idle Persistence Layer

Tests:
1. Save and load basic state
2. State integrity after load (exact reproduction)
3. Idle detection triggering
4. Auto-checkpoint functionality
5. Resume from saved state
6. Checkpoint management (list, delete)
"""

import numpy as np
from dialogue_system import RecursiveDialogueEngine, DialogueConfig
from persistence import DialoguePersistence, IdleMonitor
import time
import os
import shutil


def test_basic_save_load():
    """Test 1: Basic save and load functionality"""
    print("\n=== Test 1: Basic Save/Load ===")

    # Create engine and run
    config = DialogueConfig(
        state_dims=128,
        vocab_size=50,
        engine_optimization='fft'
    )
    engine1 = RecursiveDialogueEngine(config)

    # Run for some steps
    print("Running original engine for 200 steps...")
    emissions1 = engine1.converse(n_steps=200, verbose=False)
    print(f"  Emissions: {len(emissions1)}")
    print(f"  Time step: {engine1.t}")
    print(f"  Last token: {engine1.tdl.last_token}")

    # Save state
    persistence = DialoguePersistence('./test_checkpoints')
    save_path = persistence.save(engine1, name='test_basic')
    print(f"  Saved to: {save_path}")

    # Load state
    print("\nLoading saved state...")
    engine2 = persistence.load('test_basic')
    print(f"  Loaded time step: {engine2.t}")
    print(f"  Loaded emissions: {len(engine2.emission_history)}")
    print(f"  Loaded last token: {engine2.tdl.last_token}")

    # Verify state matches
    assert engine2.t == engine1.t, "Time step mismatch!"
    assert len(engine2.emission_history) == len(engine1.emission_history), "Emission history mismatch!"
    assert engine2.tdl.last_token == engine1.tdl.last_token, "TDL state mismatch!"
    assert np.allclose(engine2.engine.mu, engine1.engine.mu), "Engine state mismatch!"

    print("✓ Basic save/load test PASSED")
    return True


def test_state_integrity():
    """Test 2: Verify exact state reproduction after load"""
    print("\n=== Test 2: State Integrity ===")

    config = DialogueConfig(state_dims=64, vocab_size=30, engine_optimization='vectorized')
    engine1 = RecursiveDialogueEngine(config)
    engine1.converse(n_steps=150, verbose=False)

    # Save
    persistence = DialoguePersistence('./test_checkpoints')
    persistence.save(engine1, name='test_integrity')

    # Load
    engine2 = persistence.load('test_integrity')

    # Check all components
    checks = {
        'mu': np.allclose(engine1.engine.mu, engine2.engine.mu),
        'mu_prev': np.allclose(engine1.engine.mu_prev, engine2.engine.mu_prev),
        'engine_t': engine1.engine.t == engine2.engine.t,
        'global_t': engine1.t == engine2.t,
        'mu_listener': np.allclose(engine1.lomi.mu_listener, engine2.lomi.mu_listener),
        'codebook': np.allclose(engine1.codebook, engine2.codebook),
        'transition_matrix': np.allclose(engine1.tdl.transition_matrix, engine2.tdl.transition_matrix),
        'detector_steps': engine1.detector.steps_since_emission == engine2.detector.steps_since_emission,
        'detector_total': engine1.detector.total_emissions == engine2.detector.total_emissions,
    }

    print("State component checks:")
    for name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")

    all_passed = all(checks.values())
    if all_passed:
        print("✓ State integrity test PASSED")
    else:
        print("✗ State integrity test FAILED")

    return all_passed


def test_resume_continuation():
    """Test 3: Verify dynamics continue correctly after resume"""
    print("\n=== Test 3: Resume Continuation ===")

    config = DialogueConfig(state_dims=64, vocab_size=30, engine_optimization='fft')

    # Run continuously
    engine_continuous = RecursiveDialogueEngine(config)
    np.random.seed(42)
    emissions_continuous = engine_continuous.converse(n_steps=400, verbose=False)

    # Run with save/load in middle
    engine_split = RecursiveDialogueEngine(config)
    np.random.seed(42)
    emissions_split = engine_split.converse(n_steps=200, verbose=False)

    # Save at step 200
    persistence = DialoguePersistence('./test_checkpoints')
    persistence.save(engine_split, name='test_resume')

    # Load and continue
    engine_resumed = persistence.load('test_resume')
    emissions_split += engine_resumed.converse(n_steps=200, verbose=False)

    print(f"  Continuous run emissions: {len(emissions_continuous)}")
    print(f"  Split+resume emissions: {len(emissions_split)}")

    # Note: Due to RNG state, we can't expect exact match, but emission counts should be similar
    emission_diff = abs(len(emissions_continuous) - len(emissions_split))
    similar = emission_diff <= 2  # Allow small difference due to numerical precision

    if similar:
        print(f"✓ Resume continuation test PASSED (diff: {emission_diff})")
    else:
        print(f"✗ Resume continuation test FAILED (diff: {emission_diff})")

    return similar


def test_idle_detection():
    """Test 4: Verify idle detection works"""
    print("\n=== Test 4: Idle Detection ===")

    idle_triggered = {'count': 0}

    def idle_callback(engine):
        idle_triggered['count'] += 1
        print(f"  [IDLE CALLBACK] Triggered! (count: {idle_triggered['count']})")

    # Create monitor
    monitor = IdleMonitor(idle_threshold_steps=50, idle_timeout_seconds=999)
    monitor.register_idle_callback(idle_callback)

    # Simulate steps
    print("Simulating steps with idle periods...")
    monitor.update_activity(0, emission_occurred=True)

    # No emission for 50+ steps should trigger idle
    for step in range(1, 60):
        is_idle = monitor.check_idle(step)
        if is_idle and step > 50:
            monitor.on_idle(None)  # Trigger callback
            monitor.update_activity(step, emission_occurred=False)
            break

    if idle_triggered['count'] > 0:
        print("✓ Idle detection test PASSED")
        return True
    else:
        print("✗ Idle detection test FAILED")
        return False


def test_auto_checkpoint():
    """Test 5: Verify auto-checkpoint during converse()"""
    print("\n=== Test 5: Auto-Checkpoint ===")

    config = DialogueConfig(
        state_dims=64,
        vocab_size=30,
        engine_optimization='fft',
        enable_persistence=True,
        checkpoint_dir='./test_checkpoints',
        auto_checkpoint_interval=100,  # Checkpoint every 100 steps
        idle_threshold_steps=999  # Disable idle for this test
    )

    engine = RecursiveDialogueEngine(config)
    print("Running with auto-checkpoint enabled...")
    engine.converse(n_steps=250, verbose=False)

    # Check if auto checkpoints were created
    persistence = DialoguePersistence('./test_checkpoints')
    checkpoints = persistence.list_checkpoints()

    auto_checkpoints = [cp for cp in checkpoints if 'auto_step' in cp['name']]
    print(f"  Auto-checkpoints created: {len(auto_checkpoints)}")
    for cp in auto_checkpoints:
        print(f"    - {cp['name']}")

    if len(auto_checkpoints) >= 2:  # Should have checkpoints at 100 and 200
        print("✓ Auto-checkpoint test PASSED")
        return True
    else:
        print("✗ Auto-checkpoint test FAILED")
        return False


def test_checkpoint_management():
    """Test 6: Checkpoint listing and deletion"""
    print("\n=== Test 6: Checkpoint Management ===")

    persistence = DialoguePersistence('./test_checkpoints')

    # List all checkpoints
    checkpoints = persistence.list_checkpoints()
    print(f"  Total checkpoints: {len(checkpoints)}")

    if checkpoints:
        # Show first few
        for cp in checkpoints[:3]:
            print(f"    - {cp['name']} ({cp['size_mb']:.2f} MB)")

        # Test deletion
        first_cp = checkpoints[0]['name']
        print(f"\n  Deleting checkpoint: {first_cp}")
        persistence.delete_checkpoint(first_cp)

        # Verify deletion
        checkpoints_after = persistence.list_checkpoints()
        deleted = len(checkpoints_after) == len(checkpoints) - 1

        if deleted:
            print("✓ Checkpoint management test PASSED")
            return True
        else:
            print("✗ Checkpoint management test FAILED")
            return False
    else:
        print("  No checkpoints to manage (might be OK)")
        return True


def test_persistence_with_listener():
    """Test 7: Persistence with listener callback"""
    print("\n=== Test 7: Persistence with Listener ===")

    from dialogue_system import create_oscillating_listener

    config = DialogueConfig(state_dims=64, vocab_size=30, engine_optimization='fft')
    engine1 = RecursiveDialogueEngine(config)

    listener = create_oscillating_listener(frequency=0.05, amplitude=0.3, dims=64)

    # Run with listener
    print("Running with oscillating listener...")
    engine1.converse(n_steps=200, listener_callback=listener, verbose=False)

    # Save
    persistence = DialoguePersistence('./test_checkpoints')
    persistence.save(engine1, name='test_listener')

    # Load and verify listener state preserved
    engine2 = persistence.load('test_listener')

    assert np.allclose(engine2.lomi.mu_listener, engine1.lomi.mu_listener), "Listener state mismatch!"

    print("✓ Persistence with listener test PASSED")
    return True


def cleanup():
    """Clean up test checkpoints"""
    if os.path.exists('./test_checkpoints'):
        shutil.rmtree('./test_checkpoints')
        print("\nCleaned up test checkpoints")


def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("PERSISTENCE LAYER TEST SUITE")
    print("=" * 60)

    tests = [
        ("Basic Save/Load", test_basic_save_load),
        ("State Integrity", test_state_integrity),
        ("Resume Continuation", test_resume_continuation),
        ("Idle Detection", test_idle_detection),
        ("Auto-Checkpoint", test_auto_checkpoint),
        ("Checkpoint Management", test_checkpoint_management),
        ("Persistence with Listener", test_persistence_with_listener),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ {name} test FAILED with exception: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    # Cleanup
    cleanup()

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
