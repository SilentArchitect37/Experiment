# Technical Implementation Summary
## Language Representation in the Recursive Dialogue Engine

---

## PART 1: TOKEN CODEBOOK IMPLEMENTATION

### File: `dialogue_system.py` (lines 229-273)

```python
def _init_codebook(self) -> np.ndarray:
    """Initialize codebook for μ → token decoding"""
    # Random initialization - each token is a random point in μ space
    codebook = np.random.randn(self.config.vocab_size, self.config.state_dims)
    # Normalize for stable distances
    codebook = codebook / (np.linalg.norm(codebook, axis=1, keepdims=True) + 1e-8)
    return codebook

def decode_token(self, mu: np.ndarray) -> Tuple[int, np.ndarray]:
    """Decode μ state to nearest token in codebook"""
    # Normalize speaker state
    mu_norm = mu / (np.linalg.norm(mu) + 1e-8)
    
    # Compute squared distances to all codebook entries
    # scores = -distance (negative distance acts as logit)
    scores = -np.sum((self.codebook - mu_norm) ** 2, axis=1)
    
    # Apply TDL syntax constraints
    constrained_scores = self.tdl.apply_syntax_constraint(scores)
    
    # Select token with highest score
    token_id = np.argmax(constrained_scores)
    
    return token_id, constrained_scores

def encode_token(self, token_id: int) -> np.ndarray:
    """Encode token back to μ space for feedback loop"""
    return self.codebook[token_id]
```

**Key Properties:**
- `codebook.shape = (vocab_size, state_dims)` = (1000, 256) by default
- Each codebook entry is a unit vector in μ-space
- Decoding is L2-nearest-neighbor with TDL modulation
- Encoding is direct lookup (bijective during feedback)

**Information Loss:**
```
Input:  μ ∈ ℝ^256 (continuous, high-precision)
        Example: μ = [0.123, -0.456, ..., 0.789]

Process: Find nearest codebook entry
         argmin_i ||μ - codebook[i]||_2

Output: token_id ∈ {0, 1, ..., vocab_size-1}
        Example: token_id = 847
```

---

## PART 2: GRAMMAR CONSTRAINTS (TDL Layer)

### File: `dialogue_system.py` (lines 53-116)

```python
class TDLLayer:
    """Enforces syntactic constraints via Markov chain"""
    
    def __init__(self, vocab_size: int = 1000):
        self.vocab_size = vocab_size
        self.transition_matrix = self._init_transitions()
        self.last_token = None
    
    def _init_transitions(self) -> np.ndarray:
        """
        Initialize transition probabilities P(token_next | token_prev)
        Shape: (vocab_size, vocab_size)
        """
        # Start with uniform distribution
        trans = np.ones((self.vocab_size, self.vocab_size)) / self.vocab_size
        
        # Add small random perturbations
        trans += np.random.randn(self.vocab_size, self.vocab_size) * 0.01
        trans = np.clip(trans, 0, None)
        
        # Normalize rows (each row sums to 1)
        trans = trans / trans.sum(axis=1, keepdims=True)
        
        return trans
    
    def apply_syntax_constraint(self, token_logits: np.ndarray) -> np.ndarray:
        """
        Apply syntactic constraints to token emission probabilities.
        
        Modulates logits by transition probabilities:
        constrained_logits = logits * P(next_token | last_token)
        """
        if self.last_token is None:
            # No constraint on first token
            return token_logits
        
        # Get transition probabilities for this token
        trans_probs = self.transition_matrix[self.last_token]
        
        # Geometric mean: combine semantic (logits) with syntactic (probs)
        constrained = token_logits * trans_probs
        
        return constrained
    
    def update(self, emitted_token: int):
        """Update TDL state after emission"""
        self.last_token = emitted_token
```

**Constraints:**
- P(token_i | token_j) stored in transition_matrix[j, i]
- Only depends on immediate predecessor (first-order Markov)
- Smoothed uniform initialization (no clear language structure)
- Applied via element-wise multiplication (geometric mean)

**Limitations:**
```
Can represent:
  P(NNP | DET) = 0.4  # Noun after determiner is 40% likely
  P(VB | NNP) = 0.3   # Verb after noun is 30% likely

Cannot represent:
  - Subject-verb agreement (depends on full history, not just last token)
  - Long-distance dependencies (only looks back 1 step)
  - Constituent structure (bigram has no notion of phrases)
  - Recursive structure (relative clauses, embeddings)
```

---

## PART 3: SEMANTIC SPACE (LoMI Layer)

### File: `dialogue_system.py` (lines 118-182)

```python
class LoMILayer:
    """
    Law of Mutual Identity - maintains semantic coherence through
    phase alignment between speaker (μₛ) and listener (μₗ)
    """
    
    def __init__(self, state_dims: int = 256):
        self.state_dims = state_dims
        self.mu_listener = np.zeros(state_dims, dtype=np.float32)
        self.coherence_history = []
    
    def compute_coherence(self, mu_speaker: np.ndarray) -> float:
        """
        Compute phase coherence: Δμ = ||μₛ - μₗ||²
        
        Lower values = more coherent (mutual identity achieved)
        """
        delta = mu_speaker - self.mu_listener
        coherence_distance = np.sum(delta * delta)
        return coherence_distance
    
    def get_alignment_force(self, mu_speaker: np.ndarray) -> np.ndarray:
        """
        Compute gradient driving speaker toward listener
        (optional force to explicitly minimize Δμ)
        """
        delta = mu_speaker - self.mu_listener
        force = -2.0 * delta  # Negative gradient of ||μₛ - μₗ||²
        return force
    
    def update_listener(self, listener_input: np.ndarray):
        """
        Update listener state from external input
        (listener's utterance, speech signal, etc.)
        """
        self.mu_listener = listener_input.copy()
```

**How Semantics Emerge:**
```
Step 1: μₛ evolves via PDE
        μ_{t+1} = μ_t + g∇²μ_t - λμ_t³ + ρ(μ_t - μ_{t-1}) + η·μₗ

Step 2: Compute coherence
        Δμ = ||μₛ - μₗ||²

Step 3: When Δμ is minimized → emit token
        token = argmax logits(μₛ)

Step 4: Token encodes as feedback
        μ = μ + γ · encode(token)
```

**No Explicit Semantic Features:**
```
Traditional: "gave"
  Semantic features: [+PAST], [+AGENT], [+THEME], [+RECIPIENT], [+DITRANSITIVE]
  
Recursive Engine: "gave"
  Representation: codebook[5847] = [0.12, -0.34, 0.56, ..., 0.78]
                                     ↑      ↑      ↑         ↑
                           No explicit feature meanings. Learned density via training.
                           (But codebook is NOT trained—it's random!)
```

---

## PART 4: DYNAMICAL EVOLUTION

### File: `recursive_engine.py` (lines 88-120)

```python
class VectorizedEngine(RecursiveEngine):
    """Vectorized NumPy implementation - O(n) Laplacian"""
    
    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """Compute Laplacian using np.roll (periodic BC)"""
        dx2 = self.params.dx ** 2
        laplacian = (np.roll(mu, 1) - 2 * mu + np.roll(mu, -1)) / dx2
        return laplacian
    
    def step(self, input_vec: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Single time step of the dynamics:
        μ_{t+1} = μ_t + g∇²μ_t - λμ_t³ + ρ(μ_t - μ_{t-1}) + η·x_t
        """
        p = self.params
        
        # Compute Laplacian (diffusion)
        laplacian = self.compute_laplacian(self.mu)
        
        # Input perturbation
        input_term = 0.0 if input_vec is None else p.eta * input_vec
        
        # Clip to prevent overflow
        mu_clipped = np.clip(self.mu, -100.0, 100.0)
        cubic = mu_clipped ** 3
        momentum = self.mu - self.mu_prev
        
        # Full update equation
        mu_new = (self.mu +
                  p.dt * (p.g * laplacian -
                          p.lam * cubic +
                          p.rho * momentum) +
                  p.dt * input_term)
        
        # Clip output
        mu_new = np.clip(mu_new, -100.0, 100.0)
        
        # Update state
        self.mu_prev = self.mu
        self.mu = mu_new
        self.t += 1
        
        return self.mu
```

**Equation Components:**
```
dμ/dt = g·∇²μ - λ·μ³ + ρ·(μ_t - μ_{t-1}) + η·x_t
         ↑        ↑      ↑                  ↑
     Diffusion  Cubic  Momentum           Input

- Diffusion (g∇²μ): Smooths μ across spatial dimensions
  Creates coherence, long-range coupling
  
- Cubic (-λμ³): Creates bistability (three fixed points: 0, ±√(g/λ))
  Interprets as: multiple semantic states, competing attractors
  
- Momentum (ρ(μ-μ_prev)): Temporal continuity
  Interprets as: dialogue coherence, semantic continuity
  
- Input (η·x): Listener coupling
  x = μ_listener (perturbation from other speaker)
```

**No Explicit Linguistic Interpretation:**
- All 256 dimensions treated identically
- No designated dimension for tense, aspect, mood, etc.
- No way to represent part-of-speech categories
- Meaning emerges purely from PDE dynamics, not structure

---

## PART 5: EMISSION CRITERION

### File: `emission_detector.py` (lines 62-165)

```python
class EmissionDetector:
    """Detects stable points for token emission"""
    
    def compute_entropy(self, mu: np.ndarray) -> float:
        """
        Recursive entropy: S_R = -k_R Σ μ² ln(μ²)
        
        Measures information content of the state.
        Stable points → dS_R/dt ≈ 0 → good emission points
        """
        eps = 1e-8
        mu_sq = mu * mu
        entropy = -np.sum(mu_sq * np.log(mu_sq + eps))
        return entropy
    
    def estimate_entropy_derivative(self) -> Optional[float]:
        """
        Estimate dS_R/dt using finite differences
        
        Emit when |dS_R/dt| < threshold (stable point)
        """
        if len(self.entropy_history) < 2:
            return None
        
        entropies = list(self.entropy_history)
        times = list(self.time_history)
        
        if len(entropies) >= 3:
            # Central difference
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
        Main emission criterion:
        Emit when: |dS_R/dt| < entropy_threshold AND energy_min < E < energy_max
        """
        entropy = self.compute_entropy(mu)
        energy = np.sum(mu * mu)
        
        self.entropy_history.append(entropy)
        self.time_history.append(t)
        
        diagnostics = {
            'entropy': entropy,
            'energy': energy,
            'entropy_derivative': None,
            'reason': None
        }
        
        # Check cooldown (minimum steps between emissions)
        if self.steps_since_emission < self.config.cooldown_steps:
            return False, diagnostics
        
        # Compute entropy derivative
        dS_dt = self.estimate_entropy_derivative()
        
        # Check stability
        if abs(dS_dt) < self.config.entropy_threshold:
            # EMIT!
            self.steps_since_emission = 0
            diagnostics['reason'] = 'emission'
            return True, diagnostics
        
        diagnostics['reason'] = 'entropy_unstable'
        return False, diagnostics
```

**Emission Logic:**
```
Cycle:
  1. Compute S_R = -Σ μ² ln(μ²)
  2. Estimate dS_R/dt ≈ (S[t] - S[t-2]) / 2Δt
  3. If |dS_R/dt| < threshold:  → EMIT TOKEN
  4. Token fed back: μ ← μ + γ·encode(token)
  5. New recursion cycle begins

Rationale:
  - Stable points → dS_R/dt ≈ 0 → fixed points → "coherent meanings"
  - Unstable regions → dS_R/dt large → skipped
```

**Missing:**
- No linguistic interpretation of entropy
- No explicit content in emitted tokens (just nearest neighbor)
- No semantic drift or compositional meaning

---

## PART 6: COMPLETE INTEGRATION

### File: `dialogue_system.py` (lines 275-342)

```python
def step(self, listener_input: Optional[np.ndarray] = None) -> Optional[Dict]:
    """
    Complete dialogue step integrating all three layers:
    1. TDL (syntax constraints)
    2. LoMI (semantic coherence)
    3. I² (recursive emission)
    """
    
    # LOMI: Update listener state from external input
    if listener_input is not None:
        self.lomi.update_listener(listener_input)
    
    if isinstance(self.detector, PhaseCoherenceDetector):
        self.detector.set_listener_state(self.lomi.mu_listener)
    
    # I²: Compute effective input (listener perturbation)
    effective_input = self.lomi.mu_listener * 0.1
    
    # I²: Evolve dynamics
    mu_new = self.engine.step(input_vec=effective_input)
    
    # I²: Check for emission
    should_emit, diagnostics = self.detector.should_emit(mu_new, self.t)
    self.t += 1
    
    if should_emit:
        # TDL + Codebook: Decode μ → token
        token_id, token_scores = self.decode_token(mu_new)
        
        # TDL: Update state (track last token)
        self.tdl.update(token_id)
        
        # Create emission record
        emission = {
            'time': self.t,
            'token': token_id,
            'mu_state': mu_new.copy(),
            'diagnostics': diagnostics,
            'coherence': self.lomi.compute_coherence(mu_new)
        }
        
        self.emission_history.append(emission)
        
        # I²: Feedback (reflection stimulus)
        # Emitted token re-enters dynamics
        token_vec = self.encode_token(token_id)
        feedback = token_vec * self.config.feedback_decay
        
        # Add feedback to next iteration
        self.engine.mu = self.engine.mu + feedback * 0.1
        
        return emission
    
    return None
```

**Pipeline Diagram:**
```
Input: listener_input (256-dim vector)
    ↓
LoMI: Update μ_listener
    ↓
I²: Evolve μ_speaker via PDE (g∇²μ - λμ³ + ρ(μ-μ_prev) + η·μ_listener)
    ↓
I²: Compute entropy S_R = -Σμ²ln(μ²)
    ↓
I²: Check if dS_R/dt < threshold (stable point?)
    ↓
IF YES → EMIT:
    ├─ TDL: Normalize μ
    ├─ Codebook: Find nearest entry
    ├─ TDL: Apply transition constraints
    ├─ Select: token = argmax(scores)
    ├─ Feedback: μ ← μ + γ·codebook[token]
    └─ Output: token_id, coherence, diagnostics
    
IF NO → Continue to next step
```

---

## SUMMARY: Information Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 RECURSIVE DIALOGUE ENGINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Input (Listener):                                          │
│  listener_input → μ_listener (256-dim) ←─────────┐         │
│                      ↓                           │         │
│  Dynamics (I² Layer):                           │         │
│  μ_{t+1} = μ_t + g∇²μ_t - λμ_t³ + ρΔμ + η·μ_l │         │
│        (256-dim continuous evolution)            │         │
│                      ↓                           │         │
│  Emission Detection (I² Layer):                 │         │
│  S_R = -Σμ²ln(μ²)                              │         │
│  Emit if: |dS_R/dt| < threshold                │         │
│                      ↓                           │         │
│  Token Decoding (TDL + Codebook):              │         │
│  - Normalize μ                                   │         │
│  - Find nearest: argmin ||μ - codebook[i]||    │         │
│  - Apply grammar: multiply by P(next|last)     │         │
│  - Select: argmax(scores)                       │         │
│                      ↓                           │         │
│  Output:                                         │         │
│  token_id (0-999) ──────────────────────────────┘         │
│                      ↓                                       │
│  Feedback (I² Layer):                                      │
│  μ = μ + γ · codebook[token_id]  (reflection stimulus)    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**What's Encoded:**
- ✓ Dynamics: PDE with diffusion, nonlinearity, momentum
- ✓ Emission timing: Entropy stability criterion
- ✓ Basic grammar: Bigram Markov chain (TDL)
- ✓ Feedback loop: Token re-enters as perturbation

**What's Missing:**
- ✗ Semantic features: Tense, aspect, mood, modality
- ✗ Compositional semantics: No principled combination rules
- ✗ Hierarchical structure: Single flat space
- ✗ Linguistic constraints: Only statistical smoothing
- ✗ Pragmatic dimensions: No speech acts, affect, or intention

