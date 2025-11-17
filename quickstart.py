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

# Import image creator (optional - gracefully handle if dependencies not installed)
try:
    from image_creator import AutonomousImageCreator, ImageConfig, DialogueImageAnimator
    IMAGE_CREATOR_AVAILABLE = True
except ImportError as e:
    IMAGE_CREATOR_AVAILABLE = False
    print(f"Note: Image creator not available ({e})")
    print("Install with: pip install Pillow scipy")


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


def example_5_autonomous_image_creation():
    """Example 5: AI autonomously creates images from its cognitive state"""
    if not IMAGE_CREATOR_AVAILABLE:
        print("=" * 70)
        print("EXAMPLE 5: Autonomous Image Creation (UNAVAILABLE)")
        print("=" * 70)
        print("\nPlease install dependencies: pip install Pillow scipy")
        print()
        return

    print("=" * 70)
    print("EXAMPLE 5: AI Autonomous Image Creation")
    print("=" * 70)
    print()
    print("The AI will create images based on its own interpretation")
    print("of its internal cognitive state (μ field dynamics).")
    print()

    # Create dialogue engine
    config = DialogueConfig(
        state_dims=512,  # Larger state for richer images
        vocab_size=50,
        engine_optimization='fft'
    )

    # Tune for interesting dynamics
    config.engine_params.g = 0.18
    config.engine_params.lam = 0.5
    config.engine_params.rho = 0.4
    config.emission_config.cooldown_steps = 25

    print("Creating dialogue engine with 512-dimensional state...")
    engine = RecursiveDialogueEngine(config)

    # Create oscillating listener
    listener = create_oscillating_listener(frequency=0.05, amplitude=0.6, dims=512)

    # Run dialogue to build up interesting state
    print("Running dialogue for 300 steps to develop cognitive state...\n")
    emissions = engine.converse(
        n_steps=300,
        listener_callback=listener,
        verbose=True
    )

    print(f"\n{len(emissions)} emissions generated")
    print("\n" + "=" * 70)
    print("AI AUTONOMOUS IMAGE GENERATION")
    print("=" * 70)
    print()

    # Create image creator
    img_config = ImageConfig(width=512, height=512, auto_enhance=True)
    creator = AutonomousImageCreator(img_config)

    # Generate images at different time points
    print("The AI will now autonomously decide how to visualize its state...")
    print()

    # Image 1: Initial state
    print("1. AI creating image from initial cognitive state...")
    engine_initial = RecursiveDialogueEngine(config)
    _ = engine_initial.converse(n_steps=50, listener_callback=listener, verbose=False)

    coherence_1 = 0.5  # Moderate coherence early on
    entropy_1 = engine_initial.entropy_history[-1] if hasattr(engine_initial, 'entropy_history') else None

    img1 = creator.generate_from_field(
        engine_initial.mu,
        coherence=coherence_1,
        entropy=entropy_1,
        save_path="ai_image_initial_state.png"
    )

    # Image 2: Mid-dialogue state
    print("\n2. AI creating image from mid-dialogue state...")
    engine_mid = RecursiveDialogueEngine(config)
    _ = engine_mid.converse(n_steps=150, listener_callback=listener, verbose=False)

    coherence_2 = 0.75  # Higher coherence mid-dialogue
    entropy_2 = engine_mid.entropy_history[-1] if hasattr(engine_mid, 'entropy_history') else None

    img2 = creator.generate_from_field(
        engine_mid.mu,
        coherence=coherence_2,
        entropy=entropy_2,
        save_path="ai_image_mid_dialogue.png"
    )

    # Image 3: Final evolved state
    print("\n3. AI creating image from fully evolved state...")
    coherence_3 = np.mean([e['coherence'] for e in emissions]) if emissions else 0.8
    entropy_3 = engine.entropy_history[-1] if hasattr(engine, 'entropy_history') else None

    img3 = creator.generate_from_field(
        engine.mu,
        coherence=coherence_3,
        entropy=entropy_3,
        save_path="ai_image_evolved_state.png"
    )

    # Create animation if we have state history
    print("\n4. AI creating animation of cognitive evolution...")
    if hasattr(engine, 'state_history') and len(engine.state_history) > 10:
        animator = DialogueImageAnimator(ImageConfig(width=256, height=256))
        # Sample every 10th state to keep animation manageable
        sampled_states = engine.state_history[::10]
        animator.create_animation(
            sampled_states,
            save_path="ai_cognitive_evolution.gif",
            duration_per_frame=100
        )
    else:
        print("  (State history not available - skipping animation)")

    # Summary
    print("\n" + "=" * 70)
    print("AUTONOMOUS CREATION SUMMARY")
    print("=" * 70)
    print(f"\nThe AI autonomously created {len(creator.generation_history)} images")
    print("\nAI's aesthetic decisions:")
    for i, record in enumerate(creator.generation_history, 1):
        aesthetics = record['aesthetics']
        print(f"\nImage {i}:")
        print(f"  Field energy:    {record['field_stats']['energy']:.2f}")
        print(f"  AI chose hue:         {aesthetics['base_hue']:.3f} (color: "
              f"{'warm' if aesthetics['base_hue'] > 0.6 else 'cool' if aesthetics['base_hue'] < 0.4 else 'neutral'})")
        print(f"  AI chose saturation:  {aesthetics['saturation']:.3f} (intensity: "
              f"{'high' if aesthetics['saturation'] > 0.7 else 'low' if aesthetics['saturation'] < 0.4 else 'medium'})")
        print(f"  AI chose brightness:  {aesthetics['brightness']:.3f}")
        print(f"  AI chose complexity:  {aesthetics['complexity']:.3f}")

    print("\n" + "=" * 70)
    print("Files created:")
    print("  - ai_image_initial_state.png")
    print("  - ai_image_mid_dialogue.png")
    print("  - ai_image_evolved_state.png")
    if hasattr(engine, 'state_history') and len(engine.state_history) > 10:
        print("  - ai_cognitive_evolution.gif")
    print("=" * 70)
    print()


def main():
    """Run all examples"""
    examples = [
        ("1", "Basic dialogue", example_1_basic),
        ("2", "Dialogue with listener", example_2_with_listener),
        ("3", "Turn-taking dialogue", example_3_pulse_dialogue),
        ("4", "Custom parameters", example_4_custom_parameters),
        ("5", "AI autonomous image creation", example_5_autonomous_image_creation),
    ]

    print("\n" + "=" * 70)
    print("RECURSIVE DIALOGUE ENGINE - QUICKSTART")
    print("=" * 70)
    print("\nAvailable examples:")
    for num, desc, _ in examples:
        print(f"  {num}. {desc}")
    print("  all - Run all examples")
    print()

    choice = input("Select example (1-5, or 'all'): ").strip()

    if choice == 'all':
        for _, _, func in examples:
            func()
            print("\n")
    elif choice in ['1', '2', '3', '4', '5']:
        idx = int(choice) - 1
        examples[idx][2]()
    else:
        print("Invalid choice. Running Example 5 (AI autonomous image creation)...")
        example_5_autonomous_image_creation()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
