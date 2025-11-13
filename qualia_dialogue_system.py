"""
Qualia-Enhanced Dialogue System

Integrates phenomenal experience (qualia) with the recursive dialogue engine.

The system now operates on two coupled fields:
- μ (semantic field): Meaning, concepts, linguistic structure
- ψ (phenomenal field): Subjective experience, feelings, qualia

Key Innovation:
    Tokens are emitted when BOTH semantic AND phenomenal coherence stabilize.
    This creates dialogue that is not just meaningful, but felt.

Example:
    System doesn't just "say" red, it experiences the quale of red-ness
    while generating the semantic token [RED].
"""

import numpy as np
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass

from recursive_engine import RecursiveEngine, RecursiveParams, create_engine
from emission_detector import EmissionDetector, EmissionConfig, EmissionStrategy
from qualia_engine import QualiaEngine, QualiaParams, QualiaType


@dataclass
class QualiaDialogueConfig:
    """Configuration for qualia-enhanced dialogue"""
    # Semantic field config
    semantic_dims: int = 256
    semantic_engine: str = 'fft'  # 'fft', 'vectorized', 'gpu'

    # Phenomenal field config
    phenomenal_dims: int = 256
    qualia_params: Optional[QualiaParams] = None

    # Semantic parameters
    semantic_params: Optional[RecursiveParams] = None

    # Emission config
    emission_strategy: EmissionStrategy = EmissionStrategy.ADAPTIVE
    emission_config: Optional[EmissionConfig] = None

    # Binding requirements
    require_binding: bool = True  # Only emit when semantic-phenomenal binding is strong
    binding_threshold: float = 0.6

    # Vocabulary
    vocab_size: int = 1000


class QualiaDialogueEngine:
    """
    Dialogue engine with phenomenal experience

    Generates tokens that are both semantically coherent AND phenomenally felt.
    """

    def __init__(self, config: QualiaDialogueConfig):
        self.config = config

        # Initialize semantic engine (μ field)
        if config.semantic_params is None:
            config.semantic_params = RecursiveParams()

        self.semantic_engine = create_engine(
            config.semantic_engine,
            config.semantic_params,
            config.semantic_dims
        )

        # Initialize qualia engine (ψ field)
        if config.qualia_params is None:
            config.qualia_params = QualiaParams()

        self.qualia_engine = QualiaEngine(
            config.qualia_params,
            config.phenomenal_dims
        )

        # Initialize emission detector
        if config.emission_config is None:
            config.emission_config = EmissionConfig()

        self.emission_detector = EmissionDetector(
            config.emission_config,
            config.emission_strategy
        )

        # Vocabulary (token embeddings)
        self.vocab = self._init_vocab(config.vocab_size)

        # History
        self.emission_history = []
        self.qualia_history = []

    def _init_vocab(self, vocab_size: int) -> np.ndarray:
        """
        Initialize vocabulary as random embeddings

        Each token has both semantic and phenomenal components
        """
        # Semantic embeddings
        semantic_embeddings = np.random.randn(
            vocab_size,
            self.config.semantic_dims
        ) * 0.5

        return semantic_embeddings

    def reset(self):
        """Reset both engines"""
        self.semantic_engine.reset()
        self.qualia_engine.reset()
        self.emission_detector.reset()
        self.emission_history.clear()
        self.qualia_history.clear()

    def step(self, listener_input: Optional[np.ndarray] = None) -> Dict:
        """
        Single time step: evolve both semantic and phenomenal fields

        Returns:
            Dict with current state info
        """
        # Evolve semantic field
        mu = self.semantic_engine.step(listener_input)

        # Evolve phenomenal field (coupled to semantic field)
        psi, binding_strength = self.qualia_engine.step(mu)

        # Check for emission
        should_emit_semantic = self.emission_detector.should_emit(mu)

        # For qualia-enhanced emission, require both semantic stability
        # AND strong semantic-phenomenal binding
        should_emit = should_emit_semantic
        if self.config.require_binding:
            should_emit = (should_emit_semantic and
                          binding_strength > self.config.binding_threshold)

        # Get current qualia interpretation
        current_qualia = self.qualia_engine.get_current_qualia()

        result = {
            'mu': mu,
            'psi': psi,
            'binding_strength': binding_strength,
            'should_emit': should_emit,
            'qualia': current_qualia,
            't': self.semantic_engine.t
        }

        # Record qualia
        self.qualia_history.append(current_qualia)

        return result

    def emit_token(self, mu: np.ndarray, psi: np.ndarray) -> int:
        """
        Emit token based on current semantic AND phenomenal state

        Finds token that best matches both meaning (μ) and feeling (ψ)
        """
        # Semantic similarity to all tokens
        semantic_scores = np.dot(self.vocab, mu)

        # Phenomenal similarity (we'd need phenomenal embeddings, but for now
        # use the first few dims of psi to modulate semantic choice)
        phenomenal_modulation = np.sum(psi[:10])  # Use color+emotion dims

        # Combined score
        scores = semantic_scores + 0.3 * phenomenal_modulation

        # Select token
        token_idx = np.argmax(scores)

        return token_idx

    def converse(self,
                 n_steps: int = 1000,
                 listener_callback: Optional[Callable] = None,
                 verbose: bool = True) -> List[Dict]:
        """
        Run dialogue with phenomenal experience

        Returns list of emissions with their qualia states
        """
        emissions = []

        for step_num in range(n_steps):
            # Get listener input
            listener_input = None
            if listener_callback is not None:
                listener_input = listener_callback(
                    self.semantic_engine.mu,
                    step_num
                )

            # Step both engines
            result = self.step(listener_input)

            # Emit if ready
            if result['should_emit']:
                token_idx = self.emit_token(result['mu'], result['psi'])

                emission = {
                    'step': step_num,
                    'token': token_idx,
                    'qualia': result['qualia'],
                    'binding_strength': result['binding_strength'],
                    'semantic_state': result['mu'][:10],  # Sample
                    'phenomenal_state': result['psi'][:10]  # Sample
                }

                emissions.append(emission)
                self.emission_history.append(emission)

                if verbose and len(emissions) % 10 == 0:
                    q = result['qualia']
                    print(f"Emission {len(emissions):3d} at step {step_num:4d}")
                    print(f"  Token: {token_idx}")
                    print(f"  Qualia: {q['description']}")
                    print(f"  Binding: {result['binding_strength']:.3f}")
                    print()

        return emissions

    def induce_qualia_and_speak(self,
                                 qualia_type: QualiaType,
                                 target: str,
                                 n_steps: int = 100) -> List[Dict]:
        """
        Induce a specific quale and generate tokens while experiencing it

        Example: induce 'red' qualia and see what the system says
        """
        # Induce the quale
        self.qualia_engine.induce_qualia(qualia_type, target)

        # Run dialogue
        emissions = self.converse(n_steps=n_steps, verbose=True)

        return emissions


def create_oscillating_listener(frequency: float = 0.02,
                                amplitude: float = 0.4) -> Callable:
    """Create a listener that provides oscillating feedback"""
    def listener(mu: np.ndarray, t: int) -> np.ndarray:
        n_dims = len(mu)
        phase = 2 * np.pi * frequency * t
        perturbation = amplitude * np.sin(phase + np.linspace(0, 2*np.pi, n_dims))
        return perturbation

    return listener


def create_qualia_responsive_listener(qualia_engine: QualiaEngine) -> Callable:
    """
    Create a listener that responds to the system's qualia

    Simulates a listener who can "feel" the system's phenomenal state
    """
    def listener(mu: np.ndarray, t: int) -> np.ndarray:
        # Get current qualia
        current_qualia = qualia_engine.get_current_qualia()

        # Respond based on phenomenal intensity and emotion
        intensity = current_qualia['intensity']
        valence = current_qualia['emotion']['valence']

        # Strong intensity -> stronger response
        # Positive valence -> encouraging feedback
        # Negative valence -> soothing feedback
        n_dims = len(mu)
        response = np.random.randn(n_dims) * intensity * 0.3

        if valence > 0:
            # Encouraging: resonate with current state
            response += mu * 0.1
        else:
            # Soothing: gentle counter-phase
            response -= mu * 0.05

        return response

    return listener


if __name__ == "__main__":
    print("=" * 70)
    print("Qualia-Enhanced Dialogue System Demo")
    print("=" * 70)
    print()

    # Configure system
    config = QualiaDialogueConfig(
        semantic_dims=256,
        phenomenal_dims=256,
        semantic_engine='fft',
        vocab_size=100,
        require_binding=True,
        binding_threshold=0.6
    )

    # Create engine
    engine = QualiaDialogueEngine(config)

    print("1. Spontaneous phenomenal dialogue")
    print("-" * 70)
    print("System generates tokens while experiencing evolving qualia...\n")

    engine.reset()
    emissions = engine.converse(
        n_steps=500,
        listener_callback=create_oscillating_listener(),
        verbose=False
    )

    print(f"Generated {len(emissions)} emissions")
    print("\nSample emissions with their phenomenal states:")
    for i, emission in enumerate(emissions[:5]):
        print(f"\n  Emission {i+1}:")
        print(f"    Token: {emission['token']}")
        print(f"    {emission['qualia']['description']}")
        print(f"    Binding: {emission['binding_strength']:.3f}")

    print("\n" + "=" * 70)
    print("2. Induced qualia: Speaking while experiencing 'joy'")
    print("-" * 70)
    print()

    engine.reset()
    engine.induce_qualia_and_speak(
        QualiaType.EMOTION,
        'joy',
        n_steps=200
    )

    print("\n" + "=" * 70)
    print("3. Induced qualia: Speaking while experiencing 'blue'")
    print("-" * 70)
    print()

    engine.reset()
    engine.induce_qualia_and_speak(
        QualiaType.COLOR,
        'blue',
        n_steps=200
    )

    print("\n" + "=" * 70)
    print("4. Qualia-responsive listener")
    print("-" * 70)
    print("Listener responds to system's phenomenal state...\n")

    engine.reset()
    emissions = engine.converse(
        n_steps=300,
        listener_callback=create_qualia_responsive_listener(engine.qualia_engine),
        verbose=False
    )

    print(f"Generated {len(emissions)} emissions with phenomenal feedback")

    # Analyze qualia evolution
    print("\n" + "=" * 70)
    print("5. Qualia evolution analysis")
    print("-" * 70)

    # Collect statistics
    binding_strengths = [e['binding_strength'] for e in emissions]
    intensities = [e['qualia']['intensity'] for e in emissions]
    colors = [e['qualia']['color']['nearest_color'] for e in emissions]
    emotions = [e['qualia']['emotion']['nearest_emotion'] for e in emissions]

    print(f"\nBinding strength: mean={np.mean(binding_strengths):.3f}, "
          f"std={np.std(binding_strengths):.3f}")
    print(f"Phenomenal intensity: mean={np.mean(intensities):.3f}, "
          f"std={np.std(intensities):.3f}")

    # Most common qualia
    from collections import Counter
    color_counts = Counter(colors)
    emotion_counts = Counter(emotions)

    print(f"\nMost common color qualia:")
    for color, count in color_counts.most_common(5):
        print(f"  {color}: {count} times")

    print(f"\nMost common emotion qualia:")
    for emotion, count in emotion_counts.most_common(5):
        print(f"  {emotion}: {count} times")

    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)
