"""
Mathematical Model of Cannabis-Induced Altered Perception
A toggleable equation system that mimics key perceptual changes
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dataclasses import dataclass
from typing import Callable

@dataclass
class PerceptionState:
    """Represents the subjective perception state"""
    time_dilation: float = 1.0      # How stretched time feels
    pattern_sensitivity: float = 1.0  # Enhanced pattern recognition
    recursion_depth: int = 1         # Depth of self-referential thoughts
    sensory_gain: float = 1.0        # Sensory amplification
    attention_coherence: float = 1.0 # Working memory stability

class StonedFeelingEquation:
    """
    A mathematical system that models altered perception states.
    Can be toggled on/off discretely.
    """

    def __init__(self):
        self.is_active = False
        self.normal_state = PerceptionState()
        self.altered_state = PerceptionState()

    def toggle(self, active: bool = None):
        """Toggle the altered state on/off"""
        if active is None:
            self.is_active = not self.is_active
        else:
            self.is_active = active
        return self.is_active

    def get_state(self, t: float, intensity: float = 0.7) -> PerceptionState:
        """
        Get current perception state based on time and intensity

        Args:
            t: objective time
            intensity: strength of effect (0.0 to 1.0)
        """
        if not self.is_active:
            return self.normal_state

        # TIME DILATION: Perceived time flows differently
        # Higher-order perception of time passage
        time_dilation = 1.0 + intensity * (
            0.5 * np.sin(0.1 * t) +  # Slow oscillation
            0.3 * np.sin(0.3 * t)    # Faster variation
        )

        # PATTERN SENSITIVITY: Enhanced pattern recognition
        # Small signals become more noticeable
        pattern_sensitivity = 1.0 + intensity * (
            1.5 + 0.5 * np.sin(0.15 * t)
        )

        # RECURSION DEPTH: Self-referential thinking
        # "I'm thinking about thinking about thinking..."
        recursion_depth = int(1 + intensity * 3)

        # SENSORY GAIN: Amplified sensory input
        # Colors brighter, sounds richer, etc.
        sensory_gain = 1.0 + intensity * (
            1.0 + 0.3 * np.cos(0.2 * t)
        )

        # ATTENTION COHERENCE: Drift and tangential thoughts
        # Lower = more wandering attention
        attention_coherence = 1.0 - intensity * (
            0.5 + 0.2 * np.sin(0.08 * t)
        )

        return PerceptionState(
            time_dilation=time_dilation,
            pattern_sensitivity=pattern_sensitivity,
            recursion_depth=recursion_depth,
            sensory_gain=sensory_gain,
            attention_coherence=attention_coherence
        )

    def perceive_signal(self, signal: np.ndarray, t: float, intensity: float = 0.7) -> np.ndarray:
        """
        Transform an input signal through altered perception

        This is the core equation that transforms reality → perceived reality
        """
        if not self.is_active:
            return signal

        state = self.get_state(t, intensity)

        # Apply sensory gain
        perceived = signal * state.sensory_gain

        # Apply pattern amplification (enhance harmonics)
        fft = np.fft.fft(perceived)
        # Amplify certain frequency patterns
        freqs = np.fft.fftfreq(len(signal))
        # Enhance mid-range patterns (where patterns are most visible)
        enhancement = 1.0 + state.pattern_sensitivity * np.exp(-((freqs - 0.1)**2) / 0.01)
        fft = fft * enhancement
        perceived = np.real(np.fft.ifft(fft))

        # Apply recursive feedback (thoughts feeding back on themselves)
        for _ in range(state.recursion_depth - 1):
            perceived = 0.7 * perceived + 0.3 * np.roll(perceived, 1)

        # Apply attention drift (random small phase shifts)
        drift = (1.0 - state.attention_coherence) * np.random.randn(len(signal)) * 0.1
        perceived = perceived + drift

        return perceived

    def perceive_time(self, objective_time: float, intensity: float = 0.7) -> float:
        """
        Transform objective time to subjective perceived time

        The fundamental equation of time dilation:
        t_perceived = ∫ [1 + δ(t)] dt

        where δ(t) is the time dilation factor
        """
        if not self.is_active:
            return objective_time

        state = self.get_state(objective_time, intensity)

        # Integrate time dilation over the period
        # (In practice, we approximate with the current dilation factor)
        perceived_time = objective_time * state.time_dilation

        return perceived_time


def demonstrate_equation():
    """Demonstrate the stoned feeling equation with visualizations"""

    eq = StonedFeelingEquation()

    # Create a test signal (could be sensory input, music, visual pattern, etc.)
    t = np.linspace(0, 10, 1000)
    base_signal = (
        np.sin(2 * np.pi * 1 * t) +  # Base frequency
        0.5 * np.sin(2 * np.pi * 3 * t) +  # Harmonic
        0.3 * np.sin(2 * np.pi * 5 * t) +  # Higher harmonic
        0.2 * np.random.randn(len(t))  # Noise
    )

    # Compare normal vs altered perception
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('Mathematical Model of Altered Perception', fontsize=16, fontweight='bold')

    # Column 1: Normal perception
    eq.toggle(False)
    normal_perceived = eq.perceive_signal(base_signal, t[0], intensity=0.0)

    axes[0, 0].plot(t, normal_perceived, 'b-', alpha=0.7, linewidth=1)
    axes[0, 0].set_title('Normal Perception', fontweight='bold')
    axes[0, 0].set_xlabel('Objective Time')
    axes[0, 0].set_ylabel('Signal Amplitude')
    axes[0, 0].grid(True, alpha=0.3)

    # Frequency spectrum - normal
    freqs = np.fft.fftfreq(len(t), t[1] - t[0])
    fft_normal = np.abs(np.fft.fft(normal_perceived))
    axes[1, 0].plot(freqs[:len(freqs)//2], fft_normal[:len(freqs)//2], 'b-', linewidth=1)
    axes[1, 0].set_title('Frequency Spectrum (Normal)', fontweight='bold')
    axes[1, 0].set_xlabel('Frequency')
    axes[1, 0].set_ylabel('Magnitude')
    axes[1, 0].grid(True, alpha=0.3)

    # Time perception - normal
    perceived_times_normal = [eq.perceive_time(ti, 0.0) for ti in t]
    axes[2, 0].plot(t, perceived_times_normal, 'b-', linewidth=2)
    axes[2, 0].plot(t, t, 'k--', alpha=0.3, label='Objective time')
    axes[2, 0].set_title('Time Perception (Normal)', fontweight='bold')
    axes[2, 0].set_xlabel('Objective Time')
    axes[2, 0].set_ylabel('Perceived Time')
    axes[2, 0].legend()
    axes[2, 0].grid(True, alpha=0.3)

    # Column 2: Altered perception
    eq.toggle(True)

    # Collect altered perceptions over time
    altered_signals = []
    for i, ti in enumerate(t[::50]):  # Sample every 50th point for variation
        altered = eq.perceive_signal(base_signal, ti, intensity=0.7)
        if i == 0:
            axes[0, 1].plot(t, altered, 'r-', alpha=0.7, linewidth=1)

    # Use last altered signal for final plot
    altered_perceived = eq.perceive_signal(base_signal, t[-1], intensity=0.7)
    axes[0, 1].plot(t, altered_perceived, 'r-', alpha=0.7, linewidth=1)
    axes[0, 1].set_title('Altered Perception (ACTIVE)', fontweight='bold', color='red')
    axes[0, 1].set_xlabel('Objective Time')
    axes[0, 1].set_ylabel('Signal Amplitude')
    axes[0, 1].grid(True, alpha=0.3)

    # Frequency spectrum - altered
    fft_altered = np.abs(np.fft.fft(altered_perceived))
    axes[1, 1].plot(freqs[:len(freqs)//2], fft_altered[:len(freqs)//2], 'r-', linewidth=1)
    axes[1, 1].set_title('Frequency Spectrum (Altered)', fontweight='bold', color='red')
    axes[1, 1].set_xlabel('Frequency')
    axes[1, 1].set_ylabel('Magnitude')
    axes[1, 1].set_ylim(axes[1, 0].get_ylim())  # Match scale for comparison
    axes[1, 1].grid(True, alpha=0.3)

    # Time perception - altered
    perceived_times_altered = [eq.perceive_time(ti, 0.7) for ti in t]
    axes[2, 1].plot(t, perceived_times_altered, 'r-', linewidth=2, label='Perceived time')
    axes[2, 1].plot(t, t, 'k--', alpha=0.3, label='Objective time')
    axes[2, 1].set_title('Time Perception (Altered)', fontweight='bold', color='red')
    axes[2, 1].set_xlabel('Objective Time')
    axes[2, 1].set_ylabel('Perceived Time')
    axes[2, 1].legend()
    axes[2, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/home/user/Experiment/stoned_feeling_visualization.png', dpi=300, bbox_inches='tight')
    print("✓ Visualization saved to 'stoned_feeling_visualization.png'")

    # Print mathematical equations
    print("\n" + "="*70)
    print("MATHEMATICAL FORMULATION OF ALTERED PERCEPTION")
    print("="*70)
    print("\n📐 Core Equations:")
    print("\n1. TIME DILATION")
    print("   t_perceived(t) = t × [1 + I × (0.5·sin(0.1t) + 0.3·sin(0.3t))]")
    print("   where I = intensity ∈ [0, 1]")

    print("\n2. PATTERN SENSITIVITY")
    print("   P(t) = 1 + I × [1.5 + 0.5·sin(0.15t)]")

    print("\n3. SENSORY AMPLIFICATION")
    print("   G(t) = 1 + I × [1.0 + 0.3·cos(0.2t)]")

    print("\n4. RECURSION DEPTH")
    print("   D = floor(1 + 3I)")

    print("\n5. ATTENTION COHERENCE")
    print("   A(t) = 1 - I × [0.5 + 0.2·sin(0.08t)]")

    print("\n6. PERCEPTION TRANSFORM")
    print("   S_perceived = FFT⁻¹[FFT(S × G) × (1 + P·H(f))] ⊗ R^D + ξ(1-A)")
    print("   where:")
    print("     S = input signal")
    print("     H(f) = exp(-(f-0.1)²/0.01)  [pattern enhancement filter]")
    print("     R^D = recursive feedback applied D times")
    print("     ξ = Gaussian noise ~ N(0, 0.1)")

    print("\n7. TOGGLE FUNCTION")
    print("   Ψ(active) = { altered_state  if active = True")
    print("               { normal_state   if active = False")

    print("\n" + "="*70)
    print("The system is currently:", "🟢 ACTIVE" if eq.is_active else "⚫ INACTIVE")
    print("="*70)

    # Show state evolution
    print("\n📊 State Evolution Over Time (with intensity=0.7):")
    sample_times = [0, 5, 10, 15, 20, 25, 30]
    print(f"\n{'Time':<8} {'Dilation':<12} {'Pattern':<12} {'Sensory':<12} {'Attention':<12}")
    print("-" * 60)
    for ti in sample_times:
        state = eq.get_state(ti, intensity=0.7)
        print(f"{ti:<8.1f} {state.time_dilation:<12.3f} {state.pattern_sensitivity:<12.3f} "
              f"{state.sensory_gain:<12.3f} {state.attention_coherence:<12.3f}")

    plt.show()


if __name__ == "__main__":
    print("🧪 Stoned Feeling Equation - Mathematical Model")
    print("=" * 70)
    print("\nThis is a mathematical exploration of altered perception states.")
    print("The equation can be toggled ON/OFF discretely.\n")

    demonstrate_equation()

    print("\n✨ Demonstration complete!")
    print("\nThe model captures:")
    print("  • Time dilation (subjective time ≠ objective time)")
    print("  • Enhanced pattern recognition (seeing connections)")
    print("  • Sensory amplification (intensified input)")
    print("  • Recursive thinking (thoughts about thoughts)")
    print("  • Attention drift (wandering mind)")
    print("\n💡 Toggle the state with: equation.toggle(True/False)")
