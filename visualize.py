"""
Visualization tools for Recursive Dialogue Engine

Plots:
1. μ field evolution over time
2. Recursive entropy trajectory
3. Emission timing and coherence
4. Phase space analysis
"""

import numpy as np
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from recursive_engine import create_engine, RecursiveParams
from dialogue_system import RecursiveDialogueEngine, DialogueConfig
from dialogue_system import create_oscillating_listener


def plot_field_evolution(engine, n_steps: int = 200, n_snapshots: int = 5):
    """
    Plot evolution of μ field over time.

    Shows how the field develops spatial structure through diffusion
    and nonlinearity.
    """
    fig, axes = plt.subplots(1, n_snapshots, figsize=(15, 3))
    fig.suptitle('μ Field Evolution', fontsize=14)

    # Perturb initial state
    engine.reset()
    engine.mu += np.random.randn(len(engine.mu)) * 0.5

    snapshot_interval = n_steps // n_snapshots

    for i, ax in enumerate(axes):
        # Evolve to snapshot time
        for _ in range(snapshot_interval):
            engine.step()

        # Plot current state
        t = (i + 1) * snapshot_interval
        ax.plot(engine.mu if isinstance(engine.mu, np.ndarray) else engine.mu.cpu().numpy())
        ax.set_title(f't = {t}')
        ax.set_xlabel('Position')
        ax.set_ylabel('μ')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-2, 2)

    plt.tight_layout()
    return fig


def plot_entropy_trajectory(dialogue_engine, n_steps: int = 1000):
    """
    Plot recursive entropy over time with emission markers.
    """
    from emission_detector import EmissionDetector

    # Run dialogue and collect entropy
    entropies = []
    emission_times = []
    emission_entropies = []

    for t in range(n_steps):
        emission = dialogue_engine.step()

        # Compute entropy
        entropy = dialogue_engine.detector.compute_entropy(
            dialogue_engine.engine.mu if isinstance(dialogue_engine.engine.mu, np.ndarray)
            else dialogue_engine.engine.mu.cpu().numpy()
        )
        entropies.append(entropy)

        if emission is not None:
            emission_times.append(t)
            emission_entropies.append(entropy)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(entropies, label='Recursive Entropy S_R', linewidth=1)
    ax.scatter(emission_times, emission_entropies, c='red', s=50,
               label='Emissions', zorder=5, marker='v')

    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel('Recursive Entropy', fontsize=12)
    ax.set_title('Entropy Trajectory with Emission Events', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_coherence_analysis(emissions: List[Dict]):
    """
    Analyze coherence patterns in emission sequence.
    """
    if not emissions:
        print("No emissions to analyze")
        return None

    times = [e['time'] for e in emissions]
    tokens = [e['token'] for e in emissions]
    coherences = [e['coherence'] for e in emissions]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Dialogue Coherence Analysis', fontsize=14)

    # 1. Coherence over time
    axes[0, 0].plot(times, coherences, marker='o', markersize=3, linewidth=1)
    axes[0, 0].set_xlabel('Time')
    axes[0, 0].set_ylabel('Coherence Δμ')
    axes[0, 0].set_title('Phase Coherence at Emission')
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Token sequence
    axes[0, 1].scatter(times, tokens, c=coherences, cmap='viridis', s=20)
    axes[0, 1].set_xlabel('Time')
    axes[0, 1].set_ylabel('Token ID')
    axes[0, 1].set_title('Token Sequence (colored by coherence)')
    axes[0, 1].grid(True, alpha=0.3)
    plt.colorbar(axes[0, 1].collections[0], ax=axes[0, 1], label='Coherence')

    # 3. Inter-emission intervals
    if len(times) > 1:
        intervals = np.diff(times)
        axes[1, 0].hist(intervals, bins=20, edgecolor='black')
        axes[1, 0].set_xlabel('Interval (steps)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title(f'Emission Intervals (μ={np.mean(intervals):.1f})')
        axes[1, 0].grid(True, alpha=0.3)

    # 4. Token distribution
    unique_tokens = len(set(tokens))
    axes[1, 1].hist(tokens, bins=min(30, unique_tokens), edgecolor='black')
    axes[1, 1].set_xlabel('Token ID')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title(f'Token Distribution ({unique_tokens} unique)')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_phase_space(engine, n_steps: int = 5000):
    """
    Plot phase space trajectory: (μ_mean, μ_std) or (E, S)
    """
    # Run dynamics and collect statistics
    energies = []
    entropies = []

    engine.reset()
    engine.mu += np.random.randn(len(engine.mu)) * 0.3

    for _ in range(n_steps):
        engine.step()

        mu = engine.mu if isinstance(engine.mu, np.ndarray) else engine.mu.cpu().numpy()

        # Energy
        energy = np.sum(mu ** 2)
        energies.append(energy)

        # Entropy
        eps = 1e-8
        mu_sq = mu * mu
        entropy = -np.sum(mu_sq * np.log(mu_sq + eps))
        entropies.append(entropy)

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Energy-Entropy phase space
    axes[0].plot(energies, entropies, linewidth=0.5, alpha=0.7)
    axes[0].scatter([energies[0]], [entropies[0]], c='green', s=100,
                    label='Start', zorder=5, marker='o')
    axes[0].scatter([energies[-1]], [entropies[-1]], c='red', s=100,
                    label='End', zorder=5, marker='x')
    axes[0].set_xlabel('Energy E = Σμ²', fontsize=12)
    axes[0].set_ylabel('Entropy S_R', fontsize=12)
    axes[0].set_title('Phase Space Trajectory', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Time series
    axes[1].plot(energies, label='Energy', alpha=0.7)
    axes[1].plot(entropies, label='Entropy', alpha=0.7)
    axes[1].set_xlabel('Time Step', fontsize=12)
    axes[1].set_ylabel('Value', fontsize=12)
    axes[1].set_title('Energy & Entropy Evolution', fontsize=14)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def demo_visualization():
    """Run complete visualization demo"""
    print("=== Recursive Dialogue Engine Visualization Demo ===\n")

    # 1. Field evolution
    print("1. Generating field evolution plot...")
    params = RecursiveParams(g=0.1, lam=0.3, rho=0.4, dt=0.01)
    engine = create_engine('fft', params, n_dims=256)
    fig1 = plot_field_evolution(engine, n_steps=200, n_snapshots=5)
    fig1.savefig('field_evolution.png', dpi=150, bbox_inches='tight')
    print("   Saved: field_evolution.png")

    # 2. Entropy trajectory
    print("2. Generating entropy trajectory...")
    config = DialogueConfig(
        state_dims=256,
        vocab_size=100,
        engine_optimization='fft'
    )
    config.engine_params.g = 0.15
    config.engine_params.lam = 0.3
    config.emission_config.cooldown_steps = 20

    dialogue = RecursiveDialogueEngine(config)
    fig2 = plot_entropy_trajectory(dialogue, n_steps=1000)
    fig2.savefig('entropy_trajectory.png', dpi=150, bbox_inches='tight')
    print("   Saved: entropy_trajectory.png")

    # 3. Run dialogue with listener and analyze
    print("3. Running dialogue simulation...")
    dialogue.reset()
    listener = create_oscillating_listener(frequency=0.03, amplitude=0.3, dims=256)
    emissions = dialogue.converse(n_steps=1000, listener_callback=listener, verbose=False)

    print(f"   Generated {len(emissions)} emissions")

    if emissions:
        fig3 = plot_coherence_analysis(emissions)
        fig3.savefig('coherence_analysis.png', dpi=150, bbox_inches='tight')
        print("   Saved: coherence_analysis.png")

    # 4. Phase space
    print("4. Generating phase space plot...")
    engine2 = create_engine('fft', params, n_dims=256)
    fig4 = plot_phase_space(engine2, n_steps=3000)
    fig4.savefig('phase_space.png', dpi=150, bbox_inches='tight')
    print("   Saved: phase_space.png")

    print("\n=== Visualization Complete ===")
    print("Generated files:")
    print("  - field_evolution.png")
    print("  - entropy_trajectory.png")
    print("  - coherence_analysis.png")
    print("  - phase_space.png")


if __name__ == "__main__":
    try:
        demo_visualization()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure matplotlib is installed:")
        print("  pip install matplotlib")
