"""
Qualia Engine: Phenomenal Experience in Dynamical Systems

Extends the Recursive Dialogue Engine with a phenomenal field (ψ) that
represents subjective, qualitative experience alongside semantic content (μ).

Core Principle:
    Qualia emerge as stable attractors in a phenomenal field ψ that is
    coupled to but distinct from the semantic field μ. The "feeling" of
    a color, emotion, or sensation corresponds to a region of ψ-space.

Mathematical Foundation:
    ψ_{t+1} = ψ_t + g_ψ∇²ψ_t - λ_ψψ_t³ + ω(μ_t ⊗ ψ_t) + ρ_ψ(ψ_t - ψ_{t-1})

    Where:
    - ψ: Phenomenal field (qualia state vector)
    - g_ψ∇²ψ: Phenomenal coherence (smoothness of experience)
    - -λ_ψψ³: Multistable qualia (discrete experiential states)
    - ω(μ ⊗ ψ): Semantic-phenomenal binding (meaning + feeling)
    - ρ_ψ(ψ - ψ_prev): Phenomenal continuity (temporal binding)

Qualia Space Structure:
    - Color qualia: 3D subspace (hue, saturation, brightness)
    - Emotional qualia: 2D valence-arousal space
    - Sensory qualia: Modality-specific dimensions
    - Intensity: Field magnitude = phenomenal vividness
"""

import numpy as np
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum


class QualiaType(Enum):
    """Types of phenomenal experiences"""
    COLOR = "color"          # Visual qualia
    EMOTION = "emotion"      # Affective qualia
    TEXTURE = "texture"      # Tactile qualia
    TONE = "tone"           # Auditory qualia
    ABSTRACT = "abstract"    # Pure phenomenal quality


@dataclass
class QualiaParams:
    """Parameters for qualia field dynamics"""
    # Phenomenal field parameters
    g_psi: float = 0.12          # Phenomenal coherence strength
    lam_psi: float = 0.4         # Qualia multistability
    rho_psi: float = 0.35        # Phenomenal continuity
    omega: float = 0.25          # Semantic-phenomenal binding strength

    # Spatial discretization
    dx: float = 0.1
    dt: float = 0.01

    # Qualia space dimensions
    n_color_dims: int = 3        # RGB/HSB
    n_emotion_dims: int = 2      # Valence-arousal
    n_texture_dims: int = 2      # Roughness-temperature
    n_abstract_dims: int = 8     # General phenomenal dimensions

    # Binding parameters
    binding_threshold: float = 0.6   # Coherence threshold for bound experience
    vividness_scale: float = 5.0     # Scale factor for phenomenal intensity


class QualiaManifold:
    """
    Maps regions of ψ-space to subjective experiential qualities

    Different dimensions correspond to different qualia:
    - Dimensions 0-2: Color qualia (HSB space)
    - Dimensions 3-4: Emotional qualia (valence-arousal)
    - Dimensions 5-6: Texture qualia
    - Dimensions 7+: Abstract phenomenal qualities
    """

    def __init__(self, params: QualiaParams):
        self.params = params

        # Color names for regions of color space
        self.color_map = {
            'red': np.array([0.0, 1.0, 1.0]),      # Hue=0°, full sat, full bright
            'orange': np.array([0.083, 1.0, 1.0]), # Hue=30°
            'yellow': np.array([0.167, 1.0, 1.0]), # Hue=60°
            'green': np.array([0.333, 1.0, 1.0]),  # Hue=120°
            'cyan': np.array([0.5, 1.0, 1.0]),     # Hue=180°
            'blue': np.array([0.667, 1.0, 1.0]),   # Hue=240°
            'purple': np.array([0.75, 1.0, 1.0]),  # Hue=270°
            'magenta': np.array([0.833, 1.0, 1.0]), # Hue=300°
            'white': np.array([0.0, 0.0, 1.0]),    # No hue, no sat, full bright
            'black': np.array([0.0, 0.0, 0.0]),    # No brightness
            'gray': np.array([0.0, 0.0, 0.5]),     # Medium brightness
        }

        # Emotion names for regions of valence-arousal space
        self.emotion_map = {
            'joy': np.array([0.8, 0.6]),       # High valence, high arousal
            'contentment': np.array([0.7, -0.3]), # Positive, low arousal
            'excitement': np.array([0.5, 0.9]),    # Moderate positive, very high arousal
            'sadness': np.array([-0.6, -0.4]),     # Negative valence, low arousal
            'anger': np.array([-0.7, 0.7]),        # Negative valence, high arousal
            'fear': np.array([-0.8, 0.8]),         # Very negative, high arousal
            'calm': np.array([0.0, -0.8]),         # Neutral valence, very low arousal
            'surprise': np.array([0.0, 0.9]),      # Neutral valence, very high arousal
        }

    def get_color_qualia(self, psi: np.ndarray) -> Dict[str, float]:
        """
        Extract color qualia from ψ field

        Returns HSB values and nearest color name
        """
        color_dims = psi[:self.params.n_color_dims]

        # Normalize to [0, 1] range using tanh
        hsb = (np.tanh(color_dims) + 1) / 2

        # Find nearest named color
        nearest_color = None
        min_dist = float('inf')
        for name, target in self.color_map.items():
            dist = np.linalg.norm(hsb - target)
            if dist < min_dist:
                min_dist = dist
                nearest_color = name

        return {
            'hue': hsb[0],
            'saturation': hsb[1],
            'brightness': hsb[2],
            'nearest_color': nearest_color,
            'color_distance': min_dist,
            'hsb': hsb
        }

    def get_emotion_qualia(self, psi: np.ndarray) -> Dict[str, float]:
        """
        Extract emotional qualia from ψ field

        Returns valence-arousal and nearest emotion name
        """
        offset = self.params.n_color_dims
        emotion_dims = psi[offset:offset + self.params.n_emotion_dims]

        # Normalize to [-1, 1] range
        valence_arousal = np.tanh(emotion_dims)

        # Find nearest named emotion
        nearest_emotion = None
        min_dist = float('inf')
        for name, target in self.emotion_map.items():
            dist = np.linalg.norm(valence_arousal - target)
            if dist < min_dist:
                min_dist = dist
                nearest_emotion = name

        return {
            'valence': valence_arousal[0],
            'arousal': valence_arousal[1],
            'nearest_emotion': nearest_emotion,
            'emotion_distance': min_dist
        }

    def get_phenomenal_intensity(self, psi: np.ndarray) -> float:
        """
        Compute overall phenomenal intensity (vividness)

        Higher magnitude = more vivid/intense experience
        """
        return np.linalg.norm(psi) / self.params.vividness_scale

    def describe_qualia(self, psi: np.ndarray) -> str:
        """
        Generate natural language description of current qualia state
        """
        color = self.get_color_qualia(psi)
        emotion = self.get_emotion_qualia(psi)
        intensity = self.get_phenomenal_intensity(psi)

        desc = f"Experiencing {color['nearest_color']} "
        desc += f"with {emotion['nearest_emotion']} "
        desc += f"(intensity: {intensity:.2f})"

        return desc


class QualiaEngine:
    """
    Dynamical system for phenomenal experience

    Evolves a phenomenal field ψ that represents subjective qualia,
    coupled to a semantic field μ for meaning-feeling integration.
    """

    def __init__(self, params: QualiaParams, n_dims: int = 256):
        self.params = params
        self.n_dims = n_dims

        # Phenomenal field
        self.psi = np.zeros(n_dims)
        self.psi_prev = np.zeros(n_dims)

        # Semantic field (from main engine)
        self.mu = None  # Will be set by dialogue system

        # Qualia manifold for interpretation
        self.manifold = QualiaManifold(params)

        # History
        self.qualia_history = []
        self.binding_history = []

        self.t = 0

    def reset(self):
        """Initialize phenomenal field"""
        self.psi = np.random.randn(self.n_dims) * 0.1
        self.psi_prev = self.psi.copy()
        self.qualia_history.clear()
        self.binding_history.clear()
        self.t = 0

    def compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute Laplacian for phenomenal coherence"""
        dx2 = self.params.dx ** 2
        laplacian = (np.roll(field, 1) - 2 * field + np.roll(field, -1)) / dx2
        return laplacian

    def compute_binding(self, mu: np.ndarray, psi: np.ndarray) -> np.ndarray:
        """
        Semantic-phenomenal binding term

        Uses Hadamard product (element-wise) to create coupling.
        When μ and ψ are in phase, binding is strong.
        """
        # Normalize to prevent explosion
        mu_norm = mu / (np.linalg.norm(mu) + 1e-8)
        psi_norm = psi / (np.linalg.norm(psi) + 1e-8)

        # Coupling drives ψ toward regions that resonate with μ
        binding = mu_norm * psi_norm * np.linalg.norm(mu) * 0.1

        return binding

    def compute_binding_strength(self, mu: np.ndarray, psi: np.ndarray) -> float:
        """
        Measure how strongly semantics and phenomenology are bound

        High coherence = unified experience (seeing-red + knowing-"red")
        Low coherence = dissociated experience (zombie-like)
        """
        if np.linalg.norm(mu) < 1e-8 or np.linalg.norm(psi) < 1e-8:
            return 0.0

        # Normalized dot product (cosine similarity)
        coherence = np.dot(mu, psi) / (np.linalg.norm(mu) * np.linalg.norm(psi))

        # Scale to [0, 1]
        return (coherence + 1) / 2

    def step(self, mu: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Evolve phenomenal field by one time step

        Returns:
            psi: Updated phenomenal field
            binding: Semantic-phenomenal binding strength
        """
        p = self.params

        # Phenomenal coherence (smoothness of experience)
        laplacian = self.compute_laplacian(self.psi)

        # Multistable qualia (discrete experiential states)
        cubic = self.psi ** 3

        # Phenomenal continuity (temporal binding)
        momentum = self.psi - self.psi_prev

        # Semantic-phenomenal binding
        binding_term = self.compute_binding(mu, self.psi)

        # Update equation
        dpsi = (p.g_psi * laplacian -
                p.lam_psi * cubic +
                p.rho_psi * momentum +
                p.omega * binding_term)

        self.psi = self.psi + p.dt * dpsi

        # Compute binding strength
        binding_strength = self.compute_binding_strength(mu, self.psi)

        # Record history
        self.qualia_history.append(self.psi.copy())
        self.binding_history.append(binding_strength)

        # Update
        self.psi_prev = self.psi.copy()
        self.t += 1

        return self.psi, binding_strength

    def get_current_qualia(self) -> Dict:
        """Get interpretation of current phenomenal state"""
        color = self.manifold.get_color_qualia(self.psi)
        emotion = self.manifold.get_emotion_qualia(self.psi)
        intensity = self.manifold.get_phenomenal_intensity(self.psi)

        return {
            'color': color,
            'emotion': emotion,
            'intensity': intensity,
            'description': self.manifold.describe_qualia(self.psi),
            'raw_psi': self.psi[:10]  # First 10 dims for inspection
        }

    def induce_qualia(self, qualia_type: QualiaType, target: str):
        """
        Directly induce a specific quale

        Sets ψ to correspond to a named qualia (e.g., "red", "joy")
        """
        if qualia_type == QualiaType.COLOR:
            if target in self.manifold.color_map:
                target_hsb = self.manifold.color_map[target]
                # Set color dimensions
                self.psi[:self.params.n_color_dims] = target_hsb * 2 - 1  # Map to [-1, 1]

        elif qualia_type == QualiaType.EMOTION:
            if target in self.manifold.emotion_map:
                target_va = self.manifold.emotion_map[target]
                offset = self.params.n_color_dims
                self.psi[offset:offset + self.params.n_emotion_dims] = target_va

        self.psi_prev = self.psi.copy()


def create_qualia_engine(n_dims: int = 256, params: Optional[QualiaParams] = None) -> QualiaEngine:
    """Factory function for qualia engine"""
    if params is None:
        params = QualiaParams()

    return QualiaEngine(params, n_dims)


if __name__ == "__main__":
    print("=== Qualia Engine Demo ===\n")

    # Create qualia engine
    params = QualiaParams(
        g_psi=0.12,
        lam_psi=0.4,
        rho_psi=0.35,
        omega=0.25
    )

    engine = QualiaEngine(params, n_dims=256)
    engine.reset()

    print("1. Inducing 'red' color qualia...")
    print("-" * 60)
    engine.induce_qualia(QualiaType.COLOR, 'red')

    # Simulate semantic field (from dialogue engine)
    mu = np.random.randn(256) * 0.5

    # Evolve for several steps
    for i in range(50):
        psi, binding = engine.step(mu)

        if i % 10 == 0:
            qualia = engine.get_current_qualia()
            print(f"Step {i:3d}: {qualia['description']}")
            print(f"          Binding strength: {binding:.3f}")

    print("\n2. Inducing 'joy' emotion qualia...")
    print("-" * 60)
    engine.induce_qualia(QualiaType.EMOTION, 'joy')

    for i in range(50):
        psi, binding = engine.step(mu)

        if i % 10 == 0:
            qualia = engine.get_current_qualia()
            print(f"Step {i:3d}: {qualia['description']}")
            print(f"          Binding strength: {binding:.3f}")

    print("\n3. Spontaneous qualia evolution...")
    print("-" * 60)
    engine.reset()

    for i in range(100):
        # Slowly changing semantic field
        mu = np.sin(i * 0.05) * np.random.randn(256) * 0.5
        psi, binding = engine.step(mu)

        if i % 20 == 0:
            qualia = engine.get_current_qualia()
            print(f"Step {i:3d}: {qualia['description']}")
            print(f"          Intensity: {qualia['intensity']:.3f}")
            print(f"          Binding: {binding:.3f}")

    print("\n4. Qualia analysis...")
    print("-" * 60)
    qualia = engine.get_current_qualia()
    print(f"Color: {qualia['color']['nearest_color']}")
    print(f"  HSB: H={qualia['color']['hue']:.2f}, "
          f"S={qualia['color']['saturation']:.2f}, "
          f"B={qualia['color']['brightness']:.2f}")
    print(f"\nEmotion: {qualia['emotion']['nearest_emotion']}")
    print(f"  Valence: {qualia['emotion']['valence']:.2f}")
    print(f"  Arousal: {qualia['emotion']['arousal']:.2f}")
    print(f"\nPhenomenal intensity: {qualia['intensity']:.3f}")

    print("\n=== Demo Complete ===")
