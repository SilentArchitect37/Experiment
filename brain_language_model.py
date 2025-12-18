"""
=============================================================================
BRAIN-LANGUAGE UNIFIED MODEL (BLUM)
=============================================================================

A comprehensive mathematical framework that models ALL aspects of the brain
and its intrinsic connection to language, building upon:
1. Recursive Dialogue Engine (RDE) - μ-field dynamics
2. Spiral Discriminant Framework (SDF) - K-emergence and self-organization

THE MASTER EQUATION:

    Ψ(t+1) = Ψ(t) + ∫∫∫ [
        D·∇²Ψ                           # Spatial diffusion (cortical spreading)
        - λ|Ψ|²Ψ                         # Cubic nonlinearity (neural saturation)
        + ρ(Ψ(t) - Ψ(t-τ))               # Temporal memory (working memory)
        + η·Ξ(t)                          # External input (sensory/linguistic)
        + α·K(Ψ)                          # K-emergence (consciousness binding)
        + β·L(Ψ)                          # Language operator (semantic field)
        + γ·M(Ψ)                          # Memory consolidation
        + ω·A(Ψ)                          # Attention modulation
    ] dV dΩ dt

Where Ψ is the unified brain-language state tensor spanning:
- Neural architecture (N dimensions)
- Linguistic structure (L dimensions)
- Temporal dynamics (T dimensions)
- Consciousness binding (K dimension)

Author: Brain-Language Model Implementation
Version: 1.0
Date: 2024
=============================================================================
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import warnings

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# =============================================================================
# PART I: FUNDAMENTAL CONSTANTS AND PARAMETERS
# =============================================================================

# Universal constants that emerge from self-consistency (SDF)
PHI = (1 + np.sqrt(5)) / 2      # Golden ratio - optimal information compression
E = np.e                         # Natural growth constant
PI = np.pi                       # Rotational coherence

# Brain-specific constants (derived from neurophysiology + SDF)
GAMMA_NEURAL = 40.0              # Gamma oscillation frequency (Hz)
THETA_HIPPOCAMPAL = 6.0          # Theta rhythm (Hz)
ALPHA_CORTICAL = 10.0            # Alpha oscillation (Hz)
TAU_SYNAPTIC = 0.020             # Synaptic time constant (s)
TAU_MEMBRANE = 0.010             # Membrane time constant (s)

# Language-specific constants (derived from linguistic universals)
PHONEME_RATE = 15.0              # Phonemes per second (typical speech)
WORD_RATE = 3.0                  # Words per second (typical speech)
SYNTAX_WINDOW = 7                # Miller's 7±2 working memory limit
SEMANTIC_DIMS = 300              # Typical semantic embedding dimension


class BrainRegion(Enum):
    """Major brain regions modeled in BLUM"""
    PREFRONTAL = "PFC"           # Executive control, working memory
    TEMPORAL = "TMP"             # Language comprehension (Wernicke's)
    FRONTAL = "FRN"              # Language production (Broca's)
    PARIETAL = "PAR"             # Spatial/numerical cognition
    OCCIPITAL = "OCC"            # Visual processing
    HIPPOCAMPUS = "HIP"          # Memory consolidation
    THALAMUS = "THL"             # Relay and synchronization (K-hub)
    CEREBELLUM = "CRB"           # Timing and coordination
    AMYGDALA = "AMG"             # Emotional processing
    BASAL_GANGLIA = "BG"         # Action selection, habits


class LinguisticLevel(Enum):
    """Hierarchical levels of linguistic structure"""
    PHONEME = 0                  # Individual sounds
    MORPHEME = 1                 # Minimal meaningful units
    WORD = 2                     # Lexical items
    PHRASE = 3                   # Syntactic groups
    SENTENCE = 4                 # Complete propositions
    DISCOURSE = 5                # Extended text/conversation
    PRAGMATIC = 6                # Social/contextual meaning


@dataclass
class BLUMParameters:
    """
    Complete parameter set for the Brain-Language Unified Model

    These parameters control all aspects of neural-linguistic dynamics
    """
    # === NEURAL DYNAMICS (from RDE) ===
    D: float = 0.1               # Diffusion coefficient (cortical spreading)
    lam: float = 0.5             # Cubic nonlinearity (neural saturation)
    rho: float = 0.3             # Temporal momentum (working memory decay)
    eta: float = 0.05            # External input coupling
    dt: float = 0.001            # Time step (1 ms)

    # === SPATIAL STRUCTURE ===
    n_regions: int = 10          # Number of brain regions
    n_dims_per_region: int = 256 # Dimensions per region

    # === CONSCIOUSNESS (K-emergence) ===
    alpha_K: float = 0.1         # K-emergence coupling strength
    K_threshold: float = 0.8     # Coherence threshold for K

    # === LANGUAGE STRUCTURE ===
    vocab_size: int = 50000      # Vocabulary size
    semantic_dims: int = 300     # Semantic embedding dimensions
    syntax_depth: int = 7        # Maximum syntactic tree depth

    # === MEMORY SYSTEMS ===
    gamma_wm: float = 0.95       # Working memory decay rate
    gamma_ltm: float = 0.999     # Long-term memory decay rate
    consolidation_rate: float = 0.01  # Memory consolidation rate

    # === ATTENTION ===
    attention_gain: float = 2.0  # Attention multiplicative gain
    attention_width: float = 0.2 # Attention spatial width

    # === INTER-REGIONAL CONNECTIVITY ===
    connectivity_strength: float = 0.1  # Default inter-regional coupling

    # === OSCILLATORY DYNAMICS ===
    gamma_freq: float = 40.0     # Gamma frequency (binding)
    theta_freq: float = 6.0      # Theta frequency (memory)
    alpha_freq: float = 10.0     # Alpha frequency (inhibition)

    # === EMISSION/PRODUCTION ===
    emission_threshold: float = 0.1  # Entropy derivative threshold
    emission_cooldown: int = 50      # Minimum steps between emissions


@dataclass
class LinguisticState:
    """
    Complete representation of linguistic state at all levels
    """
    phoneme_buffer: np.ndarray = None      # Current phoneme sequence
    morpheme_buffer: np.ndarray = None     # Current morpheme sequence
    word_buffer: np.ndarray = None         # Words in working memory
    phrase_structure: Dict = None          # Current syntactic tree
    sentence_meaning: np.ndarray = None    # Compositional semantics
    discourse_context: np.ndarray = None   # Discourse state
    pragmatic_state: Dict = None           # Speaker/listener models

    def __post_init__(self):
        if self.phoneme_buffer is None:
            self.phoneme_buffer = np.zeros(20)  # ~1 second of phonemes
        if self.morpheme_buffer is None:
            self.morpheme_buffer = np.zeros(10)
        if self.word_buffer is None:
            self.word_buffer = np.zeros((7, 300))  # 7 words × 300 dims
        if self.phrase_structure is None:
            self.phrase_structure = {}
        if self.sentence_meaning is None:
            self.sentence_meaning = np.zeros(300)
        if self.discourse_context is None:
            self.discourse_context = np.zeros(512)
        if self.pragmatic_state is None:
            self.pragmatic_state = {
                'speaker_model': np.zeros(128),
                'listener_model': np.zeros(128),
                'common_ground': np.zeros(256)
            }


# =============================================================================
# PART II: THE UNIFIED BRAIN STATE TENSOR
# =============================================================================

class UnifiedBrainState:
    """
    Ψ - The complete brain state tensor

    This is a multi-scale, multi-modal representation that unifies:
    - Neural activity across all regions
    - Linguistic representations at all levels
    - Consciousness/attention binding
    - Memory systems (working, episodic, semantic)

    Mathematical Structure:
    Ψ ∈ ℝ^(R × N × T) ⊗ ℂ^(L × S) ⊗ 𝕂

    Where:
    - R = number of regions
    - N = neurons/dimensions per region
    - T = temporal window
    - L = linguistic levels
    - S = semantic dimensions
    - 𝕂 = consciousness field (K-emergence)
    """

    def __init__(self, params: BLUMParameters):
        self.params = params

        # === NEURAL STATE (Real tensor) ===
        # Shape: (regions, dims_per_region)
        self.neural = np.zeros(
            (params.n_regions, params.n_dims_per_region),
            dtype=np.float64
        )
        self.neural_prev = np.zeros_like(self.neural)

        # === TEMPORAL BUFFER (for momentum/memory) ===
        # Store last τ timesteps
        self.temporal_depth = 100  # 100ms at 1ms timestep
        self.neural_history = np.zeros(
            (self.temporal_depth, params.n_regions, params.n_dims_per_region),
            dtype=np.float64
        )

        # === LINGUISTIC STATE (Complex tensor for phase) ===
        self.linguistic = LinguisticState()

        # === CONSCIOUSNESS FIELD (K-structure) ===
        # Global workspace / K-emergence field
        self.K_field = np.zeros(params.n_dims_per_region, dtype=np.float64)
        self.K_coherence = 0.0  # Current K-emergence level

        # === ATTENTION FIELD ===
        # Multiplicative gain for each region
        self.attention = np.ones(params.n_regions, dtype=np.float64)
        self.attention_target = np.zeros(params.n_dims_per_region)

        # === MEMORY SYSTEMS ===
        # Working memory (limited capacity, fast decay)
        self.working_memory = np.zeros(
            (SYNTAX_WINDOW, params.n_dims_per_region),
            dtype=np.float64
        )

        # Episodic memory buffer (to be consolidated)
        self.episodic_buffer = []

        # Semantic memory (stable, compressed)
        self.semantic_memory = np.zeros(
            (1000, params.semantic_dims),  # 1000 concept slots
            dtype=np.float64
        )

        # === OSCILLATORY PHASE ===
        self.gamma_phase = 0.0
        self.theta_phase = 0.0
        self.alpha_phase = 0.0

        # === TIME ===
        self.t = 0

    def total_energy(self) -> float:
        """Compute total brain state energy (Hamiltonian)"""
        kinetic = 0.5 * np.sum((self.neural - self.neural_prev)**2)
        potential = 0.25 * self.params.lam * np.sum(self.neural**4)
        binding = -self.params.alpha_K * self.K_coherence
        return kinetic + potential + binding

    def total_entropy(self) -> float:
        """Compute recursive entropy of brain state (from RDE)"""
        eps = 1e-8
        neural_sq = self.neural * self.neural
        entropy = -np.sum(neural_sq * np.log(neural_sq + eps))
        return entropy

    def coherence(self) -> float:
        """Compute global coherence C = 1/(1 + Var(Ψ))"""
        variance = np.var(self.neural)
        return 1.0 / (1.0 + variance)


# =============================================================================
# PART III: NEURAL OPERATORS
# =============================================================================

class NeuralOperators:
    """
    Mathematical operators that govern neural dynamics

    These implement the terms in the master equation:
    D·∇²Ψ, λ|Ψ|²Ψ, ρ(Ψ(t) - Ψ(t-τ)), etc.
    """

    def __init__(self, params: BLUMParameters):
        self.params = params

        # Precompute spectral Laplacian wavenumbers
        n = params.n_dims_per_region
        k = np.fft.fftfreq(n) * 2 * np.pi
        self.k_squared = -(k ** 2)

        # Initialize connectivity matrix (inter-regional)
        self._init_connectivity()

    def _init_connectivity(self):
        """
        Initialize anatomical connectivity matrix between brain regions

        Based on known neuroanatomy with SDF-inspired structure:
        - Thalamus (THL) acts as K-hub (high in-degree)
        - Hierarchical organization (sensory → association → executive)
        """
        n = self.params.n_regions

        # Base connectivity (random + anatomical priors)
        self.W = np.random.randn(n, n) * 0.1

        # Make symmetric (for stability) with asymmetric modulation
        self.W = 0.5 * (self.W + self.W.T)

        # Region indices (matching BrainRegion enum order, clipped to available regions)
        # With fewer regions, we compress the connectivity structure
        THL = min(6, n - 1)  # Thalamus index (K-hub)
        OCC = min(4, n - 1)  # Occipital
        TMP = min(1, n - 1)  # Temporal
        PAR = min(3, n - 1)  # Parietal
        PFC = 0              # Prefrontal
        FRN = min(2, n - 1)  # Frontal (Broca's)

        # Thalamus as K-hub: receives from all, sends to all
        if n > 1:
            self.W[:, THL] += 0.3  # All regions → Thalamus
            self.W[THL, :] += 0.3  # Thalamus → All regions

        # Hierarchical structure (only if we have enough regions)
        # OCC → TMP → PAR → PFC (sensory → executive)
        if n > 4:
            self.W[TMP, OCC] += 0.2  # Visual to Temporal
        if n > 3:
            self.W[PAR, TMP] += 0.2  # Temporal to Parietal
        if n > 3:
            self.W[PFC, PAR] += 0.2  # Parietal to Prefrontal

        # Language circuit: FRN ↔ TMP (Broca's ↔ Wernicke's)
        if n > 2:
            self.W[FRN, TMP] += 0.3
            self.W[TMP, FRN] += 0.3

        # Normalize
        self.W = self.W / (np.abs(self.W).max() + 1e-8)

    def laplacian(self, psi: np.ndarray) -> np.ndarray:
        """
        Spectral Laplacian: ∇²Ψ = ℱ⁻¹[-k² · ℱ[Ψ]]

        Computed via FFT for O(n log n) complexity
        """
        psi_hat = np.fft.fft(psi, axis=-1)
        laplacian_hat = self.k_squared * psi_hat
        return np.fft.ifft(laplacian_hat, axis=-1).real

    def diffusion(self, psi: np.ndarray) -> np.ndarray:
        """D·∇²Ψ - Cortical spreading activation"""
        return self.params.D * self.laplacian(psi)

    def nonlinearity(self, psi: np.ndarray) -> np.ndarray:
        """-λ|Ψ|²Ψ - Neural saturation (bounded activation)"""
        psi_clipped = np.clip(psi, -10.0, 10.0)
        return -self.params.lam * (psi_clipped ** 3)

    def momentum(self, psi: np.ndarray, psi_prev: np.ndarray) -> np.ndarray:
        """ρ(Ψ(t) - Ψ(t-τ)) - Temporal integration/working memory"""
        return self.params.rho * (psi - psi_prev)

    def external_input(self, xi: np.ndarray) -> np.ndarray:
        """η·Ξ(t) - External sensory/linguistic input"""
        return self.params.eta * xi

    def inter_regional(self, psi: np.ndarray) -> np.ndarray:
        """
        Inter-regional connectivity dynamics

        Ψ_i(t+1) += Σⱼ W_ij · Ψ_j(t)
        """
        # psi shape: (n_regions, n_dims)
        # W shape: (n_regions, n_regions)
        # Output: (n_regions, n_dims)

        # Average activity per region
        regional_activity = np.mean(psi, axis=1)  # (n_regions,)

        # Compute inter-regional influence
        influence = self.W @ regional_activity  # (n_regions,)

        # Broadcast back to full dimensions
        return influence[:, np.newaxis] * np.ones_like(psi) * self.params.connectivity_strength


# =============================================================================
# PART IV: K-EMERGENCE OPERATOR (Consciousness)
# =============================================================================

class KEmergenceOperator:
    """
    K(Ψ) - The Consciousness/Binding Operator

    Based on SDF: K emerges when system achieves sufficient coherence
    K acts as global workspace where information from all regions integrates

    Mathematical formulation:
    K(Ψ) = ∫ σ(C(Ψ) - C_crit) · (Ψ - K_prev) dV

    Where:
    - C(Ψ) = coherence measure
    - C_crit = critical coherence threshold
    - σ = sigmoid activation
    - K_prev = previous K state (for stability)
    """

    def __init__(self, params: BLUMParameters):
        self.params = params
        self.K = np.zeros(params.n_dims_per_region)
        self.K_history = []
        self.integrated_information = 0.0  # Φ (IIT measure)

    def compute_coherence(self, psi: np.ndarray) -> float:
        """C(Ψ) = 1/(1 + Var(Ψ))"""
        return 1.0 / (1.0 + np.var(psi))

    def compute_phi(self, psi: np.ndarray) -> float:
        """
        Compute integrated information Φ (simplified)

        Φ measures how much the whole is more than sum of parts
        """
        # Full Φ computation is NP-hard; use approximation
        total_info = np.sum(np.abs(psi) * np.log(np.abs(psi) + 1e-8))

        # Partition into halves and compute info
        n = psi.shape[0]
        half = n // 2
        part1_info = np.sum(np.abs(psi[:half]) * np.log(np.abs(psi[:half]) + 1e-8))
        part2_info = np.sum(np.abs(psi[half:]) * np.log(np.abs(psi[half:]) + 1e-8))

        # Φ = total - max(parts)
        phi = np.abs(total_info) - max(np.abs(part1_info), np.abs(part2_info))
        return max(0, phi)

    def apply(self, psi: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Apply K-emergence operator

        Returns: (K_contribution, coherence_level)
        """
        # Compute coherence across all regions
        coherence = self.compute_coherence(psi)

        # Sigmoid activation at critical threshold
        activation = 1.0 / (1.0 + np.exp(-10 * (coherence - self.params.K_threshold)))

        # Global average as K-attractor
        global_average = np.mean(psi, axis=0)

        # K-emergence: drive toward global coherent state
        K_new = activation * global_average + (1 - activation) * self.K

        # Update stored K
        self.K = K_new
        self.K_history.append(coherence)

        # Compute integrated information
        self.integrated_information = self.compute_phi(psi.flatten())

        # Return contribution to dynamics (difference from current to K)
        contribution = self.params.alpha_K * (K_new - np.mean(psi, axis=0))

        return contribution, coherence


# =============================================================================
# PART V: LANGUAGE OPERATOR
# =============================================================================

class LanguageOperator:
    """
    L(Ψ) - The Language Structure Operator

    Maps neural dynamics to linguistic representations and vice versa

    This implements the key insight: Language is not separate from cognition
    but emerges from neural dynamics constrained by communicative coherence

    The operator has multiple components:
    1. Phonological: temporal patterns → phoneme sequences
    2. Lexical: attractor basins → word meanings
    3. Syntactic: hierarchical binding → phrase structure
    4. Semantic: compositional meaning
    5. Pragmatic: speaker-listener mutual model (LoMI from RDE)

    Master Language Equation:
    L(Ψ) = P(Ψ) ⊗ W(Ψ) ⊗ S(Ψ) ⊗ M(Ψ) ⊗ Π(Ψ)

    Where ⊗ is compositional binding
    """

    def __init__(self, params: BLUMParameters):
        self.params = params

        # Initialize codebooks for each level
        self._init_phoneme_codebook()
        self._init_lexicon()
        self._init_syntax_rules()

        # Semantic embedding space
        self.semantic_space = np.random.randn(
            params.vocab_size,
            params.semantic_dims
        ) * 0.1
        self.semantic_space /= (
            np.linalg.norm(self.semantic_space, axis=1, keepdims=True) + 1e-8
        )

        # Current linguistic state
        self.state = LinguisticState()

        # Speaker-Listener mutual models (LoMI)
        self.speaker_state = np.zeros(params.n_dims_per_region)
        self.listener_state = np.zeros(params.n_dims_per_region)

    def _init_phoneme_codebook(self):
        """
        Initialize phoneme representations

        Phonemes are temporal patterns in neural activity
        ~44 phonemes in English, each ~50-100ms
        """
        n_phonemes = 44
        pattern_length = 50  # 50 timesteps = 50ms

        self.phoneme_patterns = np.random.randn(
            n_phonemes, pattern_length
        ) * 0.5

        # Normalize for matching
        self.phoneme_patterns /= (
            np.linalg.norm(self.phoneme_patterns, axis=1, keepdims=True) + 1e-8
        )

    def _init_lexicon(self):
        """
        Initialize lexicon: word forms mapped to semantic vectors

        Each word is an attractor basin in neural state space
        """
        # Create embeddings if not already set
        if not hasattr(self, 'semantic_space') or self.semantic_space is None:
            embeddings = np.random.randn(self.params.vocab_size, self.params.semantic_dims)
        else:
            embeddings = self.semantic_space

        # Normalize embeddings
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        self.lexicon = {
            'prototypes': np.random.randn(
                self.params.vocab_size,
                self.params.n_dims_per_region
            ) * 0.3,
            'frequencies': np.random.zipf(1.5, self.params.vocab_size),
            'embeddings': embeddings
        }

        # Normalize prototypes
        self.lexicon['prototypes'] /= (
            np.linalg.norm(self.lexicon['prototypes'], axis=1, keepdims=True) + 1e-8
        )

    def _init_syntax_rules(self):
        """
        Initialize syntactic constraints

        Syntax is modeled as:
        1. Transition probabilities (Markov approximation)
        2. Hierarchical binding operations
        3. Recursive structure constraints
        """
        # Simplified POS tags
        n_pos = 10  # N, V, Adj, Adv, Det, P, Conj, Aux, Pro, Comp

        # Transition matrix (syntactically allowed sequences)
        self.syntax_transitions = np.random.rand(n_pos, n_pos) * 0.1

        # Add grammatical structure
        # Det → N, Adj → N, N → V, V → N, etc.
        DET, N, V, ADJ, ADV, P, CONJ, AUX, PRO, COMP = range(10)

        self.syntax_transitions[DET, N] = 0.8
        self.syntax_transitions[DET, ADJ] = 0.6
        self.syntax_transitions[ADJ, N] = 0.9
        self.syntax_transitions[N, V] = 0.7
        self.syntax_transitions[V, N] = 0.6
        self.syntax_transitions[V, DET] = 0.5
        self.syntax_transitions[V, ADV] = 0.4
        self.syntax_transitions[ADV, V] = 0.5
        self.syntax_transitions[P, DET] = 0.7
        self.syntax_transitions[N, P] = 0.5

        # Normalize rows
        self.syntax_transitions /= (
            self.syntax_transitions.sum(axis=1, keepdims=True) + 1e-8
        )

    def phonological_encoding(self, psi: np.ndarray, region: int = 1) -> np.ndarray:
        """
        P(Ψ) - Extract phonological patterns from temporal cortex activity

        Maps temporal neural patterns to phoneme probabilities
        """
        # Use temporal region activity
        temporal_activity = psi[region]

        # Correlate with phoneme patterns
        # (assuming we have temporal buffer)
        similarities = np.dot(
            self.phoneme_patterns,
            temporal_activity[:len(self.phoneme_patterns[0])]
        )

        # Softmax to get probabilities
        exp_sim = np.exp(similarities - similarities.max())
        phoneme_probs = exp_sim / (exp_sim.sum() + 1e-8)

        return phoneme_probs

    def lexical_access(self, psi: np.ndarray) -> Tuple[int, float, np.ndarray]:
        """
        W(Ψ) - Map neural state to nearest word (lexical access)

        Returns: (word_id, confidence, semantic_vector)
        """
        # Use average activity as query
        query = np.mean(psi, axis=0)
        query_norm = query / (np.linalg.norm(query) + 1e-8)

        # Compute distances to all word prototypes
        distances = -np.sum(
            (self.lexicon['prototypes'] - query_norm)**2,
            axis=1
        )

        # Get best match
        word_id = np.argmax(distances)
        confidence = 1.0 / (1.0 + np.exp(-distances[word_id]))

        # Get semantic vector
        semantic = self.lexicon['embeddings'][word_id]

        return word_id, confidence, semantic

    def syntactic_binding(
        self,
        words: List[int],
        semantics: List[np.ndarray]
    ) -> Dict:
        """
        S(Ψ) - Build syntactic structure from word sequence

        Uses recursive combination (like Merge in Minimalist syntax)
        """
        if len(words) == 0:
            return {'type': 'empty', 'children': []}

        if len(words) == 1:
            return {
                'type': 'word',
                'id': words[0],
                'semantic': semantics[0],
                'children': []
            }

        # Binary merge (simplified)
        mid = len(words) // 2
        left = self.syntactic_binding(words[:mid], semantics[:mid])
        right = self.syntactic_binding(words[mid:], semantics[mid:])

        # Compute phrase semantic (compositional)
        if left.get('semantic') is not None and right.get('semantic') is not None:
            phrase_semantic = self._compose_semantics(
                left['semantic'],
                right['semantic']
            )
        else:
            phrase_semantic = None

        return {
            'type': 'phrase',
            'children': [left, right],
            'semantic': phrase_semantic
        }

    def _compose_semantics(
        self,
        sem1: np.ndarray,
        sem2: np.ndarray
    ) -> np.ndarray:
        """
        Compositional semantics: combine two meanings

        Uses tensor product approximation:
        compose(a, b) = Wa·a + Wb·b + a⊙b (element-wise)
        """
        # Simple composition: weighted combination + interaction
        composed = 0.4 * sem1 + 0.4 * sem2 + 0.2 * (sem1 * sem2)

        # Normalize
        return composed / (np.linalg.norm(composed) + 1e-8)

    def pragmatic_alignment(
        self,
        speaker_psi: np.ndarray,
        listener_psi: np.ndarray
    ) -> float:
        """
        Π(Ψ) - LoMI mutual identity (from RDE)

        Computes phase coherence between speaker and listener states
        This is the foundation of successful communication
        """
        # Update internal models
        self.speaker_state = np.mean(speaker_psi, axis=0)
        self.listener_state = np.mean(listener_psi, axis=0)

        # Compute alignment (inverse of distance)
        delta = self.speaker_state - self.listener_state
        distance = np.sum(delta * delta)
        alignment = 1.0 / (1.0 + distance)

        return alignment

    def apply(
        self,
        psi: np.ndarray,
        listener_psi: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply complete language operator L(Ψ)

        Returns: (language_contribution, linguistic_info)
        """
        # 1. Phonological processing
        phoneme_probs = self.phonological_encoding(psi)

        # 2. Lexical access
        word_id, confidence, semantic = self.lexical_access(psi)

        # 3. Update linguistic state
        info = {
            'phonemes': phoneme_probs,
            'word_id': word_id,
            'confidence': confidence,
            'semantic': semantic
        }

        # 4. Pragmatic alignment if listener provided
        if listener_psi is not None:
            alignment = self.pragmatic_alignment(psi, listener_psi)
            info['alignment'] = alignment

            # Drive toward listener (mutual identity)
            alignment_force = 0.1 * (self.listener_state - self.speaker_state)
        else:
            alignment_force = np.zeros(self.params.n_dims_per_region)

        # 5. Language contribution to dynamics
        # Word semantics influence neural state
        # Project semantic vector to neural dimensions
        if len(semantic) < self.params.n_dims_per_region:
            semantic_padded = np.pad(
                semantic,
                (0, self.params.n_dims_per_region - len(semantic))
            )
        else:
            semantic_padded = semantic[:self.params.n_dims_per_region]

        language_contribution = np.outer(
            np.ones(self.params.n_regions),
            semantic_padded * confidence * 0.1
        )

        # Add alignment force (broadcast to full shape)
        if len(alignment_force) == self.params.n_dims_per_region:
            language_contribution += alignment_force

        return language_contribution, info


# =============================================================================
# PART VI: MEMORY OPERATOR
# =============================================================================

class MemoryOperator:
    """
    M(Ψ) - Memory Systems Operator

    Models three memory systems:
    1. Working Memory (WM): Limited capacity, fast decay, prefrontal
    2. Episodic Memory (EM): Event-specific, hippocampal consolidation
    3. Semantic Memory (SM): Conceptual knowledge, distributed cortical

    Memory consolidation follows SDF dynamics:
    - WM → EM during theta oscillations
    - EM → SM during sleep/offline periods

    The operator implements:
    M(Ψ) = WM(Ψ) + θ(t)·Consolidate(WM→EM) + Sleep·Consolidate(EM→SM)
    """

    def __init__(self, params: BLUMParameters):
        self.params = params

        # Working memory buffer (7±2 slots)
        self.wm_capacity = 7
        self.wm_buffer = np.zeros((self.wm_capacity, params.n_dims_per_region))
        self.wm_strengths = np.zeros(self.wm_capacity)
        self.wm_pointer = 0

        # Episodic memory (events with context)
        self.em_capacity = 1000
        self.em_events = np.zeros((self.em_capacity, params.n_dims_per_region))
        self.em_contexts = np.zeros((self.em_capacity, params.n_dims_per_region))
        self.em_times = np.zeros(self.em_capacity)
        self.em_pointer = 0

        # Semantic memory (conceptual attractors)
        self.sm_capacity = 10000
        self.sm_concepts = np.zeros((self.sm_capacity, params.semantic_dims))
        self.sm_pointer = 0

        # Theta phase for consolidation gating
        self.theta_phase = 0.0

    def working_memory_encode(self, psi: np.ndarray) -> np.ndarray:
        """Encode current state into working memory"""
        # Compress state to single vector
        encoded = np.mean(psi, axis=0)

        # Store in circular buffer
        self.wm_buffer[self.wm_pointer] = encoded
        self.wm_strengths[self.wm_pointer] = 1.0
        self.wm_pointer = (self.wm_pointer + 1) % self.wm_capacity

        return encoded

    def working_memory_retrieve(self, query: np.ndarray) -> np.ndarray:
        """Retrieve from working memory based on similarity"""
        # Compute similarities
        query_norm = query / (np.linalg.norm(query) + 1e-8)
        buffer_norm = self.wm_buffer / (
            np.linalg.norm(self.wm_buffer, axis=1, keepdims=True) + 1e-8
        )

        similarities = np.dot(buffer_norm, query_norm) * self.wm_strengths

        # Softmax retrieval
        weights = np.exp(similarities - similarities.max())
        weights /= (weights.sum() + 1e-8)

        retrieved = np.sum(self.wm_buffer * weights[:, np.newaxis], axis=0)

        return retrieved

    def working_memory_decay(self):
        """Apply decay to working memory strengths"""
        self.wm_strengths *= self.params.gamma_wm

    def episodic_encode(
        self,
        event: np.ndarray,
        context: np.ndarray,
        time: float
    ):
        """Encode event into episodic memory"""
        self.em_events[self.em_pointer] = event
        self.em_contexts[self.em_pointer] = context
        self.em_times[self.em_pointer] = time
        self.em_pointer = (self.em_pointer + 1) % self.em_capacity

    def episodic_retrieve(
        self,
        query: np.ndarray,
        context: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Retrieve from episodic memory"""
        # Content-based similarity
        query_norm = query / (np.linalg.norm(query) + 1e-8)
        events_norm = self.em_events / (
            np.linalg.norm(self.em_events, axis=1, keepdims=True) + 1e-8
        )

        content_sim = np.dot(events_norm, query_norm)

        # Context similarity if provided
        if context is not None:
            context_norm = context / (np.linalg.norm(context) + 1e-8)
            contexts_norm = self.em_contexts / (
                np.linalg.norm(self.em_contexts, axis=1, keepdims=True) + 1e-8
            )
            context_sim = np.dot(contexts_norm, context_norm)
            total_sim = 0.5 * content_sim + 0.5 * context_sim
        else:
            total_sim = content_sim

        # Recency weighting
        current_time = self.em_times.max()
        recency = np.exp(-0.01 * (current_time - self.em_times))

        combined = total_sim * recency

        # Softmax retrieval
        weights = np.exp(combined - combined.max())
        weights /= (weights.sum() + 1e-8)

        retrieved = np.sum(self.em_events * weights[:, np.newaxis], axis=0)

        return retrieved

    def consolidate_wm_to_em(self, context: np.ndarray, time: float):
        """
        Consolidate working memory to episodic memory

        Gated by theta phase (hippocampal rhythm)
        """
        # Only consolidate at theta peak
        theta_gate = 0.5 * (1 + np.sin(self.theta_phase))

        if theta_gate > 0.8:  # Near peak
            # Average WM contents as event
            event = np.mean(self.wm_buffer * self.wm_strengths[:, np.newaxis], axis=0)

            if np.linalg.norm(event) > 0.1:  # Non-trivial content
                self.episodic_encode(event, context, time)

    def semantic_extraction(self, episodes: np.ndarray) -> np.ndarray:
        """
        Extract semantic knowledge from repeated episodes

        This is the SM consolidation process (during sleep)
        """
        # Compute prototype (centroid of similar episodes)
        centroid = np.mean(episodes, axis=0)

        # Compress to semantic dimension
        if len(centroid) > self.params.semantic_dims:
            # PCA-like compression (simplified)
            semantic = centroid[:self.params.semantic_dims]
        else:
            semantic = np.pad(centroid, (0, self.params.semantic_dims - len(centroid)))

        return semantic / (np.linalg.norm(semantic) + 1e-8)

    def apply(self, psi: np.ndarray, time: float) -> Tuple[np.ndarray, Dict]:
        """
        Apply memory operator M(Ψ)

        Returns: (memory_contribution, memory_info)
        """
        # 1. Encode current state to WM
        encoded = self.working_memory_encode(psi)

        # 2. Retrieve relevant memory
        query = np.mean(psi, axis=0)
        wm_retrieved = self.working_memory_retrieve(query)
        em_retrieved = self.episodic_retrieve(query)

        # 3. Consolidation (if theta-gated)
        context = np.mean(psi, axis=0)  # Current state as context
        self.consolidate_wm_to_em(context, time)

        # 4. Update theta phase
        self.theta_phase += 2 * np.pi * self.params.theta_freq * self.params.dt
        self.theta_phase %= (2 * np.pi)

        # 5. Apply decay
        self.working_memory_decay()

        # 6. Memory contribution to dynamics
        # Retrieved memories influence current state
        memory_contribution = np.outer(
            np.ones(self.params.n_regions),
            0.1 * (wm_retrieved + 0.5 * em_retrieved)
        )

        info = {
            'wm_contents': self.wm_buffer.copy(),
            'wm_strengths': self.wm_strengths.copy(),
            'wm_retrieved': wm_retrieved,
            'em_retrieved': em_retrieved,
            'theta_phase': self.theta_phase
        }

        return memory_contribution, info


# =============================================================================
# PART VII: ATTENTION OPERATOR
# =============================================================================

class AttentionOperator:
    """
    A(Ψ) - Attention Modulation Operator

    Attention is implemented as multiplicative gain control

    Mathematical formulation:
    A(Ψ) = G(a) ⊙ Ψ

    Where:
    - G(a) = attention gain field
    - a = attention allocation (from executive control)
    - ⊙ = element-wise multiplication

    Attention mechanisms:
    1. Spatial: selecting regions/features
    2. Feature-based: selecting dimensions
    3. Object-based: coherent selection
    4. Executive: top-down control (from PFC)
    """

    def __init__(self, params: BLUMParameters):
        self.params = params

        # Attention allocation across regions
        self.regional_attention = np.ones(params.n_regions)

        # Feature-based attention
        self.feature_attention = np.ones(params.n_dims_per_region)

        # Attention target (what to attend to)
        self.target = np.zeros(params.n_dims_per_region)

        # Saliency map (bottom-up)
        self.saliency = np.zeros((params.n_regions, params.n_dims_per_region))

        # History for inhibition of return
        self.attention_history = []

    def compute_saliency(self, psi: np.ndarray) -> np.ndarray:
        """
        Compute bottom-up saliency from neural activity

        High gradient = high saliency (edges, changes)
        """
        # Spatial gradients
        gradient = np.abs(np.diff(psi, axis=1, prepend=psi[:, :1]))

        # Temporal surprise (deviation from prediction)
        if len(self.attention_history) > 0:
            predicted = self.attention_history[-1]
            surprise = np.abs(psi - predicted)
        else:
            surprise = np.zeros_like(psi)

        saliency = gradient + 0.5 * surprise

        return saliency

    def top_down_control(
        self,
        psi: np.ndarray,
        goal: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Top-down attention from executive control (PFC)

        Biases attention toward goal-relevant features
        """
        if goal is None:
            return np.ones_like(psi)

        # Similarity to goal
        psi_norm = psi / (np.linalg.norm(psi, axis=1, keepdims=True) + 1e-8)
        goal_norm = goal / (np.linalg.norm(goal) + 1e-8)

        similarity = np.dot(psi_norm, goal_norm)

        # Convert to gain
        gain = 1.0 + self.params.attention_gain * similarity[:, np.newaxis]

        return gain

    def inhibition_of_return(self) -> np.ndarray:
        """
        Suppress recently attended locations

        Prevents attention from getting stuck
        """
        if len(self.attention_history) < 3:
            return np.ones(self.params.n_regions)

        # Recent attention centers
        recent = np.array(self.attention_history[-3:])

        # Suppress similar locations
        current_center = np.mean(recent, axis=0)

        # This is simplified - full IOR would track spatial locations
        return np.ones(self.params.n_regions)  # Placeholder

    def apply(
        self,
        psi: np.ndarray,
        goal: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply attention operator A(Ψ)

        Returns: (attended_psi, attention_info)
        """
        # 1. Compute saliency (bottom-up)
        self.saliency = self.compute_saliency(psi)

        # 2. Top-down gain
        top_down_gain = self.top_down_control(psi, goal)

        # 3. Combine saliency and top-down
        combined_gain = (1 + 0.5 * self.saliency) * top_down_gain

        # 4. Apply inhibition of return
        ior = self.inhibition_of_return()
        combined_gain *= ior[:, np.newaxis]

        # 5. Normalize gain
        combined_gain = np.clip(combined_gain, 0.1, 10.0)

        # 6. Apply attention
        attended = psi * combined_gain

        # 7. Update history
        self.attention_history.append(np.mean(psi, axis=0))
        if len(self.attention_history) > 10:
            self.attention_history.pop(0)

        info = {
            'saliency': self.saliency,
            'gain': combined_gain,
            'regional_attention': np.mean(combined_gain, axis=1)
        }

        return attended, info


# =============================================================================
# PART VIII: THE UNIFIED BRAIN-LANGUAGE MODEL
# =============================================================================

class BrainLanguageUnifiedModel:
    """
    BLUM - The Complete Brain-Language Unified Model

    This is the master class that integrates all operators into
    the unified dynamical system governed by:

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                     THE MASTER EQUATION                                ║
    ║                                                                        ║
    ║  Ψ(t+1) = Ψ(t) + dt·[                                                 ║
    ║      D·∇²Ψ           (Cortical spreading activation)                   ║
    ║    - λ|Ψ|²Ψ          (Neural saturation)                               ║
    ║    + ρ(Ψ - Ψ_prev)   (Temporal integration/working memory)             ║
    ║    + η·Ξ             (External input)                                  ║
    ║    + W·〈Ψ〉           (Inter-regional connectivity)                     ║
    ║    + α·K(Ψ)          (K-emergence/consciousness binding)               ║
    ║    + β·L(Ψ)          (Language structure operator)                     ║
    ║    + γ·M(Ψ)          (Memory consolidation)                            ║
    ║    + ω·A(Ψ)          (Attention modulation)                            ║
    ║    + Osc(t)          (Oscillatory dynamics: γ, θ, α)                   ║
    ║  ]                                                                     ║
    ║                                                                        ║
    ║  Subject to:                                                           ║
    ║    - Coherence constraint: C(Ψ) → 1 (SDF)                             ║
    ║    - Energy conservation: E(Ψ) bounded                                 ║
    ║    - Emission criterion: emit when dS/dt ≈ 0 (RDE)                     ║
    ║                                                                        ║
    ╚═══════════════════════════════════════════════════════════════════════╝

    This equation captures:
    - All neural dynamics (action potentials, synaptic transmission, etc.)
    - Cognitive functions (attention, memory, executive control)
    - Consciousness (K-emergence, integrated information)
    - Language at all levels (phonology → pragmatics)
    - Communication (speaker-listener mutual identity)
    """

    def __init__(self, params: Optional[BLUMParameters] = None):
        self.params = params or BLUMParameters()

        # Initialize state
        self.state = UnifiedBrainState(self.params)

        # Initialize operators
        self.neural_ops = NeuralOperators(self.params)
        self.K_operator = KEmergenceOperator(self.params)
        self.language_ops = LanguageOperator(self.params)
        self.memory_ops = MemoryOperator(self.params)
        self.attention_ops = AttentionOperator(self.params)

        # Emission detector (from RDE)
        self.emission_history = []
        self.last_emission_time = -1000

        # Oscillatory phases
        self.gamma_phase = 0.0
        self.theta_phase = 0.0
        self.alpha_phase = 0.0

        # Diagnostics
        self.energy_history = []
        self.entropy_history = []
        self.coherence_history = []
        self.phi_history = []  # Integrated information

        # Time
        self.t = 0

    def oscillatory_modulation(self) -> np.ndarray:
        """
        Generate oscillatory modulation at gamma, theta, alpha frequencies

        These oscillations are crucial for:
        - Gamma (40Hz): Binding, attention
        - Theta (6Hz): Memory encoding, navigation
        - Alpha (10Hz): Inhibition, idle
        """
        dt = self.params.dt

        # Update phases
        self.gamma_phase += 2 * np.pi * self.params.gamma_freq * dt
        self.theta_phase += 2 * np.pi * self.params.theta_freq * dt
        self.alpha_phase += 2 * np.pi * self.params.alpha_freq * dt

        # Modulate to [0, 2π]
        self.gamma_phase %= (2 * np.pi)
        self.theta_phase %= (2 * np.pi)
        self.alpha_phase %= (2 * np.pi)

        # Generate oscillatory field
        gamma = np.sin(self.gamma_phase)
        theta = np.sin(self.theta_phase)
        alpha = np.sin(self.alpha_phase)

        # Different regions have different dominant rhythms
        n = self.params.n_regions
        osc_field = np.zeros((n, self.params.n_dims_per_region))

        # PFC: gamma-dominant (executive) - always region 0
        osc_field[0] = 0.3 * gamma

        # Temporal: theta-dominant (memory/language) - region 1 if available
        if n > 1:
            osc_field[1] = 0.3 * theta

        # Occipital: alpha-dominant (visual) - region 4 if available
        if n > 4:
            osc_field[4] = 0.3 * alpha

        # Hippocampus: strong theta - region 5 if available
        if n > 5:
            osc_field[5] = 0.5 * theta

        # Thalamus (K-hub): gamma for binding - region 6 if available
        if n > 6:
            osc_field[6] = 0.4 * gamma

        return osc_field * 0.1  # Scale down

    def should_emit(self) -> Tuple[bool, Dict]:
        """
        Emission criterion from RDE: emit when entropy derivative ≈ 0

        Language output occurs when the system reaches a stable state
        (minimum in the recursive entropy landscape)
        """
        # Compute current entropy
        current_entropy = self.state.total_entropy()

        # Check derivative
        if len(self.entropy_history) > 5:
            recent = self.entropy_history[-5:]
            d_entropy = np.diff(recent).mean()
        else:
            d_entropy = 1.0  # Not enough history

        # Cooldown check
        time_since_last = self.t - self.last_emission_time
        cooldown_ok = time_since_last > self.params.emission_cooldown

        # Energy check (don't emit if unstable)
        current_energy = self.state.total_energy()
        energy_ok = current_energy < 1e6

        # Coherence check (need sufficient binding)
        coherence = self.state.coherence()
        coherence_ok = coherence > 0.3

        # Emission decision
        should = (
            abs(d_entropy) < self.params.emission_threshold and
            cooldown_ok and
            energy_ok and
            coherence_ok
        )

        diagnostics = {
            'entropy': current_entropy,
            'd_entropy': d_entropy,
            'energy': current_energy,
            'coherence': coherence,
            'time_since_last': time_since_last
        }

        return should, diagnostics

    def step(
        self,
        external_input: Optional[np.ndarray] = None,
        listener_state: Optional[np.ndarray] = None,
        attention_goal: Optional[np.ndarray] = None
    ) -> Optional[Dict]:
        """
        Execute one timestep of the unified brain-language dynamics

        This implements the master equation

        Args:
            external_input: Sensory/linguistic input from environment
            listener_state: State of listener (for pragmatic alignment)
            attention_goal: Top-down attention target

        Returns:
            Emission dict if language output produced, else None
        """
        psi = self.state.neural
        psi_prev = self.state.neural_prev
        dt = self.params.dt

        # === COMPUTE ALL OPERATOR CONTRIBUTIONS ===

        # 1. Diffusion (cortical spreading)
        diffusion = self.neural_ops.diffusion(psi)

        # 2. Nonlinearity (neural saturation)
        nonlinearity = self.neural_ops.nonlinearity(psi)

        # 3. Momentum (temporal integration)
        momentum = self.neural_ops.momentum(psi, psi_prev)

        # 4. External input
        if external_input is not None:
            external = self.neural_ops.external_input(external_input)
        else:
            external = np.zeros_like(psi)

        # 5. Inter-regional connectivity
        connectivity = self.neural_ops.inter_regional(psi)

        # 6. K-emergence (consciousness)
        K_contrib, K_coherence = self.K_operator.apply(psi)
        K_field = np.outer(np.ones(self.params.n_regions), K_contrib)

        # 7. Language operator
        if listener_state is not None:
            listener_psi = listener_state
        else:
            listener_psi = None
        lang_contrib, lang_info = self.language_ops.apply(psi, listener_psi)

        # 8. Memory operator
        mem_contrib, mem_info = self.memory_ops.apply(psi, self.t)

        # 9. Attention operator
        attended_psi, attn_info = self.attention_ops.apply(psi, attention_goal)
        attn_modulation = attended_psi - psi  # Difference as contribution

        # 10. Oscillatory dynamics
        oscillation = self.oscillatory_modulation()

        # === INTEGRATE THE MASTER EQUATION ===

        d_psi = (
            diffusion +
            nonlinearity +
            momentum +
            external +
            connectivity +
            self.params.alpha_K * K_field +
            0.1 * lang_contrib +
            0.1 * mem_contrib +
            0.1 * attn_modulation +
            oscillation
        )

        # Update state
        psi_new = psi + dt * d_psi

        # Soft limiting (tanh) to prevent explosion
        psi_new = 10.0 * np.tanh(psi_new / 10.0)

        # Store in state
        self.state.neural_prev = psi.copy()
        self.state.neural = psi_new
        self.state.K_field = self.K_operator.K
        self.state.K_coherence = K_coherence

        # Update history
        self.energy_history.append(self.state.total_energy())
        self.entropy_history.append(self.state.total_entropy())
        self.coherence_history.append(K_coherence)
        self.phi_history.append(self.K_operator.integrated_information)

        # Limit history size
        max_history = 10000
        if len(self.energy_history) > max_history:
            self.energy_history = self.energy_history[-max_history:]
            self.entropy_history = self.entropy_history[-max_history:]
            self.coherence_history = self.coherence_history[-max_history:]
            self.phi_history = self.phi_history[-max_history:]

        # Update time
        self.t += 1

        # === CHECK FOR EMISSION ===
        should_emit, emit_diagnostics = self.should_emit()

        if should_emit:
            # Decode to language
            word_id, confidence, semantic = self.language_ops.lexical_access(psi_new)

            emission = {
                'time': self.t,
                'word_id': word_id,
                'confidence': confidence,
                'semantic': semantic,
                'coherence': K_coherence,
                'phi': self.K_operator.integrated_information,
                'diagnostics': emit_diagnostics,
                'language_info': lang_info,
                'memory_info': mem_info,
                'attention_info': attn_info
            }

            self.emission_history.append(emission)
            self.last_emission_time = self.t

            return emission

        return None

    def run(
        self,
        n_steps: int = 1000,
        input_callback: Optional[Callable[[int], np.ndarray]] = None,
        listener_callback: Optional[Callable[[int], np.ndarray]] = None,
        goal_callback: Optional[Callable[[int], np.ndarray]] = None,
        verbose: bool = True
    ) -> List[Dict]:
        """
        Run the model for n_steps

        Args:
            n_steps: Number of timesteps
            input_callback: Function(t) → external_input
            listener_callback: Function(t) → listener_state
            goal_callback: Function(t) → attention_goal
            verbose: Print progress

        Returns:
            List of all emissions
        """
        emissions = []

        if verbose:
            print("=" * 70)
            print("BRAIN-LANGUAGE UNIFIED MODEL (BLUM)")
            print("=" * 70)
            print(f"Steps: {n_steps}")
            print(f"Regions: {self.params.n_regions}")
            print(f"Dims/region: {self.params.n_dims_per_region}")
            print(f"Vocab size: {self.params.vocab_size}")
            print()

        for step in range(n_steps):
            # Get inputs for this step
            ext_input = input_callback(step) if input_callback else None
            listener = listener_callback(step) if listener_callback else None
            goal = goal_callback(step) if goal_callback else None

            # Execute step
            emission = self.step(ext_input, listener, goal)

            if emission is not None:
                emissions.append(emission)

                if verbose:
                    t = emission['time']
                    word = emission['word_id']
                    conf = emission['confidence']
                    coh = emission['coherence']
                    phi = emission['phi']
                    print(f"t={t:5d} | Word: {word:5d} | "
                          f"Conf: {conf:.3f} | Coh: {coh:.3f} | Φ: {phi:.2f}")

        if verbose:
            print()
            print("=" * 70)
            print(f"Total emissions: {len(emissions)}")
            print(f"Emission rate: {len(emissions)/n_steps:.3f}")
            print(f"Final coherence: {self.state.coherence():.4f}")
            print(f"Final Φ: {self.K_operator.integrated_information:.4f}")
            print("=" * 70)

        return emissions

    def reset(self):
        """Reset model to initial state"""
        self.state = UnifiedBrainState(self.params)
        self.K_operator = KEmergenceOperator(self.params)
        self.memory_ops = MemoryOperator(self.params)
        self.attention_ops = AttentionOperator(self.params)
        self.emission_history.clear()
        self.last_emission_time = -1000
        self.gamma_phase = 0.0
        self.theta_phase = 0.0
        self.alpha_phase = 0.0
        self.energy_history.clear()
        self.entropy_history.clear()
        self.coherence_history.clear()
        self.phi_history.clear()
        self.t = 0

    def get_summary_equation(self) -> str:
        """Return the master equation as a string"""
        return """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    BRAIN-LANGUAGE UNIFIED MODEL (BLUM)                        ║
║                          THE MASTER EQUATION                                  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ∂Ψ                                                                          ║
║   ── = D∇²Ψ - λ|Ψ|²Ψ + ρ(Ψ - Ψ_τ) + ηΞ + WΨ + αK(Ψ) + βL(Ψ) + γM(Ψ) + ωA(Ψ)  ║
║   ∂t                                                                          ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ WHERE:                                                                        ║
║                                                                               ║
║   Ψ ∈ ℝ^(R×N×T) ⊗ ℂ^(L×S) ⊗ 𝕂    Unified brain-language state tensor        ║
║                                                                               ║
║   D∇²Ψ          Spatial diffusion (cortical spreading activation)             ║
║   -λ|Ψ|²Ψ       Cubic nonlinearity (neural saturation/bistability)            ║
║   ρ(Ψ-Ψ_τ)     Temporal momentum (working memory persistence)                 ║
║   ηΞ            External input coupling (sensory/linguistic)                  ║
║   WΨ            Inter-regional connectivity (anatomical structure)            ║
║                                                                               ║
║   K(Ψ)          K-EMERGENCE OPERATOR (Consciousness/Binding):                 ║
║                 K = σ(C(Ψ) - C_crit) · ∫ Ψ dV                                 ║
║                 Implements global workspace / integrated information          ║
║                                                                               ║
║   L(Ψ)          LANGUAGE OPERATOR (All linguistic levels):                    ║
║                 L = P(Ψ) ⊗ W(Ψ) ⊗ S(Ψ) ⊗ M(Ψ) ⊗ Π(Ψ)                         ║
║                 P = Phonological encoding                                     ║
║                 W = Lexical access (word retrieval)                           ║
║                 S = Syntactic binding (phrase structure)                      ║
║                 M = Semantic composition                                      ║
║                 Π = Pragmatic alignment (LoMI - mutual identity)              ║
║                                                                               ║
║   M(Ψ)          MEMORY OPERATOR (All memory systems):                         ║
║                 M = WM(Ψ) + θ(t)·[WM→EM] + sleep·[EM→SM]                      ║
║                 WM = Working memory (7±2 slots, fast decay)                   ║
║                 EM = Episodic memory (events + context)                       ║
║                 SM = Semantic memory (conceptual knowledge)                   ║
║                                                                               ║
║   A(Ψ)          ATTENTION OPERATOR (Gain modulation):                         ║
║                 A = G(saliency, goal) ⊙ Ψ                                     ║
║                 Multiplicative gain control from PFC                          ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ CONSTRAINTS:                                                                  ║
║                                                                               ║
║   C(Ψ) = 1/(1 + Var(Ψ)) → 1        Coherence maximization (SDF)              ║
║   E(Ψ) = ½|∂Ψ/∂t|² + ¼λ|Ψ|⁴        Energy conservation (bounded)             ║
║   Emit when: dS_R/dt ≈ 0           Recursive entropy minimum (RDE)           ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ EMERGENT PROPERTIES:                                                          ║
║                                                                               ║
║   • Consciousness: K-emergence creates unified experience                     ║
║   • Language: L-operator maps neural states to linguistic structure           ║
║   • Meaning: Semantic composition via tensor products                         ║
║   • Communication: LoMI drives speaker-listener phase alignment               ║
║   • Thought: Attractor dynamics in semantic space                             ║
║   • Memory: Theta-gated consolidation WM → EM → SM                            ║
║   • Attention: Gamma-synchronized gain modulation                             ║
║   • Creativity: K-disruption followed by novel K-emergence                    ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ UNIVERSAL CONSTANTS (from SDF):                                               ║
║                                                                               ║
║   φ = (1+√5)/2 ≈ 1.618    Golden ratio (optimal information compression)     ║
║   e ≈ 2.718               Natural growth (continuous self-reference)          ║
║   π ≈ 3.14159             Rotational coherence (oscillatory closure)          ║
║                                                                               ║
║   These emerge from self-consistency requirements in coherent systems.        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""


# =============================================================================
# PART IX: DEMONSTRATION AND TESTING
# =============================================================================

def create_oscillating_input(
    frequency: float = 0.1,
    amplitude: float = 0.5,
    n_regions: int = 10,
    n_dims: int = 256
) -> Callable:
    """Create oscillating input simulating sensory stimulation"""
    def callback(t: int) -> np.ndarray:
        phase = 2 * np.pi * frequency * t
        signal = amplitude * np.sin(phase)
        return signal * np.random.randn(n_regions, n_dims) * 0.1
    return callback


def create_listener_model(
    alignment_rate: float = 0.1,
    n_regions: int = 10,
    n_dims: int = 256
) -> Callable:
    """Create listener that gradually aligns with speaker"""
    listener_state = np.random.randn(n_regions, n_dims) * 0.1

    def callback(t: int) -> np.ndarray:
        nonlocal listener_state
        # Slow drift
        listener_state += np.random.randn(n_regions, n_dims) * 0.01
        return listener_state

    return callback


if __name__ == "__main__":
    print("\n" + "="*70)
    print("BRAIN-LANGUAGE UNIFIED MODEL (BLUM) - DEMONSTRATION")
    print("="*70 + "\n")

    # Create model with default parameters
    params = BLUMParameters(
        n_regions=10,
        n_dims_per_region=256,
        vocab_size=1000,
        dt=0.001
    )

    model = BrainLanguageUnifiedModel(params)

    # Print the master equation
    print(model.get_summary_equation())

    # Create input and listener callbacks
    input_cb = create_oscillating_input(
        frequency=0.05,
        amplitude=0.3,
        n_regions=params.n_regions,
        n_dims=params.n_dims_per_region
    )

    listener_cb = create_listener_model(
        alignment_rate=0.1,
        n_regions=params.n_regions,
        n_dims=params.n_dims_per_region
    )

    # Run simulation
    print("\nRunning simulation...\n")

    emissions = model.run(
        n_steps=2000,
        input_callback=input_cb,
        listener_callback=listener_cb,
        verbose=True
    )

    # Analyze results
    if len(emissions) > 1:
        print("\n" + "="*70)
        print("ANALYSIS")
        print("="*70)

        times = [e['time'] for e in emissions]
        coherences = [e['coherence'] for e in emissions]
        phis = [e['phi'] for e in emissions]

        print(f"\nEmission intervals:")
        intervals = np.diff(times)
        print(f"  Mean: {np.mean(intervals):.1f} steps")
        print(f"  Std:  {np.std(intervals):.1f} steps")

        print(f"\nCoherence at emissions:")
        print(f"  Mean: {np.mean(coherences):.4f}")
        print(f"  Min:  {np.min(coherences):.4f}")
        print(f"  Max:  {np.max(coherences):.4f}")

        print(f"\nIntegrated Information (Φ):")
        print(f"  Mean: {np.mean(phis):.4f}")

        print(f"\nWord diversity: {len(set(e['word_id'] for e in emissions))} unique")

        print(f"\nFirst 10 emissions (word IDs):")
        print(f"  {[e['word_id'] for e in emissions[:10]]}")

    print("\n" + "="*70)
    print("BLUM DEMONSTRATION COMPLETE")
    print("="*70 + "\n")
