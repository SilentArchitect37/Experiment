#!/usr/bin/env python3
"""
Quickstart: Recursive Dialogue Engine

This is the simplest way to get started with the Recursive Dialogue Engine.
Run with: python quickstart.py
"""

import numpy as np
from dialogue_system import (
    RecursiveDialogueEngine, DialogueConfig,
    create_oscillating_listener, create_pulse_listener
)
from recursive_engine import RecursiveParams
from emission_detector import EmissionConfig


def example_1_basic():
    """Example 1: Basic dialogue with default settings"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Recursive Dialogue")
    print("=" * 70)
    print()

    # Create engine with default configuration
    engine = RecursiveDialogueEngine()

    # Run for 500 steps
    print("Running dialogue for 500 steps...\n")
    emissions = engine.converse(n_steps=500, verbose=True)

    print(f"\nGenerated {len(emissions)} emissions")
    print()


def example_2_with_listener():
    """Example 2: Dialogue with oscillating listener (simulates interaction)"""
    print("=" * 70)
    print("EXAMPLE 2: Dialogue with Oscillating Listener")
    print("=" * 70)
    print()

    # Configure system
    config = DialogueConfig(
        state_dims=256,
        vocab_size=50,
        engine_optimization='fft'
    )

    # Adjust dynamics for more interesting behavior
    config.engine_params.g = 0.15      # Diffusion
    config.engine_params.lam = 0.4     # Nonlinearity
    config.engine_params.rho = 0.35    # Momentum

    # Adjust emission rate
    config.emission_config.cooldown_steps = 20

    # Create engine
    engine = RecursiveDialogueEngine(config)

    # Create listener that provides rhythmic feedback
    listener = create_oscillating_listener(
        frequency=0.04,    # Oscillation frequency
        amplitude=0.5,     # Signal strength
        dims=256
    )

    # Run dialogue
    print("Running dialogue with oscillating listener...\n")
    emissions = engine.converse(
        n_steps=1000,
        listener_callback=listener,
        verbose=True
    )

    # Analyze results
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    if len(emissions) > 1:
        times = [e['time'] for e in emissions]
        intervals = np.diff(times)
        tokens = [e['token'] for e in emissions]
        coherences = [e['coherence'] for e in emissions]

        print(f"Total emissions:     {len(emissions)}")
        print(f"Unique tokens:       {len(set(tokens))}")
        print(f"Emission rate:       {len(emissions)/1000:.3f} per step")
        print(f"Mean interval:       {np.mean(intervals):.1f} steps")
        print(f"Interval variance:   {np.std(intervals):.1f} steps")
        print(f"Mean coherence:      {np.mean(coherences):.4f}")
        print(f"Coherence range:     [{np.min(coherences):.4f}, {np.max(coherences):.4f}]")

        # Show token sequence
        print(f"\nFirst 30 tokens: {tokens[:30]}")

    print()


def example_3_pulse_dialogue():
    """Example 3: Turn-taking dialogue with pulse listener"""
    print("=" * 70)
    print("EXAMPLE 3: Turn-Taking Dialogue (Pulse Listener)")
    print("=" * 70)
    print()

    # Configure for more responsive turn-taking
    config = DialogueConfig(
        state_dims=128,
        vocab_size=30,
        engine_optimization='fft',
        use_coherence_detector=True  # Use LoMI-based emission
    )

    config.engine_params.g = 0.2
    config.engine_params.lam = 0.3
    config.engine_params.rho = 0.5
    config.emission_config.cooldown_steps = 10

    # Create engine
    engine = RecursiveDialogueEngine(config)

    # Create pulse listener (simulates turn-taking)
    listener = create_pulse_listener(
        pulse_interval=40,     # Strong input every 40 steps
        pulse_strength=2.0,    # Pulse amplitude
        dims=128
    )

    # Run dialogue
    print("Running turn-taking dialogue...\n")
    emissions = engine.converse(
        n_steps=800,
        listener_callback=listener,
        verbose=True
    )

    print(f"\nGenerated {len(emissions)} emissions with turn-taking pattern")
    print()


def example_4_custom_parameters():
    """Example 4: Custom parameters for different dynamics"""
    print("=" * 70)
    print("EXAMPLE 4: Custom Parameter Exploration")
    print("=" * 70)
    print()

    # Test different parameter configurations
    configs = {
        "High Diffusion (smooth)": {
            'g': 0.3, 'lam': 0.2, 'rho': 0.3
        },
        "High Nonlinearity (chaotic)": {
            'g': 0.1, 'lam': 0.8, 'rho': 0.2
        },
        "High Momentum (persistent)": {
            'g': 0.15, 'lam': 0.3, 'rho': 0.7
        }
    }

    for name, params in configs.items():
        print(f"\nTesting: {name}")
        print(f"  g={params['g']}, λ={params['lam']}, ρ={params['rho']}")

        # Create config
        config = DialogueConfig(
            state_dims=128,
            vocab_size=40,
            engine_optimization='fft'
        )
        config.engine_params.g = params['g']
        config.engine_params.lam = params['lam']
        config.engine_params.rho = params['rho']
        config.emission_config.cooldown_steps = 15

        # Create and run engine
        engine = RecursiveDialogueEngine(config)
        listener = create_oscillating_listener(frequency=0.03, amplitude=0.3, dims=128)

        emissions = engine.converse(
            n_steps=500,
            listener_callback=listener,
            verbose=False
        )

        # Summary
        if len(emissions) > 1:
            intervals = np.diff([e['time'] for e in emissions])
            tokens = [e['token'] for e in emissions]

            print(f"  Emissions: {len(emissions)}")
            print(f"  Unique tokens: {len(set(tokens))}")
            print(f"  Mean interval: {np.mean(intervals):.1f} ± {np.std(intervals):.1f}")

    print()


def main():
    """Run all examples"""
    examples = [
        ("1", "Basic dialogue", example_1_basic),
        ("2", "Dialogue with listener", example_2_with_listener),
        ("3", "Turn-taking dialogue", example_3_pulse_dialogue),
        ("4", "Custom parameters", example_4_custom_parameters),
    ]

    print("\n" + "=" * 70)
    print("RECURSIVE DIALOGUE ENGINE - QUICKSTART")
    print("=" * 70)
    print("\nAvailable examples:")
    for num, desc, _ in examples:
        print(f"  {num}. {desc}")
    print("  all - Run all examples")
    print()

    choice = input("Select example (1-4, or 'all'): ").strip()

    if choice == 'all':
        for _, _, func in examples:
            func()
            print("\n")
    elif choice in ['1', '2', '3', '4']:
        idx = int(choice) - 1
        examples[idx][2]()
    else:
        print("Invalid choice. Running Example 2 (most interesting)...")
        example_2_with_listener()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
