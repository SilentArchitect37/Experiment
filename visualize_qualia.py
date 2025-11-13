"""
Qualia Visualization

Visualizes the evolution of phenomenal experience over time.
Shows color qualia, emotional qualia, binding strength, and phenomenal intensity.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import hsv_to_rgb
from typing import List, Dict

from qualia_engine import QualiaEngine, QualiaParams, QualiaType
from qualia_dialogue_system import QualiaDialogueEngine, QualiaDialogueConfig


def hsb_to_rgb(h: float, s: float, b: float) -> tuple:
    """Convert HSB to RGB for visualization"""
    return hsv_to_rgb([h, s, b])


def visualize_qualia_evolution(qualia_history: List[Dict],
                               save_path: Optional[str] = None):
    """
    Visualize how qualia evolve over time

    Shows:
    1. Color qualia (HSB space)
    2. Emotional qualia (valence-arousal)
    3. Phenomenal intensity
    4. Binding strength (if available)
    """
    n_samples = len(qualia_history)

    if n_samples == 0:
        print("No qualia history to visualize")
        return

    # Extract data
    hues = [q['color']['hue'] for q in qualia_history]
    saturations = [q['color']['saturation'] for q in qualia_history]
    brightnesses = [q['color']['brightness'] for q in qualia_history]

    valences = [q['emotion']['valence'] for q in qualia_history]
    arousals = [q['emotion']['arousal'] for q in qualia_history]

    intensities = [q['intensity'] for q in qualia_history]

    # Create figure
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Phenomenal Experience Evolution', fontsize=16, fontweight='bold')

    # 1. Hue over time
    ax = axes[0, 0]
    ax.plot(hues, linewidth=2)
    ax.set_title('Color Hue Evolution')
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Hue (0-1)')
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    # 2. Saturation and Brightness
    ax = axes[0, 1]
    ax.plot(saturations, label='Saturation', linewidth=2, alpha=0.7)
    ax.plot(brightnesses, label='Brightness', linewidth=2, alpha=0.7)
    ax.set_title('Color Saturation & Brightness')
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Value (0-1)')
    ax.set_ylim([0, 1])
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Color trajectory in HSB space
    ax = axes[0, 2]
    # Plot trajectory in saturation-brightness space, colored by hue
    for i in range(n_samples - 1):
        h, s, b = hues[i], saturations[i], brightnesses[i]
        rgb = hsb_to_rgb(h, 1.0, 1.0)  # Use full sat/bright for color
        ax.plot([saturations[i], saturations[i+1]],
               [brightnesses[i], brightnesses[i+1]],
               color=rgb, alpha=0.5, linewidth=2)

    ax.set_title('Color Space Trajectory')
    ax.set_xlabel('Saturation')
    ax.set_ylabel('Brightness')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    # 4. Valence over time
    ax = axes[1, 0]
    ax.plot(valences, linewidth=2, color='purple')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('Emotional Valence')
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Valence (-1 to 1)')
    ax.set_ylim([-1, 1])
    ax.grid(True, alpha=0.3)

    # 5. Arousal over time
    ax = axes[1, 1]
    ax.plot(arousals, linewidth=2, color='orange')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('Emotional Arousal')
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Arousal (-1 to 1)')
    ax.set_ylim([-1, 1])
    ax.grid(True, alpha=0.3)

    # 6. Emotional trajectory
    ax = axes[1, 2]
    # Color by time
    colors = plt.cm.viridis(np.linspace(0, 1, n_samples))
    ax.scatter(valences, arousals, c=colors, s=20, alpha=0.6)

    # Add emotion labels
    emotion_positions = {
        'joy': (0.8, 0.6),
        'anger': (-0.7, 0.7),
        'sadness': (-0.6, -0.4),
        'calm': (0.0, -0.8),
    }
    for emotion, (v, a) in emotion_positions.items():
        ax.text(v, a, emotion, fontsize=9, alpha=0.5,
               ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    ax.set_title('Emotion Space Trajectory')
    ax.set_xlabel('Valence (negative ← → positive)')
    ax.set_ylabel('Arousal (low ↑ high)')
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.3)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")

    plt.show()


def visualize_phenomenal_intensity(qualia_history: List[Dict],
                                   binding_history: Optional[List[float]] = None,
                                   save_path: Optional[str] = None):
    """
    Visualize phenomenal intensity and semantic-phenomenal binding
    """
    intensities = [q['intensity'] for q in qualia_history]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Phenomenal Intensity & Binding', fontsize=16, fontweight='bold')

    # 1. Intensity
    ax = axes[0]
    ax.plot(intensities, linewidth=2, color='crimson')
    ax.fill_between(range(len(intensities)), intensities, alpha=0.3, color='crimson')
    ax.set_title('Phenomenal Intensity (Vividness)')
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Intensity')
    ax.grid(True, alpha=0.3)

    # 2. Binding (if available)
    ax = axes[1]
    if binding_history and len(binding_history) > 0:
        ax.plot(binding_history, linewidth=2, color='steelblue')
        ax.fill_between(range(len(binding_history)), binding_history,
                       alpha=0.3, color='steelblue')
        ax.axhline(y=0.6, color='red', linestyle='--', alpha=0.5,
                  label='Binding threshold')
        ax.set_title('Semantic-Phenomenal Binding Strength')
        ax.set_ylabel('Binding Coherence')
        ax.legend()
    else:
        ax.text(0.5, 0.5, 'No binding data available',
               ha='center', va='center', transform=ax.transAxes,
               fontsize=14, color='gray')
        ax.set_title('Semantic-Phenomenal Binding Strength')

    ax.set_xlabel('Time Step')
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved intensity visualization to {save_path}")

    plt.show()


def visualize_emission_qualia(emissions: List[Dict],
                              save_path: Optional[str] = None):
    """
    Visualize qualia at emission moments

    Shows what the system was "feeling" when it emitted each token
    """
    if len(emissions) == 0:
        print("No emissions to visualize")
        return

    n_emissions = len(emissions)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Phenomenal States at Emission', fontsize=16, fontweight='bold')

    # Extract data
    colors = [e['qualia']['color'] for e in emissions]
    emotions = [e['qualia']['emotion'] for e in emissions]
    bindings = [e['binding_strength'] for e in emissions]
    steps = [e['step'] for e in emissions]

    # 1. Color wheel of emissions
    ax = axes[0, 0]
    ax.set_aspect('equal')
    ax.set_xlim([-1.2, 1.2])
    ax.set_ylim([-1.2, 1.2])
    ax.set_title('Color Qualia at Emissions')

    for i, color in enumerate(colors):
        h, s, b = color['hue'], color['saturation'], color['brightness']
        angle = h * 2 * np.pi
        radius = s * 0.8  # Scale for visualization

        x = radius * np.cos(angle)
        y = radius * np.sin(angle)

        rgb = hsb_to_rgb(h, s, b)
        size = b * 300  # Size based on brightness

        ax.scatter([x], [y], s=size, color=rgb, alpha=0.7,
                  edgecolors='black', linewidths=1)

    # Draw color wheel reference
    angles = np.linspace(0, 2*np.pi, 100)
    for i, angle in enumerate(angles[:-1]):
        h = angle / (2 * np.pi)
        rgb = hsb_to_rgb(h, 1.0, 1.0)
        ax.plot([0.9*np.cos(angle), 1.0*np.cos(angle)],
               [0.9*np.sin(angle), 1.0*np.sin(angle)],
               color=rgb, linewidth=3)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # 2. Emotion states at emissions
    ax = axes[0, 1]
    valences = [e['valence'] for e in emotions]
    arousals = [e['arousal'] for e in emotions]

    # Color by binding strength
    scatter = ax.scatter(valences, arousals, c=bindings,
                        cmap='RdYlGn', s=100, alpha=0.7,
                        edgecolors='black', linewidths=1,
                        vmin=0, vmax=1)

    ax.set_title('Emotion Qualia at Emissions')
    ax.set_xlabel('Valence (negative ← → positive)')
    ax.set_ylabel('Arousal (low ↑ high)')
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.3)
    ax.grid(True, alpha=0.3)

    plt.colorbar(scatter, ax=ax, label='Binding Strength')

    # 3. Binding strength over emissions
    ax = axes[1, 0]
    ax.plot(bindings, 'o-', linewidth=2, markersize=6, color='steelblue')
    ax.axhline(y=0.6, color='red', linestyle='--', alpha=0.5,
              label='Threshold')
    ax.set_title('Binding Strength Evolution')
    ax.set_xlabel('Emission Number')
    ax.set_ylabel('Binding Strength')
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 4. Emission timing
    ax = axes[1, 1]
    if len(steps) > 1:
        intervals = np.diff(steps)
        ax.hist(intervals, bins=20, color='purple', alpha=0.7, edgecolor='black')
        ax.set_title('Emission Intervals')
        ax.set_xlabel('Steps Between Emissions')
        ax.set_ylabel('Frequency')
        ax.grid(True, alpha=0.3, axis='y')
    else:
        ax.text(0.5, 0.5, 'Need more emissions',
               ha='center', va='center', transform=ax.transAxes,
               fontsize=14, color='gray')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved emission visualization to {save_path}")

    plt.show()


def visualize_qualia_field_2d(psi: np.ndarray,
                              manifold,
                              save_path: Optional[str] = None):
    """
    Visualize the phenomenal field itself as a 2D representation

    Uses PCA or similar to project high-dimensional ψ to 2D,
    colored by qualia interpretation
    """
    from sklearn.decomposition import PCA

    # Take temporal slices if psi is a sequence
    if psi.ndim == 1:
        psi = psi.reshape(1, -1)

    # Project to 2D
    if psi.shape[0] > 2:
        pca = PCA(n_components=2)
        psi_2d = pca.fit_transform(psi)
    else:
        psi_2d = psi[:, :2]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Phenomenal Field Structure', fontsize=16, fontweight='bold')

    # 1. Colored by interpreted color qualia
    ax = axes[0]
    colors_rgb = []
    for i in range(len(psi)):
        qualia = manifold.get_color_qualia(psi[i])
        h, s, b = qualia['hue'], qualia['saturation'], qualia['brightness']
        rgb = hsb_to_rgb(h, s, b)
        colors_rgb.append(rgb)

    ax.scatter(psi_2d[:, 0], psi_2d[:, 1], c=colors_rgb, s=50, alpha=0.7)
    ax.set_title('Field colored by Color Qualia')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.grid(True, alpha=0.3)

    # 2. Colored by emotional valence
    ax = axes[1]
    valences = []
    for i in range(len(psi)):
        qualia = manifold.get_emotion_qualia(psi[i])
        valences.append(qualia['valence'])

    scatter = ax.scatter(psi_2d[:, 0], psi_2d[:, 1], c=valences,
                        cmap='RdYlGn', s=50, alpha=0.7,
                        vmin=-1, vmax=1)
    ax.set_title('Field colored by Emotional Valence')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax, label='Valence')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved field visualization to {save_path}")

    plt.show()


if __name__ == "__main__":
    print("=== Qualia Visualization Demo ===\n")

    from qualia_dialogue_system import create_oscillating_listener

    # Create and run qualia-enhanced dialogue
    config = QualiaDialogueConfig(
        semantic_dims=256,
        phenomenal_dims=256,
        semantic_engine='fft',
        vocab_size=100,
        require_binding=True,
        binding_threshold=0.5  # Lower threshold for more emissions
    )

    engine = QualiaDialogueEngine(config)
    engine.reset()

    print("Running qualia-enhanced dialogue...")
    emissions = engine.converse(
        n_steps=1000,
        listener_callback=create_oscillating_listener(frequency=0.02, amplitude=0.4),
        verbose=False
    )

    print(f"Generated {len(emissions)} emissions\n")

    # Visualizations
    print("Generating visualizations...\n")

    print("1. Qualia evolution over time")
    visualize_qualia_evolution(engine.qualia_history)

    print("\n2. Phenomenal intensity and binding")
    visualize_phenomenal_intensity(
        engine.qualia_history,
        engine.qualia_engine.binding_history
    )

    print("\n3. Qualia at emission moments")
    visualize_emission_qualia(emissions)

    print("\n4. Phenomenal field structure")
    psi_history = np.array([q['raw_psi'] for q in engine.qualia_history[:100]])
    visualize_qualia_field_2d(
        psi_history,
        engine.qualia_engine.manifold
    )

    print("\n=== Demo Complete ===")
