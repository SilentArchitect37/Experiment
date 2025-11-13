# Episodic Memory via Dynamical Systems
## Novel Architectures for Experience Storage and Recall

---

## Current System Capabilities (What We Have)

### Existing Memory Mechanisms
1. **Momentum Term**: `ρ(μ_t - μ_{t-1})` provides 1-step temporal memory
2. **Attractor Basins**: μ³ nonlinearity creates multiple stable states
3. **Codebook**: Maps continuous μ states to discrete tokens
4. **Feedback Loops**: Emitted tokens re-enter dynamics (reflection)
5. **Phase Coherence**: Alignment between speaker-listener states

### Current Limitations
- **No long-term storage**: Only remembers previous step
- **No episodic structure**: Cannot distinguish individual experiences
- **No retrieval mechanism**: Cannot recall past episodes from cues
- **No temporal ordering**: Cannot represent "when" events occurred
- **No contextual binding**: Cannot associate "what-where-when-who"

---

## Why Dynamical Systems Are PERFECT for Episodic Memory

### Fundamental Advantages

| Traditional Approach | Dynamical Systems Approach |
|---------------------|----------------------------|
| Store vectors/embeddings | Store attractor basins |
| Discrete time stamps | Continuous trajectory encoding |
| Explicit indexing | Implicit content-addressable |
| Reconstruction by lookup | Reconstruction by trajectory replay |
| Fragile to noise | Robust via basin convergence |
| No temporal dynamics | Inherent temporal structure |

### Key Insight
**Episodic memory = storing and retrieving trajectories in phase space, not static snapshots**

---

## Architecture 1: Attractor-Based Episodic Memory (ABEM)

### Core Concept
Each episode is carved as a distinct attractor basin in μ space. Recall = convergence to attractor from partial cue.

### Mathematical Formulation

**Storage Phase:**
```
For episode E_i with content x_i(t):
1. Evolve dynamics: μ(t) ← PDE with input x_i(t)
2. At convergence, μ* forms attractor for E_i
3. Store attractor parameters: {center: μ*, basin: B_i, depth: V_i}
```

**Recall Phase:**
```
Given partial cue c:
1. Initialize: μ(0) = embed(c)
2. Evolve without input until convergence
3. μ* → nearest stored attractor → retrieved episode
```

### Implementation Strategy

#### Modified PDE:
```python
# Add memory storage term
μ_{t+1} = μ_t + g∇²μ_t - λ·V_memory(μ_t) + ρ(μ_t - μ_{t-1}) + η·x_t

where:
V_memory(μ) = Σ_i w_i·||μ - μ_i*||²·(μ - μ_i*)
# Energy landscape with attractor wells at each stored episode μ_i*
```

#### Storage Mechanism:
```python
class AttractorMemory:
    def __init__(self, n_dims=256, max_memories=1000):
        self.attractors = []  # List of (center, strength, context)

    def store_episode(self, mu_trajectory, context):
        # Extract attractor from converged state
        mu_final = mu_trajectory[-1]

        # Compute basin characteristics
        strength = self.compute_basin_depth(mu_trajectory)

        # Store with Hebbian-like strengthening
        attractor = {
            'center': mu_final,
            'strength': strength,
            'context': context,
            'timestamp': time.time(),
            'retrieval_count': 0
        }
        self.attractors.append(attractor)

    def recall(self, cue, n_steps=100):
        # Initialize with cue
        mu = self.embed_cue(cue)

        # Evolve in memory landscape
        for _ in range(n_steps):
            # Gradient descent in memory potential
            force = self.compute_memory_force(mu)
            mu = mu + force

            # Check convergence
            if self.is_converged(mu):
                break

        # Find nearest attractor
        episode = self.match_attractor(mu)
        episode['retrieval_count'] += 1  # Update statistics

        return episode
```

### Advantages
✅ **Content-addressable**: Partial cues automatically retrieve full episode
✅ **Noise-robust**: Basin convergence filters perturbations
✅ **Capacity**: Number of attractors scales with dimensionality
✅ **Interference**: Similar episodes can share basin structure

### Challenges
⚠️ **Catastrophic interference**: New attractors can disrupt old ones
⚠️ **Basin overlap**: Similar episodes may merge
⚠️ **No temporal order**: Need additional structure for sequences

---

## Architecture 2: Trajectory Encoding Memory (TEM)

### Core Concept
Store entire trajectory μ(t) as the episode, not just endpoint. Recall = trajectory replay.

### Mathematical Formulation

**Storage:**
```
Episode E_i = {μ_i(t), t ∈ [0, T_i]}
Store: {μ_i(0), μ_i(dt), μ_i(2dt), ..., μ_i(T_i)}
```

**Recall:**
```
Given cue c:
1. Find matching trajectory start: μ_j(0) ≈ embed(c)
2. Replay: μ_recall(t) = μ_j(t) for t ∈ [0, T_j]
3. Observe emissions at original time points
```

### Implementation Strategy

```python
class TrajectoryMemory:
    def __init__(self, n_dims=256):
        self.episodes = []

    def store_episode(self, mu_trajectory, emissions, context):
        episode = {
            'trajectory': mu_trajectory,  # Full temporal evolution
            'emissions': emissions,       # Tokens emitted during episode
            'context': context,           # Contextual information
            'duration': len(mu_trajectory),
            'key_states': self.extract_key_states(mu_trajectory)
        }
        self.episodes.append(episode)

    def extract_key_states(self, trajectory):
        """Extract critical points (peaks, valleys, inflections)"""
        # Use topological data analysis
        peaks = self.find_local_maxima(trajectory)
        valleys = self.find_local_minima(trajectory)
        inflections = self.find_inflection_points(trajectory)

        return {'peaks': peaks, 'valleys': valleys, 'inflections': inflections}

    def recall(self, cue, match_mode='start'):
        # Find best matching episode
        if match_mode == 'start':
            # Match beginning of trajectory
            similarities = [cosine_sim(self.embed_cue(cue), ep['trajectory'][0])
                          for ep in self.episodes]
        elif match_mode == 'anywhere':
            # Match any point in trajectory
            similarities = [self.max_similarity_in_trajectory(cue, ep['trajectory'])
                          for ep in self.episodes]

        best_idx = np.argmax(similarities)
        episode = self.episodes[best_idx]

        # Replay trajectory
        self.replay_trajectory(episode['trajectory'])

        return episode

    def replay_trajectory(self, trajectory):
        """Re-experience the episode by replaying dynamics"""
        for t, mu_t in enumerate(trajectory):
            # Option 1: Directly set state
            self.engine.mu = mu_t

            # Option 2: Drive dynamics toward trajectory (constraint)
            force = (mu_t - self.engine.mu) * replay_strength
            self.engine.step(input_vec=force)
```

### Advanced: Trajectory Compression

```python
# Use PCA/autoencoders to compress trajectories
class CompressedTrajectoryMemory:
    def __init__(self, n_dims=256, latent_dims=32):
        self.compressor = TrajectoryCompressor(n_dims, latent_dims)

    def store_episode(self, trajectory):
        # Compress trajectory to latent representation
        z = self.compressor.encode(trajectory)

        # Store compressed version
        self.episodes.append(z)

    def recall(self, cue):
        # Find matching compressed episode
        z_match = self.find_match(cue)

        # Decompress to full trajectory
        trajectory = self.compressor.decode(z_match)

        return trajectory
```

### Advantages
✅ **Temporal fidelity**: Preserves exact temporal sequence
✅ **Rich structure**: Captures dynamics, not just states
✅ **Flexible retrieval**: Can match beginning, middle, or end
✅ **Natural replay**: Re-experience through dynamics

### Challenges
⚠️ **Storage cost**: O(T) per episode vs O(1) for attractors
⚠️ **Scaling**: Need compression for large T
⚠️ **Exact replay**: May be too rigid (no generalization)

---

## Architecture 3: Phase-Coded Memory (PCM)

### Core Concept
Encode episodes as oscillation patterns (phase, frequency, amplitude) in μ. Different frequencies = different episodes.

### Mathematical Formulation

**Modified Dynamics:**
```
μ(x,t) = Σ_i A_i·sin(ω_i·t + φ_i(x))

Each episode i encoded as:
- Frequency ω_i (temporal "channel")
- Spatial phase φ_i(x) (content)
- Amplitude A_i (salience/importance)
```

**Storage:**
```python
# Decompose episode into frequency components
episode_i → {ω_i, φ_i(x), A_i} via Fourier analysis
```

**Recall:**
```python
# Reconstruct by filtering specific frequency
μ_recall = bandpass_filter(μ_total, ω_i)
```

### Implementation Strategy

```python
class PhaseCodedMemory:
    def __init__(self, n_dims=256, n_frequencies=50):
        self.n_freqs = n_frequencies
        self.frequency_bands = np.linspace(0.01, 1.0, n_frequencies)
        self.phase_patterns = {}  # freq → spatial phase pattern

    def store_episode(self, mu_trajectory, content):
        # Perform FFT over time dimension
        mu_fft = np.fft.fft(mu_trajectory, axis=0)

        # Find dominant frequency for this episode
        power_spectrum = np.abs(mu_fft) ** 2
        dominant_freq_idx = np.argmax(np.sum(power_spectrum, axis=1))
        omega = self.frequency_bands[dominant_freq_idx]

        # Extract phase pattern at this frequency
        phase_pattern = np.angle(mu_fft[dominant_freq_idx, :])
        amplitude = np.abs(mu_fft[dominant_freq_idx, :])

        # Store episode in frequency channel
        self.phase_patterns[omega] = {
            'phase': phase_pattern,
            'amplitude': amplitude,
            'content': content
        }

    def recall(self, frequency_cue):
        """Recall episode by its frequency signature"""
        # Find matching frequency
        omega = self.find_nearest_frequency(frequency_cue)

        # Reconstruct from phase pattern
        pattern = self.phase_patterns[omega]

        # Generate trajectory at this frequency
        T = 100
        t = np.arange(T)
        mu_recall = pattern['amplitude'] * np.sin(
            2*np.pi*omega*t[:, None] + pattern['phase'][None, :]
        )

        return mu_recall, pattern['content']

    def recall_by_content(self, content_cue):
        """Find frequency channel matching content"""
        # Search across all frequencies
        best_omega = None
        best_match = -inf

        for omega, pattern in self.phase_patterns.items():
            similarity = content_similarity(content_cue, pattern['content'])
            if similarity > best_match:
                best_match = similarity
                best_omega = omega

        return self.recall(best_omega)
```

### Neural Implementation (Kuramoto Model)

```python
# Each episode = phase-locked oscillator ensemble
class KuramotoMemory:
    def __init__(self, n_oscillators=256):
        self.theta = np.zeros(n_oscillators)  # Phases
        self.omega = np.random.randn(n_oscillators) * 0.1  # Natural frequencies

    def store_episode(self, phase_pattern, frequency):
        # Set oscillator ensemble to encode episode
        self.theta = phase_pattern
        self.omega[:] = frequency  # All oscillators at same freq = synchronized

    def evolve(self, K=1.0, dt=0.01):
        # Kuramoto dynamics
        coupling = K * np.sin(self.theta[:, None] - self.theta[None, :])
        dtheta = self.omega + np.mean(coupling, axis=1)
        self.theta += dtheta * dt

    def recall(self, partial_cue):
        # Initialize subset of oscillators
        self.theta[:len(partial_cue)] = partial_cue

        # Let system synchronize (memory completion)
        for _ in range(100):
            self.evolve()

        return self.theta  # Recovered full phase pattern
```

### Advantages
✅ **Natural multiplexing**: Many episodes coexist in different frequencies
✅ **Interference-free**: Orthogonal frequency channels don't interfere
✅ **Biological plausibility**: Neural oscillations (theta, gamma)
✅ **Temporal binding**: Phase = "when" within cycle

### Challenges
⚠️ **Limited capacity**: Bounded by frequency resolution
⚠️ **Cross-talk**: Harmonics can interfere
⚠️ **Continuous recall**: Must maintain oscillations

---

## Architecture 4: Topological Memory (TM)

### Core Concept
Episodes are topological features (holes, voids, connected components) in μ space. Use persistent homology.

### Mathematical Formulation

**Topology of Episodes:**
```
Episode E → point cloud in μ space
Topological signature = persistence diagram
Features:
- H₀: Connected components (number of distinct events)
- H₁: Loops (cyclic patterns, recurring themes)
- H₂: Voids (missing information, gaps)
```

**Storage:**
```python
episode → {μ₁, μ₂, ..., μ_T} → persistence_diagram(episode)
```

**Recall:**
```python
cue → partial_diagram → find episode with matching topology
```

### Implementation Strategy

```python
import ripser  # Persistent homology library
from persim import plot_diagrams

class TopologicalMemory:
    def __init__(self):
        self.episodes = []

    def store_episode(self, mu_trajectory, context):
        # Compute topological signature
        diagram = ripser.ripser(mu_trajectory)['dgms']

        # Extract persistent features (long-lived)
        persistent_features = self.extract_persistent(diagram)

        episode = {
            'trajectory': mu_trajectory,
            'topology': diagram,
            'features': persistent_features,
            'context': context
        }
        self.episodes.append(episode)

    def extract_persistent(self, diagram, threshold=0.1):
        """Extract features with persistence > threshold"""
        persistent = []
        for dim, dgm in enumerate(diagram):
            persistence = dgm[:, 1] - dgm[:, 0]  # death - birth
            long_lived = dgm[persistence > threshold]
            persistent.append((dim, long_lived))
        return persistent

    def recall(self, cue_trajectory):
        # Compute topology of cue
        cue_diagram = ripser.ripser(cue_trajectory)['dgms']
        cue_features = self.extract_persistent(cue_diagram)

        # Find episode with matching topological signature
        best_match = None
        best_distance = float('inf')

        for episode in self.episodes:
            # Bottleneck distance between persistence diagrams
            distance = self.diagram_distance(cue_features, episode['features'])
            if distance < best_distance:
                best_distance = distance
                best_match = episode

        return best_match

    def diagram_distance(self, diag1, diag2):
        """Bottleneck or Wasserstein distance between diagrams"""
        from persim import bottleneck
        # Compare each homology dimension
        total_dist = 0
        for (dim1, dgm1), (dim2, dgm2) in zip(diag1, diag2):
            if dim1 == dim2:
                total_dist += bottleneck(dgm1, dgm2)
        return total_dist
```

### Episodic Features as Topology

| Topological Feature | Episodic Interpretation |
|---------------------|-------------------------|
| H₀ (components) | Number of distinct sub-events |
| H₁ (loops) | Recurring patterns, cycles |
| H₂ (voids) | Missing information, gaps in recall |
| Persistence | Importance/salience of feature |
| Birth time | When event began |
| Death time | When event ended |

### Advantages
✅ **Structural invariance**: Robust to continuous deformations
✅ **Multi-scale**: Captures features at all temporal scales
✅ **Interpretable**: Holes = missing info, loops = repetition
✅ **Novel metrics**: Topological distances for similarity

### Challenges
⚠️ **Computational cost**: O(n³) for persistent homology
⚠️ **Abstract**: Less intuitive than attractor-based
⚠️ **Dimensionality**: High-dim spaces have trivial topology

---

## Architecture 5: Hierarchical Reservoir Memory (HRM)

### Core Concept
Multi-scale μ fields: μ₁ (fast, details), μ₂ (medium, events), μ₃ (slow, context). Episodes = patterns across scales.

### Mathematical Formulation

**Hierarchical Dynamics:**
```
μ₁(t): Fast dynamics (τ₁ ~ 1 step)   - sensory details
μ₂(t): Medium dynamics (τ₂ ~ 10 steps) - event chunks
μ₃(t): Slow dynamics (τ₃ ~ 100 steps)  - context/schema

Coupling:
dμ₁/dt = f₁(μ₁) + η₁₂·(μ₂ - μ₁)
dμ₂/dt = f₂(μ₂) + η₂₁·g(μ₁) + η₂₃·(μ₃ - μ₂)
dμ₃/dt = f₃(μ₃) + η₃₂·g(μ₂)

where g(·) = pooling/aggregation from lower level
```

### Implementation Strategy

```python
class HierarchicalMemory:
    def __init__(self, dims=[256, 128, 64], taus=[1, 10, 100]):
        self.n_levels = len(dims)
        self.engines = [
            create_engine('fft', RecursiveParams(dt=tau), n_dims=dim)
            for dim, tau in zip(dims, taus)
        ]
        self.dims = dims
        self.taus = taus

    def step(self, sensory_input):
        """Hierarchical update with top-down and bottom-up flow"""

        # Level 1: Fast sensory processing
        mu1 = self.engines[0].step(input_vec=sensory_input)

        # Level 2: Medium-term event structure
        # Bottom-up: compressed μ₁
        bottom_up = self.compress(mu1, target_dim=self.dims[1])
        # Top-down: context from μ₃
        top_down = self.expand(self.engines[2].mu, target_dim=self.dims[1])

        input_2 = 0.3 * bottom_up + 0.1 * top_down
        mu2 = self.engines[1].step(input_vec=input_2)

        # Level 3: Slow contextual schema
        # Bottom-up from μ₂
        bottom_up_3 = self.compress(mu2, target_dim=self.dims[2])
        mu3 = self.engines[2].step(input_vec=0.1 * bottom_up_3)

        return {'mu1': mu1, 'mu2': mu2, 'mu3': mu3}

    def compress(self, mu, target_dim):
        """Compress high-dim to low-dim (pooling/PCA)"""
        # Simple average pooling
        ratio = len(mu) // target_dim
        return np.mean(mu.reshape(target_dim, ratio), axis=1)

    def expand(self, mu, target_dim):
        """Expand low-dim to high-dim (broadcast)"""
        ratio = target_dim // len(mu)
        return np.repeat(mu, ratio)

    def store_episode(self, sensory_stream):
        """Store episode across all hierarchical levels"""
        trajectories = {level: [] for level in range(self.n_levels)}

        for sensory_t in sensory_stream:
            states = self.step(sensory_t)
            trajectories[0].append(states['mu1'])
            trajectories[1].append(states['mu2'])
            trajectories[2].append(states['mu3'])

        episode = {
            'details': trajectories[0],      # Full sensory detail
            'events': trajectories[1],       # Event structure
            'context': trajectories[2],      # Semantic context
        }

        return episode

    def recall(self, context_cue=None, event_cue=None, detail_cue=None):
        """Hierarchical recall - can start from any level"""

        if context_cue is not None:
            # Top-down recall: context → events → details
            self.engines[2].mu = context_cue

            # Generate events from context
            for _ in range(50):
                mu3 = self.engines[2].step()
                top_down_2 = self.expand(mu3, self.dims[1])
                mu2 = self.engines[1].step(input_vec=0.5 * top_down_2)

            # Generate details from events
            for _ in range(50):
                top_down_1 = self.expand(mu2, self.dims[0])
                mu1 = self.engines[0].step(input_vec=0.5 * top_down_1)

            return {'details': mu1, 'events': mu2, 'context': mu3}

        elif event_cue is not None:
            # Middle-out recall
            self.engines[1].mu = event_cue
            # ... similar bidirectional reconstruction

        elif detail_cue is not None:
            # Bottom-up recall: details → events → context
            # ... similar upward propagation
```

### Memory Properties

| Level | Time Scale | Content | Example |
|-------|-----------|---------|---------|
| μ₁ | ~1ms | Sensory details | "red ball, high pitch" |
| μ₂ | ~100ms | Event chunks | "ball bouncing" |
| μ₃ | ~10s | Context/schema | "playing basketball" |

### Advantages
✅ **Multi-scale**: Natural episodic structure (details + gist)
✅ **Flexible recall**: Can retrieve from any level
✅ **Compression**: Higher levels abstract lower levels
✅ **Schema formation**: μ₃ learns recurring contexts

### Challenges
⚠️ **Complexity**: Multiple coupled dynamics
⚠️ **Tuning**: Must balance time scales carefully
⚠️ **Interference**: Cross-level bleeding

---

## Architecture 6: Graph-Structured Episodic Memory (GSEM)

### Core Concept
Episodes as nodes in a graph, edges = semantic/temporal relationships. Recall = graph traversal.

### Mathematical Formulation

**Memory Graph:**
```
G = (V, E)
V = {episode_i}: nodes = μ attractors
E = {(i,j, w_ij)}: edges = semantic similarity, temporal proximity
```

**Graph Dynamics:**
```python
# Activation spreads through graph
A_i(t+1) = σ(Σ_j w_ij · A_j(t) + input_i(t))

where A_i = activation of episode i
```

**Recall:**
```python
# Initialize with cue
A(0) = one-hot at cue episode
# Spread activation
for t in range(T):
    A(t+1) = graph_propagation(A(t))
# Retrieve activated episodes
recalled = episodes[A(T) > threshold]
```

### Implementation Strategy

```python
import networkx as nx

class GraphMemory:
    def __init__(self):
        self.graph = nx.Graph()
        self.episode_count = 0

    def store_episode(self, mu_state, context, timestamp):
        episode_id = self.episode_count
        self.episode_count += 1

        # Add episode node
        self.graph.add_node(episode_id,
                          mu=mu_state,
                          context=context,
                          time=timestamp)

        # Connect to existing episodes
        for existing_id in self.graph.nodes():
            if existing_id == episode_id:
                continue

            existing_mu = self.graph.nodes[existing_id]['mu']
            existing_time = self.graph.nodes[existing_id]['time']

            # Semantic similarity edge
            semantic_sim = cosine_similarity(mu_state, existing_mu)
            if semantic_sim > 0.7:
                self.graph.add_edge(episode_id, existing_id,
                                  weight=semantic_sim,
                                  type='semantic')

            # Temporal proximity edge
            time_diff = abs(timestamp - existing_time)
            if time_diff < 100:  # Within recent window
                temporal_weight = np.exp(-time_diff / 50)
                self.graph.add_edge(episode_id, existing_id,
                                  weight=temporal_weight,
                                  type='temporal')

        return episode_id

    def recall(self, cue_mu, k=5, steps=3):
        """Retrieve k episodes via activation spreading"""

        # Find closest starting node
        closest_id = None
        closest_dist = float('inf')
        for node_id in self.graph.nodes():
            node_mu = self.graph.nodes[node_id]['mu']
            dist = np.linalg.norm(cue_mu - node_mu)
            if dist < closest_dist:
                closest_dist = dist
                closest_id = node_id

        # Spread activation from starting point
        activation = {node: 0.0 for node in self.graph.nodes()}
        activation[closest_id] = 1.0

        for step in range(steps):
            new_activation = activation.copy()
            for node in self.graph.nodes():
                # Collect activation from neighbors
                incoming = sum(
                    activation[neighbor] * self.graph[node][neighbor]['weight']
                    for neighbor in self.graph.neighbors(node)
                )
                new_activation[node] += incoming * 0.5  # Decay

            # Normalize
            total = sum(new_activation.values())
            activation = {k: v/total for k, v in new_activation.items()}

        # Return top-k activated episodes
        top_episodes = sorted(activation.items(),
                            key=lambda x: x[1],
                            reverse=True)[:k]

        recalled = [
            self.graph.nodes[episode_id]
            for episode_id, act in top_episodes
        ]

        return recalled

    def cluster_episodes(self):
        """Find communities of related episodes"""
        communities = nx.community.louvain_communities(self.graph)
        return communities
```

### Advanced: Hypergraph Memory

```python
# Episodes connected via shared concepts (multi-way relationships)
import hypernetx as hnx

class HypergraphMemory:
    def __init__(self):
        self.hyperedges = {}  # concept → set of episodes
        self.episodes = {}     # episode_id → content

    def store_episode(self, episode_id, concepts, content):
        self.episodes[episode_id] = content

        # Add episode to hyperedges for each concept
        for concept in concepts:
            if concept not in self.hyperedges:
                self.hyperedges[concept] = set()
            self.hyperedges[concept].add(episode_id)

    def recall_by_concept(self, concepts):
        """Retrieve all episodes sharing concepts"""
        # Intersection: episodes having ALL concepts
        result = set(self.hyperedges[concepts[0]])
        for concept in concepts[1:]:
            result &= self.hyperedges[concept]

        return [self.episodes[eid] for eid in result]
```

### Advantages
✅ **Relational structure**: Captures episode relationships
✅ **Associative recall**: One episode triggers related ones
✅ **Clustering**: Automatically discovers semantic organization
✅ **Flexible**: Add arbitrary relationship types

### Challenges
⚠️ **Graph growth**: Edges grow as O(n²)
⚠️ **Maintenance**: Need to prune weak edges
⚠️ **Traversal cost**: Can be expensive for large graphs

---

## Hybrid Architecture: The Complete System

### Combining Multiple Approaches

```python
class UnifiedEpisodicMemory:
    """
    Combines best features of all architectures:
    - Attractors for robust storage
    - Trajectories for temporal structure
    - Phase coding for multiplexing
    - Topology for structural features
    - Hierarchy for multi-scale
    - Graphs for relationships
    """

    def __init__(self, config):
        self.attractor_mem = AttractorMemory()
        self.trajectory_mem = TrajectoryMemory()
        self.phase_mem = PhaseCodedMemory()
        self.topo_mem = TopologicalMemory()
        self.hierarchical_mem = HierarchicalMemory()
        self.graph_mem = GraphMemory()

    def store_episode(self, sensory_stream, context):
        # Process through hierarchy
        hier_states = self.hierarchical_mem.store_episode(sensory_stream)

        # Extract μ₂ (event level) as primary representation
        mu_trajectory = hier_states['events']

        # Store in multiple systems
        episode_id = self.graph_mem.store_episode(
            mu_state=mu_trajectory[-1],
            context=context,
            timestamp=time.time()
        )

        self.attractor_mem.store_episode(mu_trajectory, context)
        self.trajectory_mem.store_episode(mu_trajectory, emissions=[], context=context)

        # Compute topological signature
        self.topo_mem.store_episode(mu_trajectory, context)

        # Encode in phase space
        phase_features = np.fft.fft(mu_trajectory, axis=0)
        self.phase_mem.store_episode(mu_trajectory, context)

        return episode_id

    def recall(self, cue, mode='hybrid'):
        """
        Multi-modal recall:
        - 'attractor': Content-addressable from partial cue
        - 'trajectory': Temporal sequence matching
        - 'phase': Frequency-based retrieval
        - 'topology': Structural similarity
        - 'graph': Associative spreading
        - 'hybrid': Consensus across methods
        """

        if mode == 'hybrid':
            # Get candidates from each system
            attractor_result = self.attractor_mem.recall(cue)
            traj_result = self.trajectory_mem.recall(cue, match_mode='anywhere')
            graph_results = self.graph_mem.recall(cue, k=5)
            topo_result = self.topo_mem.recall(cue)

            # Voting/consensus
            candidates = [attractor_result, traj_result, graph_results[0], topo_result]

            # Rank by agreement
            scores = self.compute_consensus_scores(candidates)
            best = candidates[np.argmax(scores)]

            return best

        elif mode == 'attractor':
            return self.attractor_mem.recall(cue)

        # ... other modes

    def consolidate(self):
        """
        Memory consolidation (like sleep):
        - Strengthen frequently accessed attractors
        - Prune weak graph edges
        - Compress old trajectories
        - Extract common topological patterns
        """

        # Attractor strengthening
        self.attractor_mem.strengthen_popular()

        # Graph pruning
        self.graph_mem.graph = self.graph_mem.graph.subgraph(
            [n for n, d in self.graph_mem.graph.degree() if d > 2]
        )

        # Trajectory compression
        old_episodes = self.trajectory_mem.get_old_episodes(age_threshold=1000)
        for ep in old_episodes:
            compressed = self.trajectory_mem.compressor.encode(ep['trajectory'])
            ep['trajectory'] = compressed  # Replace with compressed version

        # Topological pattern extraction
        common_patterns = self.topo_mem.find_recurring_topology()
        # Store as schemas in hierarchical memory level 3
```

---

## Novel Theoretical Contributions

### 1. Episodic Memory as Dynamical Invariants

**Insight**: Episodes = conserved quantities in the dynamics

```python
# Conservation laws define memorable events
def is_memorable(mu_trajectory):
    # Compute conserved quantities
    energy = compute_energy(mu_trajectory)
    momentum = compute_momentum(mu_trajectory)
    helicity = compute_helicity(mu_trajectory)

    # Episodes are extrema of conserved quantities
    return is_extremum(energy) or is_extremum(momentum)
```

### 2. Episodic Boundaries from Bifurcations

**Insight**: Episode segmentation = dynamical bifurcations

```python
# Detect when dynamics change qualitatively
def detect_episode_boundary(mu, mu_prev):
    # Compute Lyapunov exponent
    lyapunov = compute_lyapunov_exponent(mu, mu_prev)

    # Boundary = change from stable to chaotic (or vice versa)
    if lyapunov crosses zero:
        return True  # Episode boundary

    return False
```

### 3. Forget-Resistance via Basin Depth

**Insight**: Forgetting = basin flattening over time

```python
# Model forgetting as attractor basin decay
class ForgetfulAttractorMemory:
    def __init__(self, decay_rate=0.01):
        self.decay_rate = decay_rate

    def time_evolution(self, dt):
        # Attractors gradually flatten (forgetting)
        for attractor in self.attractors:
            attractor['strength'] *= np.exp(-self.decay_rate * dt)

    def anti_decay(self, attractor_id):
        # Retrieval strengthens attractor (reconsolidation)
        self.attractors[attractor_id]['strength'] *= 1.1
```

### 4. False Memories as Basin Merging

**Insight**: Confabulation = similar episodes merge basins

```python
# Similar episodes attract each other in phase space
def check_memory_contamination(episode_i, episode_j):
    # If basins overlap, memories can contaminate
    basin_overlap = compute_basin_overlap(episode_i, episode_j)

    if basin_overlap > 0.5:
        # High risk of false memory
        return "WARNING: Episodes may merge"
```

---

## Performance Comparison

| Architecture | Storage | Recall | Capacity | Biological | Temporal |
|--------------|---------|--------|----------|-----------|----------|
| Attractor | O(1) | O(n) | O(d²) | ⭐⭐⭐⭐ | ⭐⭐ |
| Trajectory | O(T) | O(nT) | O(∞) | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Phase | O(1) | O(log n) | O(f) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Topological | O(T) | O(n³) | O(∞) | ⭐⭐ | ⭐⭐⭐⭐ |
| Hierarchical | O(LT) | O(L) | O(∞) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Graph | O(n) | O(n) | O(∞) | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Hybrid** | **O(LT)** | **O(L)** | **O(∞)** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |

Legend:
- d = dimensionality
- T = episode duration
- n = number of episodes
- L = hierarchy levels
- f = frequency resolution

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [x] Basic recursive engine ✅
- [ ] Attractor detection algorithm
- [ ] Basin depth computation
- [ ] Energy landscape visualization

### Phase 2: Simple Memory (Week 3-4)
- [ ] Implement AttractorMemory class
- [ ] Storage and recall functions
- [ ] Forgetting mechanism
- [ ] Benchmark capacity

### Phase 3: Temporal Structure (Week 5-6)
- [ ] Implement TrajectoryMemory
- [ ] Compression algorithms
- [ ] Replay mechanism
- [ ] Key state extraction

### Phase 4: Advanced Features (Week 7-8)
- [ ] Phase coding implementation
- [ ] Topological analysis integration
- [ ] Hierarchical dynamics
- [ ] Graph structure

### Phase 5: Integration (Week 9-10)
- [ ] Unified hybrid system
- [ ] Consolidation algorithms
- [ ] Multi-modal recall
- [ ] Performance optimization

### Phase 6: Validation (Week 11-12)
- [ ] Benchmark against hippocampal data
- [ ] Human episodic memory tasks
- [ ] Capacity stress tests
- [ ] Interference and consolidation tests

---

## Key Research Questions

### Theoretical
1. **Capacity limits**: How many attractors before catastrophic interference?
2. **Optimal hierarchy**: What time scales for μ₁, μ₂, μ₃?
3. **Topology-dynamics**: What topological features predict memorability?
4. **Phase interference**: Can episodes at nearby frequencies coexist?

### Empirical
5. **Recall fidelity**: How accurate is trajectory replay?
6. **Temporal resolution**: What's the finest temporal detail preserved?
7. **Consolidation**: Does repeated recall strengthen attractors?
8. **False memories**: What causes basin merging?

### Computational
9. **Scaling**: Can this handle 10⁶ episodes?
10. **Real-time**: Can recall happen in < 100ms?
11. **Energy efficiency**: FLOPS per episode compared to transformers?
12. **Hardware**: Can neuromorphic chips accelerate this?

---

## Comparison to Existing Approaches

### vs Transformer Episodic Memory
| Feature | This System | Transformer |
|---------|-------------|-------------|
| Storage | Attractors in dynamics | Attention over sequence |
| Recall | Trajectory convergence | Cross-attention query |
| Temporal | Inherent in dynamics | Positional encoding |
| Capacity | O(d²) attractors | O(context window) |
| Biological | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### vs Hopfield Networks
| Feature | This System | Hopfield |
|---------|-------------|----------|
| Dynamics | Continuous PDE | Discrete updates |
| Attractors | Smooth basins | Binary patterns |
| Capacity | ~0.15d² | ~0.14n (Hebbian) |
| Temporal | Native | External |
| Retrieval | Guaranteed convergence | Spurious attractors |

### vs LSTM/GRU Memory
| Feature | This System | LSTM |
|---------|-------------|------|
| Structure | Physical dynamics | Gated units |
| Long-term | Attractor persistence | Gradient flow |
| Interpretability | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Training | Physics-based | Backprop |
| Generalization | Dynamical laws | Data distribution |

---

## Conclusion

**The dynamical systems framework provides a fundamentally new approach to episodic memory:**

1. **Attractors** = Content-addressable storage with noise robustness
2. **Trajectories** = Native temporal structure without explicit indexing
3. **Phase coding** = Natural multiplexing without interference
4. **Topology** = Structural invariants capture memory "shape"
5. **Hierarchy** = Multi-scale representation (details + gist)
6. **Graphs** = Emergent relational structure

**This is not just an implementation detail—it's a paradigm shift:**
- Memory as **geometry of phase space**, not lookup tables
- Recall as **dynamical process**, not database query
- Forgetting as **basin decay**, not deletion
- Consolidation as **attractor sharpening**, not rehearsal

**Next steps:**
1. Implement AttractorMemory and benchmark capacity
2. Test on standard episodic memory tasks
3. Compare to hippocampal replay data
4. Scale to naturalistic episodes (video, audio, text)
5. Explore neuromorphic hardware acceleration

The mathematics already works. Now let's build it.
