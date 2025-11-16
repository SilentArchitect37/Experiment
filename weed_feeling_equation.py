"""
Mathematical Model of Cannabis-Induced Perception (ACTUALLY weed, not shrooms)
A toggleable equation system that mimics actual weed effects
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Callable

@dataclass
class CannabisPerceptionState:
    """Represents the subjective perception state when high on cannabis"""
    time_dilation: float = 1.0       # Mild time slowdown
    working_memory: float = 1.0      # Memory decay (train of thought loss)
    sensory_enhancement: float = 1.0 # Food tastes better, music richer
    thought_tangent_prob: float = 0.0 # Probability of derailing thoughts
    humor_sensitivity: float = 1.0   # Everything becomes funnier
    motor_delay: float = 0.0         # Reaction time slowdown
    munchies_factor: float = 0.0     # Appetite enhancement

class WeedFeelingEquation:
    """
    A mathematical system that models cannabis perception.
    Much more subtle than psychedelics - no fractals, just vibes.
    """

    def __init__(self):
        self.is_active = False
        self.normal_state = CannabisPerceptionState()
        self.consumption_time = 0.0  # Track when consumption occurred

    def toggle(self, active: bool = None):
        """Toggle the high on/off"""
        if active is None:
            self.is_active = not self.is_active
        else:
            self.is_active = active

        # Reset consumption time when activating
        if self.is_active:
            self.consumption_time = 0.0

        return self.is_active

    def effect_envelope(self, t: float) -> float:
        """
        Calculate the natural onset/peak/decay envelope over time.

        Realistic cannabis pharmacokinetics (smoked/vaped):
        - Onset: 0-5 minutes (rapid rise)
        - Peak: 5-15 minutes (maximum effect)
        - Plateau: 15-45 minutes (sustained)
        - Decay: 45-120 minutes (gradual comedown)
        - Baseline: 120+ minutes (mostly sober)

        Returns: multiplier from 0.0 (sober) to 1.0 (peak high)
        """
        if not self.is_active:
            return 0.0

        # Time in minutes since consumption
        time_elapsed = t - self.consumption_time

        if time_elapsed < 0:
            return 0.0
        elif time_elapsed < 5:
            # Onset phase: rapid rise (0 to 1)
            # Exponential approach to peak
            return 1.0 - np.exp(-0.6 * time_elapsed)
        elif time_elapsed < 15:
            # Peak phase: maximum effect with slight fluctuation
            peak_level = 0.95 + 0.05 * np.sin(0.5 * time_elapsed)
            return peak_level
        elif time_elapsed < 45:
            # Plateau phase: sustained high with gentle decline
            plateau_start = 1.0
            plateau_end = 0.75
            progress = (time_elapsed - 15) / (45 - 15)
            return plateau_start - (plateau_start - plateau_end) * progress
        elif time_elapsed < 120:
            # Decay phase: gradual comedown (exponential decay)
            decay_start = 0.75
            time_in_decay = time_elapsed - 45
            return decay_start * np.exp(-0.025 * time_in_decay)
        else:
            # Mostly sober, with very slight residual
            return 0.05 * np.exp(-0.01 * (time_elapsed - 120))


    def get_state(self, t: float, intensity: float = 0.7) -> CannabisPerceptionState:
        """
        Get current perception state based on time and intensity

        Args:
            t: objective time (time since consumption in minutes)
            intensity: base strength of effect (0.0 to 1.0)
        """
        if not self.is_active:
            return self.normal_state

        # Get the natural decay envelope (0.0 to 1.0)
        envelope = self.effect_envelope(t)

        # Apply envelope to intensity - all effects naturally decay over time
        effective_intensity = intensity * envelope

        # TIME DILATION: Things feel slower (but not wildly different)
        # Mild effect - maybe 1.2-1.5x slower perception
        time_dilation = 1.0 + effective_intensity * 0.3 * (1 + 0.2 * np.sin(0.05 * t))

        # WORKING MEMORY DECAY: "Wait, what was I just saying?"
        # Exponential decay of short-term memory buffer
        # Peak around t=2-5, then gradually recovers
        memory_curve = np.exp(-0.1 * (t - 3)**2)  # Peak at t=3
        working_memory = 1.0 - effective_intensity * 0.6 * memory_curve

        # SENSORY ENHANCEMENT: Music sounds richer, food tastes amazing
        # Mild amplification, not hallucinations
        sensory_enhancement = 1.0 + effective_intensity * (0.8 + 0.3 * np.sin(0.1 * t))

        # THOUGHT TANGENTS: Random derailment of train of thought
        # "I was thinking about pizza... wait, do fish get thirsty?"
        thought_tangent_prob = effective_intensity * 0.4 * (1 + 0.2 * np.sin(0.08 * t))

        # HUMOR SENSITIVITY: Everything is funnier
        humor_sensitivity = 1.0 + effective_intensity * (1.5 + 0.5 * np.cos(0.12 * t))

        # MOTOR DELAY: Reaction time slowdown, "couch lock"
        motor_delay = effective_intensity * 0.3 * (1 + 0.2 * np.sin(0.06 * t))

        # MUNCHIES: Enhanced appetite
        # Peaks after initial onset
        munchies_curve = 1 / (1 + np.exp(-0.5 * (t - 4)))  # Sigmoid centered at t=4
        munchies_factor = effective_intensity * munchies_curve

        return CannabisPerceptionState(
            time_dilation=time_dilation,
            working_memory=working_memory,
            sensory_enhancement=sensory_enhancement,
            thought_tangent_prob=thought_tangent_prob,
            humor_sensitivity=humor_sensitivity,
            motor_delay=motor_delay,
            munchies_factor=munchies_factor
        )

    def perceive_signal(self, signal: np.ndarray, t: float, intensity: float = 0.7) -> np.ndarray:
        """
        Transform an input signal through cannabis perception
        (Much more subtle than psychedelics - just enhancement, not transformation)
        """
        if not self.is_active:
            return signal

        state = self.get_state(t, intensity)

        # Apply sensory enhancement (mild amplification)
        perceived = signal * state.sensory_enhancement

        # Add slight noise from reduced focus
        noise_level = (1.0 - state.working_memory) * 0.15
        perceived = perceived + np.random.randn(len(signal)) * noise_level

        # Mild smoothing (things feel more "smooth" or "rounded")
        from scipy.ndimage import gaussian_filter1d
        smoothing_sigma = 1 + intensity * 0.5
        perceived = gaussian_filter1d(perceived, sigma=smoothing_sigma)

        return perceived

    def perceive_time(self, objective_time: float, intensity: float = 0.7) -> float:
        """
        Transform objective time to subjective perceived time
        Mild dilation - not the extreme warping of psychedelics
        """
        if not self.is_active:
            return objective_time

        state = self.get_state(objective_time, intensity)
        perceived_time = objective_time * state.time_dilation

        return perceived_time

    def thought_derailment(self, original_thought: str, t: float, intensity: float = 0.7) -> list:
        """
        Model the tangential thinking pattern
        "I was thinking about X... but then I thought about Y... wait, what was I saying?"
        """
        if not self.is_active:
            return [original_thought]

        state = self.get_state(t, intensity)

        # Simulate thought chain with potential derailments
        thoughts = [original_thought]
        num_derailments = int(state.thought_tangent_prob * 5)  # 0-2 tangents typically

        for _ in range(num_derailments):
            thoughts.append("[tangent thought]")

        if num_derailments > 0 and state.working_memory < 0.6:
            thoughts.append("...wait, what was I saying?")

        return thoughts


def demonstrate_weed_equation():
    """Demonstrate the cannabis perception equation"""

    eq = WeedFeelingEquation()

    # Create test signal (could be music, visual input, etc.)
    t = np.linspace(0, 10, 1000)
    base_signal = (
        np.sin(2 * np.pi * 1 * t) +
        0.5 * np.sin(2 * np.pi * 2 * t) +
        0.3 * np.sin(2 * np.pi * 3 * t) +
        0.1 * np.random.randn(len(t))
    )

    # Create visualization
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('Mathematical Model of Cannabis Perception', fontsize=16, fontweight='bold')

    # Normal perception
    eq.toggle(False)
    normal_perceived = eq.perceive_signal(base_signal, t[0], intensity=0.0)

    axes[0, 0].plot(t, normal_perceived, 'b-', alpha=0.7, linewidth=1)
    axes[0, 0].set_title('Normal Perception (Sober)', fontweight='bold')
    axes[0, 0].set_xlabel('Time')
    axes[0, 0].set_ylabel('Signal (Music/Sensory Input)')
    axes[0, 0].grid(True, alpha=0.3)

    # Time perception - normal
    perceived_times_normal = [eq.perceive_time(ti, 0.0) for ti in t]
    axes[1, 0].plot(t, perceived_times_normal, 'b-', linewidth=2)
    axes[1, 0].plot(t, t, 'k--', alpha=0.3, label='Objective time')
    axes[1, 0].set_title('Time Perception (Sober)', fontweight='bold')
    axes[1, 0].set_xlabel('Objective Time (minutes)')
    axes[1, 0].set_ylabel('Perceived Time')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Working memory - normal
    axes[2, 0].axhline(y=1.0, color='b', linewidth=2)
    axes[2, 0].set_title('Working Memory (Sober)', fontweight='bold')
    axes[2, 0].set_xlabel('Time (minutes)')
    axes[2, 0].set_ylabel('Memory Retention')
    axes[2, 0].set_ylim([0, 1.5])
    axes[2, 0].grid(True, alpha=0.3)

    # High perception
    eq.toggle(True)
    high_perceived = eq.perceive_signal(base_signal, 3.0, intensity=0.7)

    axes[0, 1].plot(t, high_perceived, 'g-', alpha=0.7, linewidth=1)
    axes[0, 1].set_title('High Perception (Enhanced & Smooth)', fontweight='bold', color='green')
    axes[0, 1].set_xlabel('Time')
    axes[0, 1].set_ylabel('Signal (Music/Sensory Input)')
    axes[0, 1].grid(True, alpha=0.3)

    # Time perception - high
    perceived_times_high = [eq.perceive_time(ti, 0.7) for ti in t]
    axes[1, 1].plot(t, perceived_times_high, 'g-', linewidth=2, label='Perceived time')
    axes[1, 1].plot(t, t, 'k--', alpha=0.3, label='Objective time')
    axes[1, 1].set_title('Time Perception (Mild Dilation)', fontweight='bold', color='green')
    axes[1, 1].set_xlabel('Objective Time (minutes)')
    axes[1, 1].set_ylabel('Perceived Time')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    # Working memory decay over time
    time_course = np.linspace(0, 15, 100)
    memory_retention = [eq.get_state(ti, 0.7).working_memory for ti in time_course]
    axes[2, 1].plot(time_course, memory_retention, 'g-', linewidth=2)
    axes[2, 1].axhline(y=1.0, color='k', linestyle='--', alpha=0.3, label='Sober baseline')
    axes[2, 1].set_title('Working Memory Decay ("Wait, what?")', fontweight='bold', color='green')
    axes[2, 1].set_xlabel('Time (minutes)')
    axes[2, 1].set_ylabel('Memory Retention')
    axes[2, 1].set_ylim([0, 1.5])
    axes[2, 1].legend()
    axes[2, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/home/user/Experiment/weed_feeling_visualization.png', dpi=300, bbox_inches='tight')
    print("✓ Visualization saved to 'weed_feeling_visualization.png'")

    # Create a second figure showing the natural decay curve
    fig2, ax = plt.subplots(1, 1, figsize=(12, 6))

    # Plot the full decay envelope over 150 minutes
    time_full = np.linspace(0, 150, 1000)
    envelope_values = [eq.effect_envelope(ti) for ti in time_full]

    ax.plot(time_full, envelope_values, 'g-', linewidth=2.5, label='Effect Intensity')
    ax.fill_between(time_full, 0, envelope_values, alpha=0.3, color='green')

    # Mark the phases
    ax.axvspan(0, 5, alpha=0.1, color='yellow', label='Onset (0-5min)')
    ax.axvspan(5, 15, alpha=0.1, color='red', label='Peak (5-15min)')
    ax.axvspan(15, 45, alpha=0.1, color='orange', label='Plateau (15-45min)')
    ax.axvspan(45, 120, alpha=0.1, color='blue', label='Decay (45-120min)')

    ax.set_xlabel('Time Since Consumption (minutes)', fontsize=12)
    ax.set_ylabel('Effect Intensity (0-1)', fontsize=12)
    ax.set_title('Natural Cannabis Effect Decay Curve', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_ylim([0, 1.1])

    plt.tight_layout()
    plt.savefig('/home/user/Experiment/weed_decay_curve.png', dpi=300, bbox_inches='tight')
    print("✓ Decay curve saved to 'weed_decay_curve.png'")

    # Print equations
    print("\n" + "="*70)
    print("MATHEMATICAL MODEL OF CANNABIS PERCEPTION")
    print("="*70)
    print("\n📐 Core Equations (Actually weed this time, not shrooms):")

    print("\n0. NATURAL DECAY ENVELOPE (applies to all effects)")
    print("   E(t) = {")
    print("       1 - exp(-0.6t)           if 0 ≤ t < 5    [Onset: rapid rise]")
    print("       0.95 + 0.05·sin(0.5t)    if 5 ≤ t < 15   [Peak: maximum effect]")
    print("       1 - 0.25(t-15)/30        if 15 ≤ t < 45  [Plateau: sustained]")
    print("       0.75·exp[-0.025(t-45)]   if 45 ≤ t < 120 [Decay: comedown]")
    print("       0.05·exp[-0.01(t-120)]   if t ≥ 120      [Residual]")
    print("   }")
    print("   → All effects multiplied by E(t) for natural onset/decay")

    print("\n1. TIME DILATION (mild)")
    print("   t_perceived(t) = t × [1 + 0.3·E(t)·I × (1 + 0.2·sin(0.05t))]")
    print("   where I = base intensity ∈ [0, 1]")
    print("   → Typical dilation: 1.2-1.5x (not extreme)")

    print("\n2. WORKING MEMORY DECAY")
    print("   M(t) = 1 - 0.6·E(t)·I × exp[-0.1(t-3)²]")
    print("   → Peaks at t≈3min, causes 'wait, what was I saying?' moments")

    print("\n3. SENSORY ENHANCEMENT")
    print("   S(t) = 1 + E(t)·I × [0.8 + 0.3·sin(0.1t)]")
    print("   → Music sounds richer, food tastes better (no hallucinations)")

    print("\n4. THOUGHT TANGENT PROBABILITY")
    print("   P_tangent(t) = 0.4·E(t)·I × [1 + 0.2·sin(0.08t)]")
    print("   → Random derailment of train of thought")

    print("\n5. HUMOR SENSITIVITY")
    print("   H(t) = 1 + E(t)·I × [1.5 + 0.5·cos(0.12t)]")
    print("   → Everything becomes 1.5-2x funnier")

    print("\n6. MOTOR DELAY")
    print("   D(t) = 0.3·E(t)·I × [1 + 0.2·sin(0.06t)]")
    print("   → Reaction time slowdown, 'couch lock'")

    print("\n7. MUNCHIES FACTOR")
    print("   F(t) = E(t)·I / [1 + exp(-0.5(t-4))]")
    print("   → Appetite enhancement (sigmoid, peaks after ~4min)")

    print("\n8. SIGNAL PERCEPTION")
    print("   S_perceived = GaussianFilter(S × Enhancement, σ=1.5) + ξ(1-M)")
    print("   → Mild amplification + smoothing + memory-noise")

    print("\n" + "="*70)
    print("The system is currently:", "🟢 HIGH" if eq.is_active else "⚫ SOBER")
    print("="*70)

    # Show realistic state evolution with decay
    print("\n📊 State Evolution Over Time (intensity=0.7, showing full onset/peak/decay):")
    print(f"\n{'Time':<8} {'Envelope':<10} {'Dilation':<10} {'Memory':<10} {'Sensory':<10} {'Munchies':<10}")
    print("-" * 80)
    sample_times = [0, 2, 5, 10, 15, 30, 45, 60, 90, 120, 150]
    for ti in sample_times:
        envelope = eq.effect_envelope(ti)
        state = eq.get_state(ti, intensity=0.7)
        print(f"{ti:<8.0f} {envelope:<10.2f} {state.time_dilation:<10.2f} {state.working_memory:<10.2f} "
              f"{state.sensory_enhancement:<10.2f} "
              f"{state.munchies_factor:<10.2f}")

    # Demonstrate thought derailment
    print("\n" + "="*70)
    print("THOUGHT DERAILMENT EXAMPLE")
    print("="*70)
    thoughts = eq.thought_derailment("I should order pizza", t=3, intensity=0.7)
    print("\nOriginal thought process:")
    for i, thought in enumerate(thoughts):
        print(f"  {i+1}. {thought}")

    plt.show()


if __name__ == "__main__":
    import scipy.ndimage

    print("🌿 Cannabis Perception Equation - Mathematical Model")
    print("=" * 70)
    print("\nThis models ACTUAL cannabis effects (not psychedelics):")
    print("  • Mild time dilation (1.2-1.5x, not extreme)")
    print("  • Working memory decay ('wait, what?')")
    print("  • Sensory enhancement (not hallucinations)")
    print("  • Thought tangents and derailment")
    print("  • Enhanced humor sensitivity")
    print("  • Motor delay and 'couch lock'")
    print("  • The munchies\n")

    demonstrate_weed_equation()

    print("\n✨ Demonstration complete!")
    print("\n💡 Toggle with: equation.toggle(True/False)")
