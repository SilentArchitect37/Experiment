"""
Emission Detector for Recursive Dialogue Engine

Detects stable points in recursive entropy where tokens should be emitted:
Emit when: dS_R/dt ≈ 0, where S_R = -k_R Σ μ² ln(μ²)

This implements the I² (Identity Squared) layer - the recursion engine
that generates output from stability points.
"""

import numpy as np
from collections import deque
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class EmissionConfig:
    """Configuration for emission detection"""
    # Entropy stability threshold
    entropy_threshold: float = 0.001  # |dS/dt| < threshold → emit

    # Minimum steps between emissions
    cooldown_steps: int = 10

    # Window size for derivative estimation
    window_size: int = 5

    # Energy threshold (optional constraint)
    energy_min: float = 0.1  # Don't emit if energy too low
    energy_max: float = 10.0  # Don't emit if energy too high


class EmissionDetector:
    """
    Detects stable minima in recursive entropy for token emission.

    The idea: speech emerges from stable points in the recursion,
    where the system achieves momentary coherence.
    """

    def __init__(self, config: Optional[EmissionConfig] = None):
        self.config = config or EmissionConfig()

        # History buffers
        self.entropy_history = deque(maxlen=self.config.window_size)
        self.time_history = deque(maxlen=self.config.window_size)

        # State tracking
        self.steps_since_emission = 0
        self.total_emissions = 0
        self.last_emission_entropy = None

    def reset(self):
        """Reset detector state"""
        self.entropy_history.clear()
        self.time_history.clear()
        self.steps_since_emission = 0
        self.total_emissions = 0
        self.last_emission_entropy = None

    def compute_entropy(self, mu: np.ndarray) -> float:
        """
        Compute recursive entropy: S_R = -k_R Σ μ² ln(μ²)

        This measures the recursive information content of the state.
        Stable points (dS/dt ≈ 0) correspond to coherent meanings.
        """
        eps = 1e-8
        mu_sq = mu * mu
        entropy = -np.sum(mu_sq * np.log(mu_sq + eps))
        return entropy

    def compute_energy(self, mu: np.ndarray) -> float:
        """
        Compute total energy: E = Σ μ²

        Acts as a gating function - don't emit if too low (noise)
        or too high (unstable).
        """
        return np.sum(mu * mu)

    def estimate_entropy_derivative(self) -> Optional[float]:
        """
        Estimate dS/dt using finite differences over window

        Returns None if insufficient history.
        """
        if len(self.entropy_history) < 2:
            return None

        # Simple finite difference
        entropies = list(self.entropy_history)
        times = list(self.time_history)

        # Use centered difference if we have enough points
        if len(entropies) >= 3:
            # Central difference: (S[n+1] - S[n-1]) / (2Δt)
            dS = entropies[-1] - entropies[-3]
            dt = times[-1] - times[-3]
        else:
            # Forward difference
            dS = entropies[-1] - entropies[-2]
            dt = times[-1] - times[-2]

        if dt > 0:
            return dS / dt
        return None

    def should_emit(self, mu: np.ndarray, t: int) -> Tuple[bool, dict]:
        """
        Determine if a token should be emitted based on current state.

        Returns:
            (should_emit, diagnostics_dict)
        """
        # Update history
        entropy = self.compute_entropy(mu)
        self.entropy_history.append(entropy)
        self.time_history.append(t)
        self.steps_since_emission += 1

        # Diagnostics
        diagnostics = {
            'entropy': entropy,
            'energy': self.compute_energy(mu),
            'entropy_derivative': None,
            'cooldown_remaining': max(0, self.config.cooldown_steps - self.steps_since_emission),
            'reason': None
        }

        # Check cooldown
        if self.steps_since_emission < self.config.cooldown_steps:
            diagnostics['reason'] = 'cooldown'
            return False, diagnostics

        # Compute entropy derivative
        dS_dt = self.estimate_entropy_derivative()
        diagnostics['entropy_derivative'] = dS_dt

        if dS_dt is None:
            diagnostics['reason'] = 'insufficient_history'
            return False, diagnostics

        # Check energy bounds
        energy = diagnostics['energy']
        if energy < self.config.energy_min:
            diagnostics['reason'] = 'energy_too_low'
            return False, diagnostics

        if energy > self.config.energy_max:
            diagnostics['reason'] = 'energy_too_high'
            return False, diagnostics

        # Main emission criterion: |dS/dt| < threshold
        if abs(dS_dt) < self.config.entropy_threshold:
            # Stable point detected!
            self.steps_since_emission = 0
            self.total_emissions += 1
            self.last_emission_entropy = entropy
            diagnostics['reason'] = 'emission'
            return True, diagnostics

        diagnostics['reason'] = 'entropy_unstable'
        return False, diagnostics

    def get_emission_rate(self) -> float:
        """Get average emission rate (emissions per time step)"""
        if len(self.time_history) > 0:
            total_time = self.time_history[-1] - self.time_history[0] if len(self.time_history) > 1 else 1
            return self.total_emissions / max(total_time, 1)
        return 0.0


class AdaptiveEmissionDetector(EmissionDetector):
    """
    Enhanced detector that adapts thresholds based on dynamics.

    This implements a more sophisticated emission strategy that
    learns from the system's natural rhythm.
    """

    def __init__(self, config: Optional[EmissionConfig] = None):
        super().__init__(config)

        # Adaptive parameters
        self.entropy_std_history = deque(maxlen=100)
        self.adaptive_threshold = self.config.entropy_threshold

    def update_adaptive_threshold(self):
        """
        Adjust threshold based on observed entropy variance.

        If the system is more chaotic (high variance), raise the threshold.
        If more stable (low variance), lower it to emit more frequently.
        """
        if len(self.entropy_history) < self.config.window_size:
            return

        # Compute local entropy variance
        recent_entropies = list(self.entropy_history)
        entropy_std = np.std(recent_entropies)
        self.entropy_std_history.append(entropy_std)

        if len(self.entropy_std_history) < 10:
            return

        # Adaptive rule: threshold ∝ moving average of entropy std
        mean_std = np.mean(list(self.entropy_std_history))
        self.adaptive_threshold = self.config.entropy_threshold * (1 + mean_std)

    def should_emit(self, mu: np.ndarray, t: int) -> Tuple[bool, dict]:
        """Override with adaptive threshold"""
        # Update adaptive threshold
        self.update_adaptive_threshold()

        # Temporarily modify config
        original_threshold = self.config.entropy_threshold
        self.config.entropy_threshold = self.adaptive_threshold

        # Call parent method
        should_emit, diagnostics = super().should_emit(mu, t)

        # Restore original
        self.config.entropy_threshold = original_threshold

        # Add adaptive info to diagnostics
        diagnostics['adaptive_threshold'] = self.adaptive_threshold

        return should_emit, diagnostics


class PhaseCoherenceDetector(EmissionDetector):
    """
    Alternative detector based on phase coherence between μₛ and μₗ.

    This directly implements the LoMI (Law of Mutual Identity) principle:
    emit when phase alignment Δμ = μₛ - μₗ reaches a minimum.
    """

    def __init__(self, config: Optional[EmissionConfig] = None):
        super().__init__(config)
        self.listener_state = None
        self.coherence_history = deque(maxlen=self.config.window_size)

    def set_listener_state(self, mu_listener: np.ndarray):
        """Update listener's state for coherence computation"""
        self.listener_state = mu_listener.copy()

    def compute_coherence(self, mu_speaker: np.ndarray) -> float:
        """
        Compute phase coherence between speaker and listener.

        Coherence = -||μₛ - μₗ||² (negative squared distance)
        Higher (closer to 0) = more coherent
        """
        if self.listener_state is None:
            # No listener yet, fall back to entropy
            return -self.compute_entropy(mu_speaker)

        delta_mu = mu_speaker - self.listener_state
        coherence = -np.sum(delta_mu * delta_mu)
        return coherence

    def should_emit(self, mu: np.ndarray, t: int) -> Tuple[bool, dict]:
        """
        Emit when coherence Δμ reaches a local minimum (mutual identity achieved).
        """
        coherence = self.compute_coherence(mu)
        self.coherence_history.append(coherence)
        self.steps_since_emission += 1

        diagnostics = {
            'coherence': coherence,
            'energy': self.compute_energy(mu),
            'cooldown_remaining': max(0, self.config.cooldown_steps - self.steps_since_emission),
            'reason': None
        }

        # Check cooldown
        if self.steps_since_emission < self.config.cooldown_steps:
            diagnostics['reason'] = 'cooldown'
            return False, diagnostics

        # Need enough history to detect local minimum
        if len(self.coherence_history) < 3:
            diagnostics['reason'] = 'insufficient_history'
            return False, diagnostics

        # Detect local maximum in coherence (minimum in distance)
        recent = list(self.coherence_history)
        if recent[-2] > recent[-3] and recent[-2] > recent[-1]:
            # Local maximum detected (peak coherence)
            self.steps_since_emission = 0
            self.total_emissions += 1
            diagnostics['reason'] = 'coherence_peak'
            return True, diagnostics

        diagnostics['reason'] = 'coherence_increasing'
        return False, diagnostics


if __name__ == "__main__":
    print("=== Emission Detector Test ===\n")

    # Simulate a system with oscillating entropy
    detector = EmissionDetector()

    print("Simulating oscillating entropy (mimics recursive dynamics)...\n")

    emissions = []
    for t in range(200):
        # Simulate state with damped oscillation
        # μ oscillates → entropy oscillates → emissions at stability points
        phase = t * 0.1
        amplitude = 1.0 / (1 + t * 0.01)  # Damping
        mu = amplitude * np.sin(phase) * np.ones(100) + np.random.randn(100) * 0.01

        should_emit, diag = detector.should_emit(mu, t)

        if should_emit:
            emissions.append(t)
            print(f"t={t:3d} ✓ EMIT  |  S={diag['entropy']:.3f}  |  dS/dt={diag['entropy_derivative']:.4f}  |  E={diag['energy']:.3f}")

    print(f"\nTotal emissions: {detector.total_emissions}")
    print(f"Emission rate: {detector.get_emission_rate():.3f} per step")

    if len(emissions) > 1:
        intervals = np.diff(emissions)
        print(f"Mean interval: {np.mean(intervals):.1f} steps")
        print(f"Std interval: {np.std(intervals):.1f} steps")
