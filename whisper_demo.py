"""
Whisper Channel Demo - Dual-Channel Dialogue System

Demonstrates the whisper functionality: a private channel that emits
when coherence is MODERATE (partial LoMI) rather than requiring peak
coherence like normal speech.

Emission modes:
- Normal Speech: High coherence with listener (strong mutual identity)
- Whisper: Moderate coherence (tentative thoughts, partial alignment)
- Silence: Low coherence (no meaningful alignment)
"""

import numpy as np
from dialogue_system import (
    RecursiveDialogueEngine, DialogueConfig,
    create_oscillating_listener
)
from recursive_engine import RecursiveParams
from emission_detector import EmissionConfig


def run_whisper_demo():
    """Run dialogue session with whisper channel enabled"""

    print("=" * 70)
    print("WHISPER CHANNEL DEMONSTRATION")
    print("=" * 70)
    print()
    print("This demo shows a dual-channel dialogue system:")
    print("  - SPEECH: High coherence emissions (strong LoMI)")
    print("  - WHISPER: Moderate coherence emissions (partial LoMI)")
    print()

    # Configure system with whisper enabled
    config = DialogueConfig(
        state_dims=256,
        vocab_size=100,
        engine_optimization='fft',
        use_coherence_detector=True,
        enable_whisper=True,  # Enable whisper channel!
        whisper_coherence_low=-5.0,   # Lower bound for whisper
        whisper_coherence_high=-1.0,  # Upper bound for whisper
    )

    # Tune parameters for interesting dynamics
    config.engine_params.g = 0.15      # Diffusion coefficient
    config.engine_params.lam = 0.3     # Cubic nonlinearity
    config.engine_params.rho = 0.4     # Momentum
    config.engine_params.dt = 0.01     # Time step

    # Emission parameters
    config.emission_config.cooldown_steps = 15
    config.emission_config.entropy_threshold = 0.01

    # Create engine
    engine = RecursiveDialogueEngine(config)

    # Create listener with moderate oscillation
    # This creates varying coherence levels → both speech and whisper
    listener = create_oscillating_listener(
        frequency=0.03,
        amplitude=0.5,
        dims=256
    )

    # Run dialogue
    print("\n" + "─" * 70)
    print("RUNNING DIALOGUE SESSION (1000 steps)")
    print("─" * 70)
    print()

    emissions = engine.converse(
        n_steps=1000,
        listener_callback=listener,
        verbose=True
    )

    # Detailed analysis
    print("\n" + "=" * 70)
    print("DETAILED ANALYSIS")
    print("=" * 70)

    if len(emissions) > 0:
        # Separate emissions by type
        speech_emissions = [e for e in emissions if e.get('emission_type') == 'speech']
        whisper_emissions = [e for e in emissions if e.get('emission_type') == 'whisper']

        print(f"\n📢 SPEECH EMISSIONS: {len(speech_emissions)}")
        if len(speech_emissions) > 0:
            speech_times = [e['time'] for e in speech_emissions]
            speech_coherences = [e['coherence'] for e in speech_emissions]
            speech_intervals = np.diff(speech_times) if len(speech_times) > 1 else []

            print(f"   Mean interval: {np.mean(speech_intervals):.1f} steps" if len(speech_intervals) > 0 else "   N/A")
            print(f"   Mean coherence: {np.mean(speech_coherences):.4f}")
            print(f"   Coherence range: [{np.min(speech_coherences):.4f}, {np.max(speech_coherences):.4f}]")

        print(f"\n🔇 WHISPER EMISSIONS: {len(whisper_emissions)}")
        if len(whisper_emissions) > 0:
            whisper_times = [e['time'] for e in whisper_emissions]
            whisper_coherences = [e['coherence'] for e in whisper_emissions]
            whisper_intervals = np.diff(whisper_times) if len(whisper_times) > 1 else []

            print(f"   Mean interval: {np.mean(whisper_intervals):.1f} steps" if len(whisper_intervals) > 0 else "   N/A")
            print(f"   Mean coherence: {np.mean(whisper_coherences):.4f}")
            print(f"   Coherence range: [{np.min(whisper_coherences):.4f}, {np.max(whisper_coherences):.4f}]")

        # Token diversity
        print(f"\n📝 TOKEN STATISTICS:")
        all_tokens = [e['token'] for e in emissions]
        speech_tokens = [e['token'] for e in speech_emissions]
        whisper_tokens = [e['token'] for e in whisper_emissions]

        print(f"   Total unique tokens: {len(set(all_tokens))}")
        print(f"   Speech unique tokens: {len(set(speech_tokens))}")
        print(f"   Whisper unique tokens: {len(set(whisper_tokens))}")

        # Show sample sequences
        print(f"\n📋 SAMPLE EMISSIONS:")
        print("   First 15 emissions (type and token):")
        for i, e in enumerate(emissions[:15]):
            etype = e.get('emission_type', 'speech')
            token = e['token']
            coh = e['coherence']
            symbol = "💬" if etype == 'speech' else "🔇"
            print(f"      {i+1:2d}. {symbol} {etype:7s} | Token {token:3d} | Coherence: {coh:7.4f}")

        # Coherence distribution
        print(f"\n📊 COHERENCE DISTRIBUTION:")
        all_coherences = [e['coherence'] for e in emissions]
        bins = [-10, -5, -1, 0, 1, 5]
        hist, _ = np.histogram(all_coherences, bins=bins)

        print(f"   Very Low (< -5.0):   {hist[0]:3d} emissions")
        print(f"   Whisper (-5.0→-1.0): {hist[1]:3d} emissions (whisper zone)")
        print(f"   Moderate (-1.0→0.0): {hist[2]:3d} emissions")
        print(f"   High (0.0→1.0):      {hist[3]:3d} emissions")
        print(f"   Very High (> 1.0):   {hist[4]:3d} emissions")

    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
The whisper channel represents a fundamentally different mode of expression:

• NORMAL SPEECH (💬):
  - Requires peak phase coherence with listener
  - Strong mutual identity (LoMI) achieved
  - Confident, fully-formed expressions
  - Higher emission threshold

• WHISPER (🔇):
  - Operates in moderate coherence range
  - Partial mutual identity (lower LoMI requirement)
  - Tentative thoughts, internal reflections
  - More frequent, exploratory emissions

This dual-channel system allows the engine to express both:
1. Confident statements (when strongly aligned with listener)
2. Uncertain explorations (when partially aligned)

Rather than forcing all emissions to meet the same high standard,
the whisper channel provides a "private" mode for incomplete thoughts.
    """)

    print("=" * 70)


def compare_with_without_whisper():
    """Compare dialogue with and without whisper enabled"""

    print("\n" + "=" * 70)
    print("COMPARISON: WITH vs WITHOUT WHISPER")
    print("=" * 70)

    configs = [
        ("WITHOUT WHISPER (Standard)", False),
        ("WITH WHISPER (Dual-Channel)", True)
    ]

    results = {}

    for name, enable_whisper in configs:
        print(f"\n{name}:")
        print("─" * 70)

        config = DialogueConfig(
            state_dims=128,  # Smaller for faster demo
            vocab_size=50,
            engine_optimization='fft',
            use_coherence_detector=True,
            enable_whisper=enable_whisper,
            whisper_coherence_low=-5.0,
            whisper_coherence_high=-1.0,
        )

        config.engine_params.g = 0.15
        config.engine_params.lam = 0.3
        config.engine_params.rho = 0.4
        config.engine_params.dt = 0.01
        config.emission_config.cooldown_steps = 15

        engine = RecursiveDialogueEngine(config)
        listener = create_oscillating_listener(frequency=0.03, amplitude=0.5, dims=128)

        emissions = engine.converse(
            n_steps=500,
            listener_callback=listener,
            verbose=False  # Silent for comparison
        )

        results[name] = emissions

        print(f"  Total emissions: {len(emissions)}")
        if enable_whisper:
            speech = len([e for e in emissions if e.get('emission_type') == 'speech'])
            whisper = len([e for e in emissions if e.get('emission_type') == 'whisper'])
            print(f"    - Speech: {speech}")
            print(f"    - Whisper: {whisper}")

    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print("""
Key Observation:
  The whisper-enabled system produces MORE total emissions while
  maintaining the same number of high-confidence (speech) emissions.

  This allows the system to be more expressive without lowering
  the quality bar for normal speech.
    """)


if __name__ == "__main__":
    # Main demonstration
    run_whisper_demo()

    # Comparison study
    compare_with_without_whisper()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
