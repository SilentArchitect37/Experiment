"""
CORAL: Compositional Oscillatory Recursive Associative Language System

A novel architecture for language synthesis that supersedes transformers through:
1. Sparse Distributed Representations (SDRs)
2. Hyperdimensional Computing operations
3. Modern Hopfield associative memory
4. Construction-based form-meaning pairs
5. Hierarchical predictive processing
6. Self-organizing dynamics

Core Design Principles:
- Works with minimal or no training data
- Learns patterns incrementally
- Maintains unlimited context through episodic memory
- Self-organizes structure from interaction
"""

import numpy as np
from typing import Optional, List, Dict, Tuple, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
from abc import ABC, abstractmethod


# =============================================================================
# Part 1: Sparse Distributed Representations (SDR)
# =============================================================================

@dataclass
class SDRConfig:
    """Configuration for Sparse Distributed Representations"""
    n_bits: int = 16384          # Total dimensionality (128 x 128)
    sparsity: float = 0.02       # Target sparsity (2% active)
    noise_tolerance: float = 0.1 # Fraction of bits that can be wrong

    @property
    def n_active(self) -> int:
        """Number of active bits at target sparsity"""
        return int(self.n_bits * self.sparsity)


class SDR:
    """
    Sparse Distributed Representation

    A high-dimensional binary vector where only ~2% of bits are active.
    Similarity = overlap of active bits (Hamming similarity).

    Key properties:
    - Robust to noise (can tolerate ~10% bit flips)
    - Semantic similarity = bit overlap
    - Efficient storage and comparison
    """

    def __init__(self, config: SDRConfig, active_bits: Optional[np.ndarray] = None):
        self.config = config
        if active_bits is not None:
            self._active = np.array(active_bits, dtype=np.int32)
        else:
            self._active = np.array([], dtype=np.int32)

    @classmethod
    def random(cls, config: SDRConfig) -> 'SDR':
        """Create random SDR with target sparsity"""
        active = np.random.choice(config.n_bits, size=config.n_active, replace=False)
        return cls(config, np.sort(active))

    @classmethod
    def from_dense(cls, config: SDRConfig, dense: np.ndarray) -> 'SDR':
        """Convert dense vector to SDR via winner-take-all"""
        k = config.n_active
        if len(dense) != config.n_bits:
            # Project to SDR space
            np.random.seed(hash(dense.tobytes()) % (2**32))
            projection = np.random.randn(len(dense), config.n_bits) / np.sqrt(len(dense))
            dense = dense @ projection

        # Winner-take-all: top k activations
        threshold_idx = np.argpartition(dense, -k)[-k:]
        return cls(config, np.sort(threshold_idx))

    @classmethod
    def from_string(cls, config: SDRConfig, text: str) -> 'SDR':
        """Create SDR from text via semantic folding"""
        # Use hash to get deterministic but distributed bits
        combined_active = set()
        for i, char in enumerate(text):
            # Each character activates a pattern based on position and value
            seed = hash((char, i)) % (2**32)
            np.random.seed(seed)
            char_active = np.random.choice(config.n_bits,
                                           size=config.n_active // max(len(text), 1),
                                           replace=False)
            combined_active.update(char_active)

        # Enforce sparsity
        active = np.array(list(combined_active), dtype=np.int32)
        if len(active) > config.n_active:
            active = np.random.choice(active, size=config.n_active, replace=False)

        return cls(config, np.sort(active))

    def to_dense(self) -> np.ndarray:
        """Convert to dense binary vector"""
        dense = np.zeros(self.config.n_bits, dtype=np.float32)
        dense[self._active] = 1.0
        return dense

    def overlap(self, other: 'SDR') -> int:
        """Count overlapping active bits"""
        return len(np.intersect1d(self._active, other._active))

    def similarity(self, other: 'SDR') -> float:
        """Compute similarity as normalized overlap"""
        if len(self._active) == 0 or len(other._active) == 0:
            return 0.0
        overlap = self.overlap(other)
        max_possible = min(len(self._active), len(other._active))
        return overlap / max_possible if max_possible > 0 else 0.0

    def union(self, other: 'SDR') -> 'SDR':
        """Bundle operation: union of active bits (OR)"""
        combined = np.union1d(self._active, other._active)
        # If too many active, subsample
        if len(combined) > self.config.n_active * 2:
            combined = np.random.choice(combined,
                                        size=self.config.n_active,
                                        replace=False)
        return SDR(self.config, np.sort(combined))

    def intersection(self, other: 'SDR') -> 'SDR':
        """Intersection of active bits (AND)"""
        active = np.intersect1d(self._active, other._active)
        return SDR(self.config, active)

    def bind(self, other: 'SDR') -> 'SDR':
        """Binding operation: XOR of active bits (role-filler binding)"""
        dense1 = self.to_dense()
        dense2 = other.to_dense()
        xor_result = np.logical_xor(dense1 > 0, dense2 > 0).astype(np.float32)

        # Re-sparsify via winner-take-all on XOR pattern
        # Add small noise to break ties
        xor_result += np.random.randn(len(xor_result)) * 0.01
        return SDR.from_dense(self.config, xor_result)

    def permute(self, shift: int = 1) -> 'SDR':
        """Permutation operation: circular shift for sequence encoding"""
        shifted = (self._active + shift) % self.config.n_bits
        return SDR(self.config, np.sort(shifted))

    def add_noise(self, noise_fraction: float) -> 'SDR':
        """Add noise by flipping some bits"""
        n_flip = int(len(self._active) * noise_fraction)

        # Remove some active bits
        keep_idx = np.random.choice(len(self._active),
                                    size=max(0, len(self._active) - n_flip),
                                    replace=False)
        kept = self._active[keep_idx]

        # Add some random new bits
        available = np.setdiff1d(np.arange(self.config.n_bits), self._active)
        new_active = np.random.choice(available, size=n_flip, replace=False)

        combined = np.union1d(kept, new_active)
        return SDR(self.config, np.sort(combined))

    def __len__(self):
        return len(self._active)

    def __repr__(self):
        return f"SDR(n_active={len(self._active)}, total={self.config.n_bits})"


# =============================================================================
# Part 2: Associative Memory (Modern Hopfield Network)
# =============================================================================

class AssociativeMemory:
    """
    Modern Hopfield Network for pattern completion and retrieval

    Key properties:
    - Content-addressable: retrieve by partial cue
    - Exponential capacity: can store ~exp(d) patterns
    - Attention connection: update rule ≈ softmax attention
    """

    def __init__(self, config: SDRConfig, capacity: int = 10000):
        self.config = config
        self.capacity = capacity
        self.patterns: List[SDR] = []
        self.pattern_matrix: Optional[np.ndarray] = None
        self._needs_rebuild = True

        # Temperature for softmax attention
        self.beta = 1.0

    def store(self, pattern: SDR) -> int:
        """Store a pattern, return its index"""
        self.patterns.append(pattern)
        self._needs_rebuild = True

        # Enforce capacity
        if len(self.patterns) > self.capacity:
            # Remove oldest (FIFO)
            self.patterns.pop(0)

        return len(self.patterns) - 1

    def _rebuild_matrix(self):
        """Rebuild dense pattern matrix for efficient retrieval"""
        if not self.patterns:
            self.pattern_matrix = None
            return

        self.pattern_matrix = np.stack([p.to_dense() for p in self.patterns])
        self._needs_rebuild = False

    def retrieve(self, query: SDR, top_k: int = 1) -> List[Tuple[SDR, float]]:
        """
        Retrieve patterns most similar to query

        Uses modern Hopfield update:
        output = softmax(beta * query @ patterns.T) @ patterns
        """
        if not self.patterns:
            return []

        if self._needs_rebuild:
            self._rebuild_matrix()

        query_dense = query.to_dense()

        # Compute similarities (= energy in Hopfield)
        similarities = self.pattern_matrix @ query_dense

        # Softmax attention
        exp_sim = np.exp(self.beta * (similarities - similarities.max()))
        attention = exp_sim / (exp_sim.sum() + 1e-10)

        # Get top-k indices
        top_indices = np.argsort(attention)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            results.append((self.patterns[idx], float(attention[idx])))

        return results

    def complete(self, partial: SDR, n_iterations: int = 3) -> SDR:
        """
        Pattern completion via iterative retrieval

        Start with partial pattern, iteratively refine toward stored pattern
        """
        current = partial

        for _ in range(n_iterations):
            # Get weighted combination of similar patterns
            if self._needs_rebuild:
                self._rebuild_matrix()

            if self.pattern_matrix is None:
                return current

            query_dense = current.to_dense()
            similarities = self.pattern_matrix @ query_dense

            # Softmax attention with higher temperature for completion
            exp_sim = np.exp(self.beta * 2 * (similarities - similarities.max()))
            attention = exp_sim / (exp_sim.sum() + 1e-10)

            # Weighted combination
            completed_dense = attention @ self.pattern_matrix

            # Convert back to SDR
            current = SDR.from_dense(self.config, completed_dense)

        return current

    def clear(self):
        """Clear all stored patterns"""
        self.patterns.clear()
        self.pattern_matrix = None
        self._needs_rebuild = True


# =============================================================================
# Part 3: Episodic Memory with Event Segmentation
# =============================================================================

@dataclass
class Episode:
    """A single episode in memory"""
    sdrs: List[SDR]
    context: SDR
    timestamp: int
    metadata: Dict = field(default_factory=dict)

    def get_summary(self) -> SDR:
        """Get summary SDR by bundling all SDRs in episode"""
        if not self.sdrs:
            return self.context
        summary = self.sdrs[0]
        for sdr in self.sdrs[1:]:
            summary = summary.union(sdr)
        return summary


class EpisodicMemory:
    """
    Episodic Memory with Event Segmentation

    Stores sequences of SDRs as discrete episodes, segmented by
    prediction error (surprise). Enables:
    - Retrieval of similar past experiences
    - Context-dependent recall
    - Temporal navigation
    """

    def __init__(self, config: SDRConfig,
                 capacity: int = 1000,
                 surprise_threshold: float = 0.5):
        self.config = config
        self.capacity = capacity
        self.surprise_threshold = surprise_threshold

        self.episodes: List[Episode] = []
        self.current_episode: List[SDR] = []
        self.current_context: Optional[SDR] = None
        self.timestamp = 0

        # For retrieval
        self.episode_summaries: List[SDR] = []

    def observe(self, sdr: SDR, predicted: Optional[SDR] = None) -> bool:
        """
        Observe new SDR, potentially triggering event boundary

        Returns True if new episode started (event boundary detected)
        """
        self.timestamp += 1

        # Compute prediction error (surprise)
        surprise = 0.0
        if predicted is not None:
            surprise = 1.0 - sdr.similarity(predicted)

        # Check for event boundary
        boundary_detected = False
        if surprise > self.surprise_threshold and self.current_episode:
            # Commit current episode
            self._commit_episode()
            boundary_detected = True

        # Add to current episode
        self.current_episode.append(sdr)

        # Update running context (exponential moving average)
        if self.current_context is None:
            self.current_context = sdr
        else:
            self.current_context = self.current_context.union(sdr)

        return boundary_detected

    def _commit_episode(self):
        """Commit current episode to long-term memory"""
        if not self.current_episode:
            return

        episode = Episode(
            sdrs=self.current_episode.copy(),
            context=self.current_context or SDR.random(self.config),
            timestamp=self.timestamp
        )

        self.episodes.append(episode)
        self.episode_summaries.append(episode.get_summary())

        # Enforce capacity
        if len(self.episodes) > self.capacity:
            self.episodes.pop(0)
            self.episode_summaries.pop(0)

        # Reset current episode
        self.current_episode = []
        self.current_context = None

    def retrieve_by_similarity(self, query: SDR, top_k: int = 5) -> List[Episode]:
        """Retrieve episodes most similar to query"""
        if not self.episode_summaries:
            return []

        similarities = [query.similarity(summary) for summary in self.episode_summaries]
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [self.episodes[i] for i in top_indices]

    def retrieve_by_context(self, context: SDR, top_k: int = 5) -> List[Episode]:
        """Retrieve episodes with similar context"""
        if not self.episodes:
            return []

        similarities = [context.similarity(ep.context) for ep in self.episodes]
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [self.episodes[i] for i in top_indices]

    def retrieve_recent(self, n: int = 5) -> List[Episode]:
        """Retrieve n most recent episodes"""
        return self.episodes[-n:][::-1]

    def force_boundary(self):
        """Force an event boundary (explicit segmentation)"""
        self._commit_episode()


# =============================================================================
# Part 4: Construction Memory (Form-Meaning Pairs)
# =============================================================================

@dataclass
class Construction:
    """
    A construction: learned form-meaning pair

    Following Construction Grammar, these are the basic units of linguistic
    knowledge, ranging from morphemes to complex syntactic patterns.
    """
    form: SDR              # Surface pattern
    meaning: SDR           # Semantic representation
    slots: List[str]       # Named argument slots
    slot_types: Dict[str, SDR]  # Type constraints for slots
    frequency: int = 1     # Usage frequency (for entrenchment)

    def match_strength(self, input_sdr: SDR) -> float:
        """How well does input match this construction's form?"""
        return input_sdr.similarity(self.form)

    def compose(self, fillers: Dict[str, SDR], config: SDRConfig) -> SDR:
        """
        Compose construction with fillers

        Uses HD binding to create compositional meaning:
        result = meaning XOR (slot1_role XOR filler1) XOR (slot2_role XOR filler2) ...
        """
        result = self.meaning

        for slot_name, filler in fillers.items():
            if slot_name in self.slot_types:
                role = self.slot_types[slot_name]
                bound = role.bind(filler)
                result = result.union(bound)

        return result


class ConstructionMemory:
    """
    Memory of constructions (form-meaning pairs)

    Implements construction grammar: all linguistic knowledge is stored as
    constructions at various levels of abstraction.
    """

    def __init__(self, config: SDRConfig):
        self.config = config
        self.constructions: List[Construction] = []

        # Index by form similarity for efficient retrieval
        self.form_index = AssociativeMemory(config, capacity=50000)

    def learn(self, form: SDR, meaning: SDR,
              slots: Optional[List[str]] = None,
              slot_types: Optional[Dict[str, SDR]] = None):
        """Learn a new construction or reinforce existing"""

        # Check if similar construction exists
        matches = self.match(form, threshold=0.8, top_k=1)

        if matches and matches[0][1] > 0.9:
            # Reinforce existing
            matches[0][0].frequency += 1
        else:
            # Create new construction
            construction = Construction(
                form=form,
                meaning=meaning,
                slots=slots or [],
                slot_types=slot_types or {}
            )
            self.constructions.append(construction)
            self.form_index.store(form)

    def match(self, input_sdr: SDR,
              threshold: float = 0.3,
              top_k: int = 5) -> List[Tuple[Construction, float]]:
        """Find constructions matching input"""

        matches = []
        for construction in self.constructions:
            strength = construction.match_strength(input_sdr)
            if strength >= threshold:
                matches.append((construction, strength))

        # Sort by match strength * frequency (entrenchment)
        matches.sort(key=lambda x: x[1] * np.log1p(x[0].frequency), reverse=True)

        return matches[:top_k]

    def compose(self, construction: Construction,
                fillers: Dict[str, SDR]) -> SDR:
        """Compose a construction with fillers"""
        return construction.compose(fillers, self.config)


# =============================================================================
# Part 5: Hierarchical Predictive Dynamics
# =============================================================================

@dataclass
class DynamicsConfig:
    """Configuration for dynamics engine"""
    # Diffusion coefficient (spatial coherence)
    g: float = 0.15
    # Cubic nonlinearity (bistability)
    lam: float = 0.3
    # Momentum (temporal continuity)
    rho: float = 0.4
    # Input coupling
    eta: float = 0.1
    # Prediction error coupling
    alpha: float = 0.2
    # Time step
    dt: float = 0.01
    # Dimensionality
    n_dims: int = 512


class PredictiveLevel:
    """
    Single level in hierarchical predictive processing

    Each level:
    - Receives input from level below
    - Makes predictions about level below
    - Sends prediction errors up
    - Receives predictions from level above
    """

    def __init__(self, n_dims: int, timescale: int, config: DynamicsConfig):
        self.n_dims = n_dims
        self.timescale = timescale
        self.config = config

        # State
        self.mu = np.zeros(n_dims, dtype=np.float32)
        self.mu_prev = np.zeros(n_dims, dtype=np.float32)

        # Predictions
        self.prediction_down = np.zeros(n_dims, dtype=np.float32)
        self.prediction_error = np.zeros(n_dims, dtype=np.float32)

        # Internal step counter
        self.step_count = 0

        # Learnable prediction weights (simple linear for now)
        self._pred_weights = np.eye(n_dims) * 0.9 + np.random.randn(n_dims, n_dims) * 0.01

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """Compute discrete Laplacian (spatial coherence)"""
        # Circular convolution with Laplacian kernel [-1, 2, -1]
        laplacian = (
            2 * mu -
            np.roll(mu, 1) -
            np.roll(mu, -1)
        )
        return laplacian

    def predict_down(self) -> np.ndarray:
        """Generate prediction for level below"""
        self.prediction_down = self._pred_weights @ self.mu
        return self.prediction_down

    def step(self, input_from_below: np.ndarray,
             prediction_from_above: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Single dynamics step

        Update equation:
        mu_{t+1} = mu_t + dt * (g*laplacian - lam*mu^3 + rho*momentum + eta*input + alpha*pred_error)
        """
        self.step_count += 1

        # Only update at this level's timescale
        if self.step_count % self.timescale != 0:
            return self.mu

        # Compute terms
        laplacian = self.compute_laplacian(self.mu)
        cubic = self.mu ** 3
        momentum = self.mu - self.mu_prev

        # Prediction error from above
        pred_error_above = np.zeros_like(self.mu)
        if prediction_from_above is not None:
            # Resize if needed
            if len(prediction_from_above) != self.n_dims:
                # Simple linear projection
                scale = self.n_dims / len(prediction_from_above)
                pred_error_above = np.interp(
                    np.arange(self.n_dims),
                    np.linspace(0, self.n_dims, len(prediction_from_above)),
                    prediction_from_above
                )
            else:
                pred_error_above = self.mu - prediction_from_above

        # Compute prediction error for level below
        if len(input_from_below) != self.n_dims:
            input_resized = np.interp(
                np.arange(self.n_dims),
                np.linspace(0, self.n_dims, len(input_from_below)),
                input_from_below
            )
        else:
            input_resized = input_from_below

        self.prediction_error = input_resized - self.prediction_down

        # Update
        delta = self.config.dt * (
            self.config.g * laplacian -
            self.config.lam * cubic +
            self.config.rho * momentum +
            self.config.eta * input_resized +
            self.config.alpha * pred_error_above
        )

        self.mu_prev = self.mu.copy()
        self.mu = self.mu + delta

        # Stability clipping
        self.mu = np.clip(self.mu, -10, 10)

        # Update prediction
        self.predict_down()

        return self.mu

    def reset(self):
        """Reset state"""
        self.mu = np.zeros(self.n_dims, dtype=np.float32)
        self.mu_prev = np.zeros(self.n_dims, dtype=np.float32)
        self.prediction_down = np.zeros(self.n_dims, dtype=np.float32)
        self.prediction_error = np.zeros(self.n_dims, dtype=np.float32)
        self.step_count = 0


class HierarchicalDynamics:
    """
    Hierarchical Predictive Processing Dynamics

    Five levels corresponding to:
    1. Phoneme/Character (fastest, smallest)
    2. Word/Token
    3. Phrase/Construction
    4. Sentence/Proposition
    5. Discourse/Context (slowest, largest)

    Information flows:
    - Bottom-up: input and prediction errors
    - Top-down: predictions and context
    """

    LEVELS = [
        ("phoneme", 256, 1),      # Level 0: Phonemes - fastest
        ("word", 512, 10),        # Level 1: Words
        ("phrase", 1024, 50),     # Level 2: Phrases
        ("sentence", 2048, 200),  # Level 3: Sentences
        ("discourse", 4096, 1000) # Level 4: Discourse - slowest
    ]

    def __init__(self, config: DynamicsConfig):
        self.config = config

        self.levels = []
        for name, n_dims, timescale in self.LEVELS:
            level = PredictiveLevel(n_dims, timescale, config)
            self.levels.append(level)

        self.step_count = 0

    def step(self, input_sdr: SDR) -> List[np.ndarray]:
        """
        Single step of hierarchical dynamics

        Returns states at all levels
        """
        self.step_count += 1

        # Convert input SDR to dense for bottom level
        bottom_input = input_sdr.to_dense()

        # Resize to bottom level dimensions
        if len(bottom_input) != self.levels[0].n_dims:
            bottom_input = np.interp(
                np.arange(self.levels[0].n_dims),
                np.linspace(0, self.levels[0].n_dims, len(bottom_input)),
                bottom_input
            )

        states = []

        # Bottom-up pass: propagate input and prediction errors
        current_input = bottom_input
        for i, level in enumerate(self.levels):
            # Get prediction from above (if exists)
            pred_from_above = None
            if i < len(self.levels) - 1:
                pred_from_above = self.levels[i + 1].prediction_down

            # Step this level
            state = level.step(current_input, pred_from_above)
            states.append(state)

            # Pass prediction error up
            current_input = level.prediction_error

        return states

    def get_prediction(self, level: int = 0) -> np.ndarray:
        """Get prediction at specified level"""
        return self.levels[level].prediction_down

    def get_prediction_error(self, level: int = 0) -> np.ndarray:
        """Get prediction error at specified level"""
        return self.levels[level].prediction_error

    def get_context(self) -> np.ndarray:
        """Get highest level state (discourse context)"""
        return self.levels[-1].mu

    def reset(self):
        """Reset all levels"""
        for level in self.levels:
            level.reset()
        self.step_count = 0


# =============================================================================
# Part 6: CORAL - The Complete System
# =============================================================================

@dataclass
class CORALConfig:
    """Configuration for CORAL system"""
    sdr_config: SDRConfig = field(default_factory=SDRConfig)
    dynamics_config: DynamicsConfig = field(default_factory=DynamicsConfig)

    # Memory capacities
    associative_capacity: int = 10000
    episodic_capacity: int = 1000

    # Event segmentation
    surprise_threshold: float = 0.5

    # Emission
    emission_cooldown: int = 10
    coherence_threshold: float = 0.3

    # Learning
    learning_rate: float = 0.1
    min_confidence: float = 0.5


class CORAL:
    """
    CORAL: Compositional Oscillatory Recursive Associative Language System

    Main interface for language synthesis that integrates:
    - SDR-based representations
    - Associative memory (Hopfield)
    - Episodic memory with events
    - Construction memory
    - Hierarchical predictive dynamics
    """

    def __init__(self, config: Optional[CORALConfig] = None):
        self.config = config or CORALConfig()

        # Memory systems
        self.associative = AssociativeMemory(
            self.config.sdr_config,
            capacity=self.config.associative_capacity
        )
        self.episodic = EpisodicMemory(
            self.config.sdr_config,
            capacity=self.config.episodic_capacity,
            surprise_threshold=self.config.surprise_threshold
        )
        self.constructions = ConstructionMemory(self.config.sdr_config)

        # Dynamics engine
        self.dynamics = HierarchicalDynamics(self.config.dynamics_config)

        # Token codebook (SDR for each token)
        self.token_to_sdr: Dict[str, SDR] = {}
        self.sdr_to_token: List[Tuple[SDR, str]] = []

        # State
        self.step_count = 0
        self.last_emission_step = -self.config.emission_cooldown
        self.context_sdr: Optional[SDR] = None

        # Emission history
        self.emissions: List[Dict] = []

    def register_token(self, token: str) -> SDR:
        """Register a token in the vocabulary"""
        if token not in self.token_to_sdr:
            sdr = SDR.from_string(self.config.sdr_config, token)
            self.token_to_sdr[token] = sdr
            self.sdr_to_token.append((sdr, token))
            self.associative.store(sdr)
        return self.token_to_sdr[token]

    def encode(self, text: str) -> SDR:
        """Encode text to SDR"""
        # Split into tokens (simple whitespace for now)
        tokens = text.lower().split()

        if not tokens:
            return SDR.random(self.config.sdr_config)

        # Encode each token and bundle with position binding
        result = None
        for i, token in enumerate(tokens):
            token_sdr = self.register_token(token)
            # Position binding via permutation
            positioned = token_sdr.permute(i * 100)

            if result is None:
                result = positioned
            else:
                result = result.union(positioned)

        return result

    def decode(self, sdr: SDR, top_k: int = 5) -> List[Tuple[str, float]]:
        """Decode SDR to tokens"""
        if not self.sdr_to_token:
            return []

        results = []
        for stored_sdr, token in self.sdr_to_token:
            sim = sdr.similarity(stored_sdr)
            results.append((token, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def observe(self, input_text: str) -> Dict:
        """
        Observe input, update state, potentially emit response

        Returns dict with observation results
        """
        self.step_count += 1

        # Encode input
        input_sdr = self.encode(input_text)

        # Get prediction from dynamics
        predicted = self.dynamics.get_prediction(level=1)  # Word level
        predicted_sdr = SDR.from_dense(self.config.sdr_config, predicted)

        # Compute prediction error
        pred_error = 1.0 - input_sdr.similarity(predicted_sdr)

        # Update episodic memory (may trigger event boundary)
        boundary = self.episodic.observe(input_sdr, predicted_sdr)

        # Store in associative memory
        self.associative.store(input_sdr)

        # Update dynamics
        states = self.dynamics.step(input_sdr)

        # Update context
        if self.context_sdr is None:
            self.context_sdr = input_sdr
        else:
            self.context_sdr = self.context_sdr.union(input_sdr)

        # Check for emission
        emission = self._maybe_emit()

        return {
            "step": self.step_count,
            "input_sdr": input_sdr,
            "prediction_error": pred_error,
            "event_boundary": boundary,
            "emission": emission,
            "context": self.context_sdr
        }

    def _maybe_emit(self) -> Optional[Dict]:
        """Check if ready to emit and generate output"""
        # Cooldown check
        if self.step_count - self.last_emission_step < self.config.emission_cooldown:
            return None

        # Get word-level state
        word_state = self.dynamics.levels[1].mu

        # Compute stability (low variance = stable)
        stability = 1.0 / (np.var(word_state) + 0.01)

        # Get context coherence
        context_state = self.dynamics.get_context()
        context_sdr = SDR.from_dense(self.config.sdr_config, context_state)
        coherence = context_sdr.similarity(self.context_sdr) if self.context_sdr else 0

        # Emit if stable and coherent
        if stability > 10 and coherence > self.config.coherence_threshold:
            return self._emit(word_state)

        return None

    def _emit(self, state: np.ndarray) -> Dict:
        """Generate emission from current state"""
        self.last_emission_step = self.step_count

        # Convert state to SDR
        state_sdr = SDR.from_dense(self.config.sdr_config, state)

        # Pattern completion from associative memory
        completed = self.associative.complete(state_sdr)

        # Decode to tokens
        candidates = self.decode(completed)

        # Retrieve relevant episodic context
        episodes = self.episodic.retrieve_by_similarity(completed, top_k=3)

        # Match constructions
        construction_matches = self.constructions.match(completed)

        emission = {
            "step": self.step_count,
            "sdr": completed,
            "tokens": candidates,
            "top_token": candidates[0] if candidates else ("", 0),
            "relevant_episodes": len(episodes),
            "matched_constructions": len(construction_matches)
        }

        self.emissions.append(emission)
        return emission

    def generate(self, prompt: str, max_tokens: int = 50) -> str:
        """
        Generate continuation from prompt

        This is the main interface for language generation
        """
        # Process prompt
        self.observe(prompt)

        generated_tokens = []

        for _ in range(max_tokens):
            # Step dynamics forward
            if self.context_sdr:
                states = self.dynamics.step(self.context_sdr)

            # Check for emission
            emission = self._maybe_emit()

            if emission:
                token, conf = emission["top_token"]
                if conf > self.config.min_confidence:
                    generated_tokens.append(token)

                    # Feed back as new observation
                    self.observe(token)

        return " ".join(generated_tokens)

    def learn_pattern(self, form: str, meaning: str):
        """
        Learn a form-meaning pair (construction)
        """
        form_sdr = self.encode(form)
        meaning_sdr = self.encode(meaning)
        self.constructions.learn(form_sdr, meaning_sdr)

    def converse(self, user_input: str) -> str:
        """
        Have a conversation turn

        More sophisticated than generate() - uses episodic retrieval
        """
        # Observe user input
        result = self.observe(user_input)

        # Retrieve relevant past episodes
        input_sdr = result["input_sdr"]
        relevant = self.episodic.retrieve_by_similarity(input_sdr, top_k=5)

        # Use retrieved context to bias generation
        if relevant:
            # Combine with current context
            for episode in relevant:
                summary = episode.get_summary()
                self.context_sdr = self.context_sdr.union(summary) if self.context_sdr else summary

        # Generate response
        response = self.generate("", max_tokens=20)

        # Learn from this interaction
        if response:
            self.learn_pattern(user_input, response)

        return response if response else "(processing...)"

    def reset(self):
        """Reset to initial state (keep learned patterns)"""
        self.dynamics.reset()
        self.step_count = 0
        self.last_emission_step = -self.config.emission_cooldown
        self.context_sdr = None
        self.emissions.clear()

    def clear(self):
        """Clear everything including learned patterns"""
        self.reset()
        self.associative.clear()
        self.episodic.episodes.clear()
        self.episodic.episode_summaries.clear()
        self.constructions.constructions.clear()
        self.token_to_sdr.clear()
        self.sdr_to_token.clear()


# =============================================================================
# Part 7: Testing and Demonstration
# =============================================================================

def demo_sdr():
    """Demonstrate SDR properties"""
    print("=" * 60)
    print("SDR DEMONSTRATION")
    print("=" * 60)

    config = SDRConfig(n_bits=16384, sparsity=0.02)

    # Create SDRs for words
    cat = SDR.from_string(config, "cat")
    dog = SDR.from_string(config, "dog")
    car = SDR.from_string(config, "car")
    cats = SDR.from_string(config, "cats")

    print(f"\nSDR dimensionality: {config.n_bits}")
    print(f"Target sparsity: {config.sparsity} ({config.n_active} active bits)")

    print(f"\n'cat' SDR: {cat}")
    print(f"'dog' SDR: {dog}")
    print(f"'car' SDR: {car}")
    print(f"'cats' SDR: {cats}")

    print(f"\nSimilarities:")
    print(f"  cat-dog: {cat.similarity(dog):.4f}")
    print(f"  cat-car: {cat.similarity(car):.4f}")
    print(f"  cat-cats: {cat.similarity(cats):.4f}")
    print(f"  dog-car: {dog.similarity(car):.4f}")

    # Test operations
    print(f"\nOperations:")
    union = cat.union(dog)
    print(f"  cat ∪ dog: {union} (contains {cat.overlap(union)} cat bits, {dog.overlap(union)} dog bits)")

    bound = cat.bind(dog)
    print(f"  cat ⊗ dog (bind): {bound}")

    perm = cat.permute(100)
    print(f"  permute(cat, 100): {perm}")
    print(f"  cat similarity to permuted: {cat.similarity(perm):.4f}")

    # Noise robustness
    print(f"\nNoise robustness:")
    noisy = cat.add_noise(0.1)
    print(f"  cat with 10% noise: {noisy}")
    print(f"  similarity to original: {cat.similarity(noisy):.4f}")


def demo_memory():
    """Demonstrate memory systems"""
    print("\n" + "=" * 60)
    print("MEMORY SYSTEMS DEMONSTRATION")
    print("=" * 60)

    config = SDRConfig(n_bits=16384, sparsity=0.02)

    # Associative memory
    print("\n--- Associative Memory (Hopfield) ---")
    mem = AssociativeMemory(config, capacity=100)

    # Store some patterns
    patterns = ["hello", "world", "language", "memory", "neural"]
    stored = []
    for word in patterns:
        sdr = SDR.from_string(config, word)
        mem.store(sdr)
        stored.append((word, sdr))

    print(f"Stored {len(patterns)} patterns")

    # Test retrieval
    query = SDR.from_string(config, "lang")  # Partial cue
    results = mem.retrieve(query, top_k=3)
    print(f"\nQuery 'lang' (partial) retrieves:")
    for i, (sdr, score) in enumerate(results):
        # Find matching word
        matches = [(w, s.similarity(sdr)) for w, s in stored]
        best = max(matches, key=lambda x: x[1])
        print(f"  {i+1}. '{best[0]}' (attention: {score:.4f})")

    # Pattern completion
    print(f"\nPattern completion:")
    partial = stored[2][1].add_noise(0.3)  # Noisy "language"
    completed = mem.complete(partial)
    print(f"  Noisy 'language' → completed similarity to original: {stored[2][1].similarity(completed):.4f}")

    # Episodic memory
    print("\n--- Episodic Memory ---")
    episodic = EpisodicMemory(config, capacity=100, surprise_threshold=0.5)

    # Simulate a conversation
    utterances = [
        "hello how are you",
        "i am fine thanks",
        "what is your name",  # Topic change - should trigger boundary
        "my name is coral",
        "nice to meet you",
        "tell me about language",  # Topic change
        "language is fascinating"
    ]

    print("Processing conversation:")
    for utt in utterances:
        sdr = SDR.from_string(config, utt)
        predicted = SDR.random(config) if not episodic.episodes else \
                   episodic.episodes[-1].get_summary() if episodic.episodes else SDR.random(config)
        boundary = episodic.observe(sdr, predicted)
        marker = " [EVENT BOUNDARY]" if boundary else ""
        print(f"  '{utt}'{marker}")

    # Force final boundary
    episodic.force_boundary()

    print(f"\nDetected {len(episodic.episodes)} episodes")

    # Retrieve by similarity
    query = SDR.from_string(config, "language")
    relevant = episodic.retrieve_by_similarity(query, top_k=2)
    print(f"\nQuery 'language' retrieves {len(relevant)} episodes")


def demo_coral():
    """Demonstrate full CORAL system"""
    print("\n" + "=" * 60)
    print("CORAL SYSTEM DEMONSTRATION")
    print("=" * 60)

    # Create CORAL instance
    coral = CORAL()

    # Register some vocabulary
    vocab = ["hello", "hi", "how", "are", "you", "i", "am", "fine", "good",
             "what", "is", "your", "name", "my", "coral", "nice", "meet",
             "language", "learning", "pattern", "memory", "understand"]

    print(f"\nRegistering vocabulary ({len(vocab)} tokens)...")
    for word in vocab:
        coral.register_token(word)

    # Learn some patterns
    print("\nLearning form-meaning pairs...")
    coral.learn_pattern("hello", "greeting")
    coral.learn_pattern("how are you", "wellbeing inquiry")
    coral.learn_pattern("what is your name", "identity question")
    coral.learn_pattern("nice to meet you", "polite response")

    print(f"Learned {len(coral.constructions.constructions)} constructions")

    # Test observation
    print("\n--- Testing Observation ---")
    test_inputs = ["hello", "how are you", "what is language"]

    for inp in test_inputs:
        result = coral.observe(inp)
        print(f"\nInput: '{inp}'")
        print(f"  Prediction error: {result['prediction_error']:.4f}")
        print(f"  Event boundary: {result['event_boundary']}")
        if result['emission']:
            print(f"  Emission: {result['emission']['top_token']}")

    # Test conversation
    print("\n--- Testing Conversation ---")
    coral.reset()

    conversation = [
        "hello",
        "how are you",
        "what is your name",
        "tell me about language"
    ]

    for user_input in conversation:
        print(f"\nUser: {user_input}")
        response = coral.converse(user_input)
        print(f"CORAL: {response}")

    # Statistics
    print("\n--- System Statistics ---")
    print(f"Total steps: {coral.step_count}")
    print(f"Emissions: {len(coral.emissions)}")
    print(f"Episodes stored: {len(coral.episodic.episodes)}")
    print(f"Patterns in associative memory: {len(coral.associative.patterns)}")
    print(f"Constructions learned: {len(coral.constructions.constructions)}")


if __name__ == "__main__":
    demo_sdr()
    demo_memory()
    demo_coral()

    print("\n" + "=" * 60)
    print("CORAL CORE MODULE LOADED SUCCESSFULLY")
    print("=" * 60)
    print("\nUsage:")
    print("  from coral_core import CORAL, CORALConfig")
    print("  coral = CORAL()")
    print("  coral.observe('hello world')")
    print("  response = coral.converse('how are you?')")
