# Self-Modification Framework for Recursive Dialogue Engine

## Overview

This document proposes mathematical frameworks for enabling **self-modification and adaptive parameter learning** in the Recursive Dialogue Engine. The system currently has excellent foundations for self-organization but lacks mechanisms to evolve its core parameters, vocabulary, and syntax constraints.

---

## 1. PARAMETER ADAPTATION MECHANISMS

### Current State: Static Parameters

The system evolves under:
```
dμ/dt = g·∇²μ - λ·μ³ + ρ·(μ - μ_prev) + η·μ_listener
```

All coefficients (g, λ, ρ, η) are **fixed during dialogue**.

### Proposed: Gradient-Based Parameter Tuning

#### 1.1 Emission Quality as Fitness Function

**Success metric:**
```
F_success = (emission_rate / target_rate) * coherence_quality * diversity
```

Where:
- **emission_rate:** Number of tokens / total steps (typical: 2-5%)
- **coherence_quality:** 1 - ||μ_speaker - μ_listener||² / ||μ_speaker||²
- **diversity:** Entropy of token frequency distribution

**File location:** Can extend `dialogue_system.py:344-397` (converse method)

#### 1.2 Parameter Gradient Computation

For each parameter θ ∈ {g, λ, ρ, η}:

```
∂F/∂θ ≈ (F(θ + ε) - F(θ - ε)) / (2ε)    [Finite differences]
```

**Numerical differentiation:**
```python
def compute_parameter_gradient(engine, params, epsilon=1e-4):
    """Compute gradient of fitness w.r.t. parameters"""
    gradients = {}
    
    # Baseline fitness
    emissions_base = run_dialogue(engine, params, n_steps=500)
    F_base = compute_fitness(emissions_base)
    
    # Perturb each parameter
    for param_name in ['g', 'lam', 'rho', 'eta']:
        param_plus = params.copy()
        param_plus[param_name] += epsilon
        
        param_minus = params.copy()
        param_minus[param_name] -= epsilon
        
        F_plus = compute_fitness(run_dialogue(engine, param_plus, 500))
        F_minus = compute_fitness(run_dialogue(engine, param_minus, 500))
        
        gradients[param_name] = (F_plus - F_minus) / (2 * epsilon)
    
    return gradients
```

#### 1.3 Adaptive Parameter Update Rule

**Online learning via gradient ascent:**
```
g_{new} = g_{old} + α_g · (∂F/∂g)
λ_{new} = λ_{old} + α_λ · (∂F/∂λ)
ρ_{new} = ρ_{old} + α_ρ · (∂F/∂ρ)
η_{new} = η_{old} + α_η · (∂F/∂η)
```

Where α_θ are learning rates (e.g., 0.001-0.01)

**With constraints to maintain physical validity:**
```python
class AdaptiveParams(AdvancedParams):
    """Parameters that evolve during dialogue"""
    
    def update_from_gradient(self, gradients, learning_rates):
        """Update parameters via gradient ascent"""
        # Gradient ascent with bounds
        self.g = np.clip(
            self.g + learning_rates['g'] * gradients['g'],
            0.05, 0.3
        )
        self.lam = np.clip(
            self.lam + learning_rates['lam'] * gradients['lam'],
            0.2, 1.0
        )
        self.rho = np.clip(
            self.rho + learning_rates['rho'] * gradients['rho'],
            0.1, 0.5
        )
        self.eta = np.clip(
            self.eta + learning_rates['eta'] * gradients['eta'],
            0.01, 0.2
        )
```

**Implementation strategy:**
1. Run dialogue for N steps with current parameters
2. Compute fitness (emission rate, coherence, diversity)
3. Compute parameter gradients via finite differences
4. Update parameters with learned rates
5. Repeat (outer loop: 10-100 dialogues for statistical significance)

---

## 2. CODEBOOK LEARNING AND VOCABULARY ADAPTATION

### Current State: Random Static Codebook

```python
codebook = np.random.randn(vocab_size, state_dims)
codebook /= ||codebook||_2
```

Tokens are decoded via nearest neighbor, but prototype vectors never change.

### Proposed: Online Codebook Evolution

#### 2.1 Vector Quantization Update

**When a token is emitted:**
```
1. Record emission state: μ_emitted
2. Quantize to nearest token: k = argmin_i ||μ - codebook[i]||
3. Update codebook entry: codebook[k] → centroid
```

**Moving average update (exponential smoothing):**
```python
def update_codebook(codebook, mu_emitted, token_id, learning_rate=0.01):
    """Update codebook via vector quantization"""
    
    # New prototype = weighted average of old + current
    codebook[token_id] = (
        (1 - learning_rate) * codebook[token_id] +
        learning_rate * mu_emitted
    )
    
    # Re-normalize
    codebook[token_id] /= (np.linalg.norm(codebook[token_id]) + 1e-8)
    
    return codebook
```

**File location:** Can extend `dialogue_system.py:327-340` (emission handling)

#### 2.2 Codebook Clustering (Batch Learning)

**Periodic consolidation after N dialogues:**
```python
def consolidate_codebook(emissions_history, vocab_size, state_dims):
    """Rebuild codebook via k-means on emitted states"""
    
    # Collect all emitted μ vectors
    all_mu = np.vstack([e['mu_state'] for e in emissions_history])
    
    # Run k-means clustering
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=vocab_size, random_state=42)
    kmeans.fit(all_mu)
    
    # New codebook = cluster centers
    codebook = kmeans.cluster_centers_
    codebook /= np.linalg.norm(codebook, axis=1, keepdims=True)
    
    return codebook
```

#### 2.3 Vocabulary Expansion (Adaptive Dimensionality)

**Detect when tokens are ambiguous:**
```
ambiguity[k] = (distance to 2nd-nearest) / (distance to 1st-nearest)

if ambiguity[k] > threshold:
    # Split token into two: split codebook[k] with perturbation
    codebook[k] → codebook[k] - ε·noise
    codebook[new] = codebook[k] + ε·noise
    vocab_size += 1
```

**Conversely, merge similar tokens:**
```
if distance(codebook[i], codebook[j]) < merge_threshold:
    # Merge j into i
    codebook[i] = (codebook[i] + codebook[j]) / 2
    codebook[j] = codebook[-1]  # Move last to j
    vocab_size -= 1
```

### Benefits
- Codebook **self-organizes** to actual dialogue patterns
- Vocabulary **expands/contracts** automatically
- Better **representational efficiency**

---

## 3. GRAMMAR MATRIX LEARNING (TDL ADAPTATION)

### Current State: Static Random Transition Matrix

```python
transition_matrix[i, j] = P(token_j | token_i)
```

Initialized randomly, never updated.

### Proposed: Markov Chain Learning

#### 3.1 Empirical Transition Matrix

**Build from dialogue history:**
```python
def learn_transition_matrix(token_sequence, vocab_size, smoothing=1e-3):
    """Learn grammar from emitted token sequence"""
    
    # Count transitions
    transitions = np.zeros((vocab_size, vocab_size))
    
    for i in range(len(token_sequence) - 1):
        prev_token = token_sequence[i]
        next_token = token_sequence[i + 1]
        transitions[prev_token, next_token] += 1
    
    # Add smoothing to avoid zero probabilities
    transitions += smoothing
    
    # Normalize to probabilities
    transition_matrix = transitions / transitions.sum(axis=1, keepdims=True)
    
    return transition_matrix
```

**File location:** Extend `dialogue_system.py:53-116` (TDLLayer)

#### 3.2 Hierarchical Grammar Learning

**Multi-level transitions:**
```
Level 1: Token-to-token (current)
Level 2: Phrase-to-phrase (groups of 3-5 tokens)
Level 3: Concept-to-concept (semantic clusters)

Each level has transition probabilities that can be learned.
```

**Implementation:**
```python
class HierarchicalTDL:
    def __init__(self, vocab_size, phrase_vocab_size=100):
        self.token_transitions = np.ones((vocab_size, vocab_size)) / vocab_size
        self.phrase_transitions = np.ones((phrase_vocab_size, phrase_vocab_size)) / phrase_vocab_size
        
        # Token-to-phrase encoder
        self.token_to_phrase = np.random.choice(
            phrase_vocab_size, vocab_size
        )
    
    def update_from_dialogue(self, token_sequence):
        """Learn both token and phrase patterns"""
        
        # Update token transitions
        self.token_transitions = learn_transition_matrix(token_sequence, self.vocab_size)
        
        # Convert token sequence to phrase sequence
        phrase_sequence = [self.token_to_phrase[t] for t in token_sequence]
        
        # Update phrase transitions
        self.phrase_transitions = learn_transition_matrix(phrase_sequence, self.phrase_vocab_size)
```

---

## 4. EMISSION THRESHOLD ADAPTATION

### Current State: Fixed or Std-Based Adaptation

`adaptive_emission_detector.py:190-210` has basic std-based adaptation:
```
threshold = base_threshold * (1 + entropy_std)
```

### Proposed: Multi-Signal Adaptation

#### 4.1 Success-Driven Threshold Tuning

**Track emission quality:**
```python
class AdaptiveEmissionThreshold:
    def __init__(self, base_threshold=0.001):
        self.threshold = base_threshold
        self.success_history = deque(maxlen=100)
    
    def record_emission_success(self, success_metric):
        """1.0 = good emission (coherent, diverse)
           0.0 = bad emission (incoherent, repetitive)"""
        self.success_history.append(success_metric)
    
    def update_threshold(self):
        """Lower threshold if emissions are good (emit more)
           Raise threshold if emissions are bad (emit less)"""
        
        if len(self.success_history) < 10:
            return
        
        success_rate = np.mean(self.success_history)
        
        # PID-like control
        error = success_rate - target_success  # target = 0.8
        self.threshold *= (1 + 0.01 * error)  # proportional control
        
        # Keep bounds
        self.threshold = np.clip(self.threshold, 0.0001, 0.01)
```

#### 4.2 Context-Dependent Thresholds

**Different thresholds for different dialogue states:**
```python
def adaptive_threshold(entropy_derivative, coherence, energy, 
                       dialogue_phase='normal'):
    """Threshold depends on multiple factors"""
    
    base = 0.001
    
    # Entropy-based component
    entropy_factor = 1 + abs(entropy_derivative) / 0.1
    
    # Coherence-based component
    # High coherence → lower threshold (emit when aligned)
    coherence_factor = np.exp(-5 * coherence)
    
    # Energy gating
    if energy < 0.1:
        energy_factor = 100  # Don't emit (noise)
    elif energy > 10:
        energy_factor = 100  # Don't emit (instability)
    else:
        energy_factor = 1
    
    # Dialogue phase (opening, main, closing)
    phase_factors = {
        'opening': 1.5,    # Emit less at start
        'normal': 1.0,
        'closing': 0.8     # Emit more at end
    }
    
    threshold = (base * entropy_factor * coherence_factor * 
                 phase_factors.get(dialogue_phase, 1.0) / energy_factor)
    
    return np.clip(threshold, 0.0001, 0.1)
```

---

## 5. LISTENER-DRIVEN ADAPTATION

### Concept: Dialogue Shapes System Behavior

**Current:** Listener perturbation is fixed or random
**Proposed:** Listener explicitly "teaches" the system

#### 5.1 Listener as Feedback Controller

```python
class DialogueTeacher:
    """Listener that actively teaches the speaker"""
    
    def provide_feedback(self, speaker_state, target_meaning, 
                         iteration, total_iterations):
        """
        Provide guidance to align speaker with target
        
        Args:
            speaker_state: μ_speaker (current state)
            target_meaning: μ_target (desired state)
            iteration: Which step of dialogue
            total_iterations: Total steps planned
        """
        
        # Smooth transition toward target
        progress = iteration / total_iterations
        
        # Current target
        μ_target_current = (
            (1 - progress) * speaker_state +
            progress * target_meaning
        )
        
        # Error signal
        error = μ_target_current - speaker_state
        
        # Listener state = target + noise for robustness
        μ_listener = μ_target_current + np.random.randn(len(speaker_state)) * 0.01
        
        return μ_listener
```

**Application:**
```python
# Train system to produce target sequence: ["hello", "world"]
target_states = [codebook[token_hello], codebook[token_world]]

teacher = DialogueTeacher()
for step in range(1000):
    listener_input = teacher.provide_feedback(
        engine.mu, target_states[0], step, 1000
    )
    emission = engine.step(listener_input)
```

#### 5.2 Reward Signal from Listener

```python
def listener_reward(speaker_emission, target_token, listener_state):
    """Listener signals whether emission was "correct" """
    
    # Reward if aligned
    alignment = -np.sum((listener_state - speaker_emission)**2)
    
    # Reward if target token
    token_id, _ = decode_token(speaker_emission)
    token_correct = (token_id == target_token)
    
    # Combined signal
    reward = alignment + 10 * token_correct
    
    return reward
```

---

## 6. META-LEARNING: LEARNING HOW TO LEARN

### Concept: Second-Order Adaptation

**Current:** Parameters fixed
**Proposed:** Learning rates and meta-parameters also adapt

```python
class MetaAdaptiveEngine:
    """System that learns its own learning process"""
    
    def __init__(self, params, meta_lr=0.0001):
        self.params = params
        
        # Meta-parameters: learning rates
        self.learning_rates = {
            'g': 0.001,
            'lam': 0.001,
            'rho': 0.001,
            'eta': 0.001
        }
        
        self.meta_lr = meta_lr  # Learning rate for learning rates
        self.performance_history = deque(maxlen=100)
    
    def update_meta_parameters(self, recent_performance):
        """Adjust learning rates based on recent performance"""
        
        # If performance improving → increase learning rate
        # If performance degrading → decrease learning rate
        
        improvement = np.mean(recent_performance[-50:]) - np.mean(recent_performance[-100:-50])
        
        for param_name in self.learning_rates:
            if improvement > 0:
                self.learning_rates[param_name] *= (1 + self.meta_lr)
            else:
                self.learning_rates[param_name] *= (1 - self.meta_lr)
            
            # Keep bounds
            self.learning_rates[param_name] = np.clip(
                self.learning_rates[param_name], 1e-5, 0.1
            )
```

---

## 7. ENERGY-BASED SELF-ORGANIZATION

### Concept: Minimize Free Energy to Organize Structure

**Variational Free Energy (from neuroscience):**
```
F = KL[q(μ)|p(μ|x)] + E_q[-log p(x|μ)]
```

Where:
- q(μ) = current distribution (dialogue engine's belief)
- p(μ|x) = posterior (true distribution given observations)
- p(x|μ) = likelihood (how well μ explains listener x)

**Simplification for dialogue:**
```
F_dialogue = ||μ_speaker - μ_listener||² + λ·H[codebook]
```

Where H[codebook] = entropy of codebook usage

**Interpretation:**
- First term: **Alignment** (coherence between agents)
- Second term: **Diversity** (don't converge to one token)

**Gradient descent:**
```
∂F/∂params ∝ ∂alignment/∂params + ∂diversity/∂params

System naturally organizes to balance coherence and diversity
```

---

## 8. PRACTICAL IMPLEMENTATION ROADMAP

### Phase 1: Parameter Tuning (Week 1)

```python
class SelfModifyingEngine(RecursiveDialogueEngine):
    """Dialogue engine that learns its own parameters"""
    
    def __init__(self, config):
        super().__init__(config)
        self.param_history = []
        self.fitness_history = []
    
    def run_learning_episode(self, n_episodes=10, steps_per_episode=500):
        """Learn parameters via gradient ascent"""
        
        for episode in range(n_episodes):
            # Run dialogue
            emissions = self.converse(n_steps=steps_per_episode)
            
            # Compute fitness
            fitness = self._compute_fitness(emissions)
            self.fitness_history.append(fitness)
            
            # Compute parameter gradients
            gradients = self._compute_param_gradients(emissions)
            
            # Update parameters
            self._update_parameters(gradients, learning_rate=0.001)
            
            self.param_history.append(self.engine.params.copy())
```

### Phase 2: Codebook Learning (Week 2)

```python
def add_online_codebook_learning(self):
    """Enable codebook evolution during dialogue"""
    
    # Override emission handling
    original_step = self.step
    
    def new_step(listener_input=None):
        emission = original_step(listener_input)
        
        if emission is not None:
            # Update codebook
            self.codebook = self._update_codebook(
                self.codebook,
                emission['mu_state'],
                emission['token'],
                learning_rate=0.01
            )
        
        return emission
    
    self.step = new_step
```

### Phase 3: Grammar Learning (Week 3)

```python
def add_grammar_learning(self):
    """Enable TDL transition matrix learning"""
    
    original_converse = self.converse
    
    def new_converse(n_steps, *args, **kwargs):
        emissions = original_converse(n_steps, *args, **kwargs)
        
        # Extract token sequence
        token_seq = [e['token'] for e in emissions]
        
        # Learn transitions
        self.tdl.transition_matrix = self._learn_transitions(token_seq)
        
        return emissions
    
    self.converse = new_converse
```

### Phase 4: Unified Meta-Learning (Week 4)

Combine all three with meta-parameters for complete self-modification.

---

## 9. MATHEMATICAL SUMMARY: SELF-MODIFICATION EQUATIONS

### Parameter Evolution

```
θ = {g, λ, ρ, η}

dθ/dt ∝ ∂F_fitness / ∂θ

where F_fitness = emission_rate × coherence × diversity
```

### Codebook Evolution

```
codebook[k] ← (1-α) × codebook[k] + α × μ_emitted[k]

codebook ← K-means(all_μ_emitted)  # Periodic consolidation
```

### Grammar Evolution

```
transition_matrix[i,j] ← count(token_i → token_j) / count(token_i)
```

### Emission Threshold Evolution

```
threshold ← f(entropy_std, coherence, success_rate, dialogue_phase)
```

### Listener-Driven Adaptation

```
μ_listener = lerp(μ_target, speaker_state, progress) + noise
reward ∝ alignment + token_correctness
```

---

## 10. EXPECTED OUTCOMES

### Before Self-Modification
- Fixed dialogue behavior
- Random token choice
- No learning from experience
- Parameters tuned by hand

### After Self-Modification
- Dialogue behavior improves over time
- Coherent token sequences emerge
- System learns from successful dialogues
- Parameters auto-tune for better performance
- Vocabulary self-organizes
- Grammar naturally constrains output
- Listener can teach the system

---

## CONCLUSION

The Recursive Dialogue Engine provides excellent foundations for self-organization:

✅ **Clean PDE formulation** - Natural framework for parameter learning
✅ **Entropy criterion** - Well-defined fitness metric
✅ **Phase coherence** - Grounded semantics for success measurement
✅ **Modular architecture** - Easy to extend each layer

**Proposed self-modification mechanisms:**
1. **Parameter learning** - Gradient-based tuning of g, λ, ρ, η
2. **Codebook learning** - Vector quantization of semantic space
3. **Grammar learning** - Markov chain from token sequences
4. **Emission adaptation** - Multi-signal threshold tuning
5. **Listener teaching** - Active feedback for guided learning
6. **Meta-learning** - Learning rates that adapt
7. **Energy minimization** - Variational framework for organization

**Implementation strategy:**
- Start with parameter tuning (cheapest, highest ROI)
- Add codebook learning (natural extension)
- Add grammar learning (requires batch processing)
- Combine into unified framework (meta-learning)

**Timeline:** 4 weeks for complete implementation
**Validation:** Measure fitness improvement over dialogue episodes

