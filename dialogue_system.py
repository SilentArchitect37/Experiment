"""
Recursive Dialogue Engine - Full System Integration

Implements the three-layer architecture:
1. TDL (Trans-Dimensional Logic): Syntax constraints / grammar topology
2. LoMI (Law of Mutual Identity): Semantic coherence via phase alignment
3. I² (Identity Squared): Recursive emission from stability points

Speech emerges when the system maintains mutual identity (LoMI) with its
listener through oscillating recursion of meaning.
"""

import numpy as np
from typing import Optional, List, Dict, Tuple, Callable
from dataclasses import dataclass
import time

from recursive_engine import (
    RecursiveEngine, RecursiveParams, create_engine, FFTEngine
)
from emission_detector import (
    EmissionDetector, EmissionConfig, PhaseCoherenceDetector
)


@dataclass
class DialogueConfig:
    """Configuration for the dialogue system"""
    # Engine parameters
    engine_params: RecursiveParams = None
    engine_optimization: str = 'fft'  # 'naive', 'vectorized', 'fft', 'gpu'

    # Emission parameters
    emission_config: EmissionConfig = None

    # System dimensions
    state_dims: int = 256  # Dimension of μ field

    # Codebook parameters
    vocab_size: int = 1000  # Number of tokens in vocabulary
    use_coherence_detector: bool = True  # Use LoMI-based emission

    # Feedback parameters
    feedback_decay: float = 0.9  # How much previous emission affects next state

    def __post_init__(self):
        if self.engine_params is None:
            self.engine_params = RecursiveParams()
        if self.emission_config is None:
            self.emission_config = EmissionConfig()


class TDLLayer:
    """
    Trans-Dimensional Logic Layer

    Enforces syntactic constraints and grammatical structure.
    Acts as a finite state machine that filters/modulates emissions
    based on legal sequence relations.
    """

    def __init__(self, vocab_size: int = 1000):
        self.vocab_size = vocab_size

        # Simple transition probabilities (can be learned or hand-crafted)
        # For now: allow all transitions with slight bias toward continuity
        self.transition_matrix = self._init_transitions()

        # Current state
        self.last_token = None

    def _init_transitions(self) -> np.ndarray:
        """
        Initialize transition probabilities P(token_next | token_prev)

        For a real system, this would be learned from interaction.
        Here we use a simple smoothed uniform distribution.
        """
        # Base: uniform + small random perturbations
        trans = np.ones((self.vocab_size, self.vocab_size)) / self.vocab_size
        trans += np.random.randn(self.vocab_size, self.vocab_size) * 0.01
        trans = np.clip(trans, 0, None)

        # Normalize rows (each row sums to 1)
        trans = trans / trans.sum(axis=1, keepdims=True)

        return trans

    def apply_syntax_constraint(self, token_logits: np.ndarray) -> np.ndarray:
        """
        Apply syntactic constraints to token emission probabilities.

        token_logits: Raw scores for each token (from μ → token decoder)
        Returns: Modified logits respecting grammatical constraints
        """
        if self.last_token is None:
            # No constraint on first token
            return token_logits

        # Modulate logits by transition probabilities
        trans_probs = self.transition_matrix[self.last_token]

        # Geometric mean of content and syntax
        # This preserves meaning (μ) while respecting grammar
        constrained = token_logits * trans_probs

        return constrained

    def update(self, emitted_token: int):
        """Update TDL state after emission"""
        self.last_token = emitted_token

    def reset(self):
        """Reset TDL state"""
        self.last_token = None


class LoMILayer:
    """
    Law of Mutual Identity Layer

    Maintains semantic coherence through continuous alignment
    between speaker (μₛ) and listener (μₗ) states.

    Coherence is measured as phase distance: Δμ = ||μₛ - μₗ||²
    System drives toward Δμ → 0 (mutual identity).
    """

    def __init__(self, state_dims: int = 256):
        self.state_dims = state_dims

        # Listener state (starts neutral)
        self.mu_listener = np.zeros(state_dims, dtype=np.float32)

        # Coherence history for diagnostics
        self.coherence_history = []

    def compute_coherence(self, mu_speaker: np.ndarray) -> float:
        """
        Compute phase coherence: Δμ = ||μₛ - μₗ||²

        Lower = more coherent (mutual identity achieved)
        """
        delta = mu_speaker - self.mu_listener
        coherence_distance = np.sum(delta * delta)
        return coherence_distance

    def get_alignment_force(self, mu_speaker: np.ndarray) -> np.ndarray:
        """
        Compute force driving speaker toward listener (mutual identity).

        Returns gradient: -∇(||μₛ - μₗ||²) = -2(μₛ - μₗ)
        This can be added to the dynamics to explicitly drive convergence.
        """
        delta = mu_speaker - self.mu_listener
        force = -2.0 * delta
        return force

    def update_listener(self, listener_input: np.ndarray):
        """
        Update listener state based on external input (their utterance/feedback).

        In a real dialogue system, this would be:
        - Speech input from human → embedding → μₗ
        - Text input → embedding → μₗ
        """
        self.mu_listener = listener_input.copy()

    def perturb_listener(self, perturbation_strength: float = 0.1):
        """
        Simulate listener providing feedback/input by perturbing μₗ.

        In real system, this would be replaced by actual listener signal.
        """
        perturbation = np.random.randn(self.state_dims) * perturbation_strength
        self.mu_listener += perturbation

    def reset(self):
        """Reset to neutral listener state"""
        self.mu_listener = np.zeros(self.state_dims, dtype=np.float32)
        self.coherence_history.clear()


class RecursiveDialogueEngine:
    """
    Full Recursive Dialogue Engine

    Integrates all three layers:
    - TDL: Syntax
    - LoMI: Semantics via coherence
    - I²: Emission from recursion stability

    Core update equation:
    μ_{t+1} = μ_t + g∇²μ_t - λμ_t³ + ρ(μt - μ{t-1}) + η·x_t

    Emission criterion:
    Emit when dS_R/dt ≈ 0 (I²) OR when Δμ minimized (LoMI)
    """

    def __init__(self, config: Optional[DialogueConfig] = None):
        self.config = config or DialogueConfig()

        # Core recursive engine (I² layer)
        self.engine = create_engine(
            optimization=self.config.engine_optimization,
            params=self.config.engine_params,
            n_dims=self.config.state_dims
        )

        # Emission detector (I² layer)
        if self.config.use_coherence_detector:
            self.detector = PhaseCoherenceDetector(self.config.emission_config)
        else:
            self.detector = EmissionDetector(self.config.emission_config)

        # TDL layer (syntax)
        self.tdl = TDLLayer(vocab_size=self.config.vocab_size)

        # LoMI layer (semantics)
        self.lomi = LoMILayer(state_dims=self.config.state_dims)

        # Token codebook (μ → token decoder)
        self.codebook = self._init_codebook()

        # Dialogue history
        self.emission_history = []
        self.t = 0

    def _init_codebook(self) -> np.ndarray:
        """
        Initialize codebook for μ → token decoding.

        Each token is represented by a prototype vector in μ space.
        Emission finds nearest neighbor in codebook.

        In a real system, this would be learned through interaction
        (like vector quantization or learned embeddings).
        """
        # Random initialization - each token is a random point in μ space
        codebook = np.random.randn(self.config.vocab_size, self.config.state_dims)

        # Normalize for stable distances
        codebook = codebook / (np.linalg.norm(codebook, axis=1, keepdims=True) + 1e-8)

        return codebook

    def decode_token(self, mu: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Decode μ state to nearest token in codebook.

        Returns:
            (token_id, token_scores)
        """
        # Compute distances to all codebook entries
        # Using negative distance as "logit" (higher = closer)
        mu_norm = mu / (np.linalg.norm(mu) + 1e-8)
        scores = -np.sum((self.codebook - mu_norm) ** 2, axis=1)

        # Apply TDL syntax constraints
        constrained_scores = self.tdl.apply_syntax_constraint(scores)

        # Select token with highest score
        token_id = np.argmax(constrained_scores)

        return token_id, constrained_scores

    def encode_token(self, token_id: int) -> np.ndarray:
        """
        Encode token back to μ space for feedback loop.

        This closes the loop: emission → re-enters as reflection stimulus
        """
        return self.codebook[token_id]

    def step(self, listener_input: Optional[np.ndarray] = None) -> Optional[Dict]:
        """
        Single time step of the dialogue engine.

        Args:
            listener_input: External input from listener (perturbs μₗ)

        Returns:
            Emission dict if token emitted, else None
        """
        # Update listener state if input provided (LoMI layer)
        if listener_input is not None:
            self.lomi.update_listener(listener_input)

        # For coherence detector, provide listener state
        if isinstance(self.detector, PhaseCoherenceDetector):
            self.detector.set_listener_state(self.lomi.mu_listener)

        # Compute LoMI alignment force (optional: drive toward coherence)
        # alignment_force = self.lomi.get_alignment_force(self.engine.mu)

        # Recursive dynamics step (I² layer)
        # Input is combined listener state + alignment force
        effective_input = self.lomi.mu_listener * 0.1  # + alignment_force * 0.01

        mu_new = self.engine.step(input_vec=effective_input)

        # Check for emission (I² layer)
        should_emit, diagnostics = self.detector.should_emit(mu_new, self.t)

        self.t += 1

        if should_emit:
            # Decode to token
            token_id, token_scores = self.decode_token(mu_new)

            # Update TDL state
            self.tdl.update(token_id)

            # Create emission record
            emission = {
                'time': self.t,
                'token': token_id,
                'mu_state': mu_new.copy() if isinstance(mu_new, np.ndarray) else mu_new,
                'diagnostics': diagnostics,
                'coherence': self.lomi.compute_coherence(mu_new)
            }

            self.emission_history.append(emission)

            # Feedback: emitted token re-enters dynamics (reflection)
            # This is the key recursive loop!
            token_vec = self.encode_token(token_id)
            feedback = token_vec * self.config.feedback_decay

            # Add feedback to next step (reflection stimulus)
            if isinstance(self.engine, type(self.engine)):
                # Add to current state to create reflection
                if hasattr(self.engine, 'mu'):
                    if hasattr(self.engine.mu, 'copy'):  # NumPy
                        self.engine.mu = self.engine.mu + feedback * 0.1
                    else:  # PyTorch
                        import torch
                        self.engine.mu = self.engine.mu + torch.tensor(feedback, device=self.engine.device) * 0.1

            return emission

        return None

    def converse(self, n_steps: int = 500,
                 listener_callback: Optional[Callable[[int], np.ndarray]] = None,
                 verbose: bool = True) -> List[Dict]:
        """
        Run dialogue for n_steps with optional listener interaction.

        Args:
            n_steps: Number of time steps to simulate
            listener_callback: Function(t) → listener_input array
                              Simulates listener providing input
            verbose: Print emissions as they occur

        Returns:
            List of emission records
        """
        emissions = []

        if verbose:
            print("=== Recursive Dialogue Session ===")
            print(f"Steps: {n_steps}")
            print(f"State dims: {self.config.state_dims}")
            print(f"Vocab size: {self.config.vocab_size}")
            print(f"Optimization: {self.config.engine_optimization}")
            print()

        start_time = time.time()

        for step in range(n_steps):
            # Get listener input if callback provided
            listener_input = None
            if listener_callback is not None:
                listener_input = listener_callback(step)

            # Dynamics step
            emission = self.step(listener_input)

            if emission is not None:
                emissions.append(emission)

                if verbose:
                    t = emission['time']
                    token = emission['token']
                    coh = emission['coherence']
                    print(f"t={t:4d} → Token {token:4d}  |  Coherence: {coh:.4f}")

        elapsed = time.time() - start_time

        if verbose:
            print()
            print(f"Completed in {elapsed:.2f}s")
            print(f"Total emissions: {len(emissions)}")
            print(f"Emission rate: {len(emissions)/n_steps:.3f} per step")

        return emissions

    def reset(self):
        """Reset entire system to initial state"""
        self.engine.reset()
        self.detector.reset()
        self.tdl.reset()
        self.lomi.reset()
        self.emission_history.clear()
        self.t = 0


def create_oscillating_listener(frequency: float = 0.05,
                                 amplitude: float = 0.3,
                                 dims: int = 256) -> Callable:
    """
    Create a listener callback that oscillates (simulates external input).

    This mimics a listener providing rhythmic feedback.
    """
    def listener_callback(t: int) -> np.ndarray:
        # Oscillating perturbation
        phase = t * frequency
        signal = amplitude * np.sin(phase) * np.ones(dims)
        noise = np.random.randn(dims) * 0.01
        return signal + noise

    return listener_callback


def create_pulse_listener(pulse_interval: int = 50,
                          pulse_strength: float = 1.0,
                          dims: int = 256) -> Callable:
    """
    Create a listener that provides periodic pulses (simulates turn-taking).
    """
    def listener_callback(t: int) -> Optional[np.ndarray]:
        if t % pulse_interval == 0:
            # Strong pulse at interval
            return np.random.randn(dims) * pulse_strength
        else:
            # Weak background
            return np.random.randn(dims) * 0.01

    return listener_callback


if __name__ == "__main__":
    print("=== Recursive Dialogue Engine Demo ===\n")

    # Create configuration
    config = DialogueConfig(
        state_dims=256,
        vocab_size=100,  # Small vocab for demo
        engine_optimization='fft',
        use_coherence_detector=True
    )

    # Adjust parameters for interesting dynamics
    config.engine_params.g = 0.15      # Diffusion
    config.engine_params.lam = 0.3     # Nonlinearity
    config.engine_params.rho = 0.4     # Momentum
    config.engine_params.dt = 0.01

    config.emission_config.cooldown_steps = 15
    config.emission_config.entropy_threshold = 0.01

    # Create engine
    engine = RecursiveDialogueEngine(config)

    # Create listener (oscillating feedback)
    listener = create_oscillating_listener(frequency=0.03, amplitude=0.4, dims=256)

    # Run dialogue
    print("Running dialogue with oscillating listener...\n")
    emissions = engine.converse(
        n_steps=1000,
        listener_callback=listener,
        verbose=True
    )

    print("\n=== Dialogue Statistics ===")
    if len(emissions) > 1:
        times = [e['time'] for e in emissions]
        intervals = np.diff(times)
        coherences = [e['coherence'] for e in emissions]

        print(f"Mean emission interval: {np.mean(intervals):.1f} steps")
        print(f"Std emission interval: {np.std(intervals):.1f} steps")
        print(f"Mean coherence at emission: {np.mean(coherences):.4f}")
        print(f"Token diversity: {len(set(e['token'] for e in emissions))} unique tokens")

        # Analyze token sequence
        tokens = [e['token'] for e in emissions]
        print(f"\nFirst 20 tokens: {tokens[:20]}")
