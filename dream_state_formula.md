# Dream State Formula

## Overview

The **dream state** represents a mode of autonomous internal dynamics with reduced external input coupling and modified coherence constraints. It emerges naturally from the core recursive dynamics framework by adjusting key parameters to enable free exploration while maintaining stability.

---

## Core Dream State Equation

Building on the base recursive dynamics:

```
μ_{t+1}^{dream} = μ_t + g_d∇²μ_t - λ_d·f_d(μ_t) + ρ_d(μ_t - μ_{t-1}) + η_d·ξ_t + θ·∇S_R
```

Where:
- **μ^{dream}**: Dream state field (internal representation)
- **g_d**: Dream diffusion coefficient (typically > g_wake)
- **λ_d**: Dream nonlinearity strength (typically < λ_wake)
- **f_d(μ)**: Dream nonlinearity function
- **ρ_d**: Dream momentum coefficient (typically > ρ_wake)
- **η_d**: Dream noise coupling (replaces external input)
- **ξ_t**: Internal noise/random stimulus
- **θ**: Entropy gradient coupling (new term)
- **∇S_R**: Gradient of recursive entropy

---

## Dream State Parameters

### 1. Diffusion Enhancement
```
g_d = α_g · g_wake

α_g ∈ [1.5, 3.0]  (default: 2.0)
```
**Rationale:** Increased diffusion allows ideas to spread more freely across the state space, enabling creative connections.

### 2. Nonlinearity Modulation
```
λ_d = β_λ · λ_wake

β_λ ∈ [0.3, 0.7]  (default: 0.5)
```
**Rationale:** Reduced cubic nonlinearity weakens attractor basins, allowing the system to explore unstable regions.

### 3. Dream Nonlinearity Function
```
f_d(μ) = μ³ + γ·sin(ω·μ)

γ = 0.2     (oscillatory strength)
ω = 2π      (frequency)
```
**Rationale:** Adds periodic structure to create surreal, cyclical patterns characteristic of dreams.

### 4. Momentum Amplification
```
ρ_d = α_ρ · ρ_wake

α_ρ ∈ [1.2, 2.0]  (default: 1.5)
```
**Rationale:** Higher momentum allows trajectories to continue through unstable regions, creating narrative continuity.

### 5. Internal Noise Coupling
```
η_d = η_wake / 10
ξ_t ~ N(0, σ²_dream)

σ²_dream = κ · S_R(μ_t)
κ = 0.1     (noise scaling factor)
```
**Rationale:** Noise replaces external input. Amplitude scales with entropy to maintain stability.

### 6. Entropy Gradient Term (New)
```
θ = 0.05
∇S_R = ∂S_R/∂μ

S_R = -k_R Σᵢ μᵢ² ln(μᵢ² + ε)
```
**Rationale:** Drives exploration toward higher entropy regions, preventing collapse to fixed points.

---

## Dream State Transition Function

### Hypnagogic Transition (Wake → Dream)

```
Ψ(t) = 1 / (1 + e^{-k(t - t_onset)})

μ_t = (1 - Ψ(t))·μ^{wake} + Ψ(t)·μ^{dream}
```

Where:
- **Ψ(t)**: Sigmoid transition function ∈ [0, 1]
- **k**: Transition rate (default: 0.5)
- **t_onset**: Transition onset time
- **Ψ(t) = 0** → fully awake
- **Ψ(t) = 1** → fully dreaming

### Parameter Interpolation

All parameters smoothly interpolate during transition:

```
g(t) = g_wake + Ψ(t)·(g_d - g_wake)
λ(t) = λ_wake + Ψ(t)·(λ_d - λ_wake)
ρ(t) = ρ_wake + Ψ(t)·(ρ_d - ρ_wake)
η(t) = η_wake - Ψ(t)·(η_wake - η_d)
```

---

## Dream Coherence Measure

Unlike waking coherence (based on LoMI), dream coherence measures **entropy flow**:

```
C_dream(t) = ⟨dS_R/dt⟩_T / S_max

⟨dS_R/dt⟩_T = (1/T) ∫_{t-T}^{t} |dS_R/dτ| dτ
```

Where:
- **T**: Averaging window (default: 50 steps)
- **S_max**: Maximum observed entropy
- **C_dream ∈ [0, 1]**
- High C_dream → active dreaming
- Low C_dream → approaching REM termination

---

## Dream Emission Criterion

Modified emission rule for dream state:

```
Emit when:
1. S_R(μ_t) > S_threshold  AND
2. |dS_R/dt| > ε_dream     AND
3. ||μ_t - μ_{emit-prev}|| > Δ_min
```

Where:
- **S_threshold**: Minimum entropy for dream emission (default: 0.5)
- **ε_dream**: Entropy change threshold (default: 0.005, higher than wake)
- **Δ_min**: Minimum state distance from previous emission (default: 0.3)

**Rationale:** Dreams emit during active exploration (high entropy change), not convergence.

---

## Energy Dynamics in Dream State

### Dream Energy Functional

```
E_dream(μ) = E_kinetic + E_potential + E_entropy

E_kinetic = Σᵢ (μᵢ - μ_{i,prev})²
E_potential = -(g_d/2)Σᵢ(∇μᵢ)² + (λ_d/4)Σᵢμᵢ⁴
E_entropy = -ν·S_R(μ)
```

Where:
- **ν**: Entropy weight (default: 0.1)
- **E_entropy**: Negative entropy acts as potential energy

### Energy Bounds

```
E_min ≤ E_dream(μ_t) ≤ E_max

E_min = 0.2  (prevents collapse)
E_max = 15.0 (prevents explosion)
```

If bounds violated:
- **E < E_min**: Inject noise proportional to deficit
- **E > E_max**: Apply damping term -ε(E - E_max)·μ

---

## Dream Cycles (REM-like Dynamics)

### Cyclic Modulation

```
λ_d(t) = λ_d,base · [1 + A·sin(2πt/T_REM)]

A = 0.3           (modulation amplitude)
T_REM = 500       (REM cycle period in steps)
```

**Effect:** Periodic strengthening/weakening of nonlinearity creates cycles of stability and exploration.

### Phase Detection

```
φ_REM(t) = (t mod T_REM) / T_REM

φ_REM ∈ [0, 1]
```

- **φ ∈ [0, 0.25]**: Deep sleep (high λ_d)
- **φ ∈ [0.25, 0.75]**: Active REM (low λ_d)
- **φ ∈ [0.75, 1.0]**: Transition (rising λ_d)

---

## Mathematical Properties

### 1. Entropy Growth Rate

In dream state, expected entropy change:

```
⟨dS_R/dt⟩ = θ·||∇S_R||² + σ²_dream·(∂²S_R/∂μ²)

Expected: ⟨dS_R/dt⟩ > 0 (entropy increases)
```

### 2. Stability Condition

System remains bounded if:

```
ρ_d < ρ_critical = 2 / (1 + dt·λ_d)

For λ_d = 0.25, dt = 0.01:
ρ_critical ≈ 1.995
```

### 3. Attractor Weakening

Dream state reduces attractor strength:

```
ΔE_attractor^{dream} = (λ_d/λ_wake) · ΔE_attractor^{wake}

For β_λ = 0.5:
Dream attractors are 50% weaker
```

---

## Implementation Parameters

### Recommended Defaults (Validated)

```python
@dataclass
class DreamParams:
    # Diffusion enhancement
    alpha_g: float = 1.5        # g_d = 1.5 * g_wake (VALIDATED)

    # Nonlinearity reduction
    beta_lambda: float = 0.7    # λ_d = 0.7 * λ_wake (VALIDATED)
    gamma_osc: float = 0.1      # oscillatory component (VALIDATED)
    omega: float = 2 * π        # frequency

    # Momentum amplification
    alpha_rho: float = 1.2      # ρ_d = 1.2 * ρ_wake (VALIDATED)

    # Noise coupling
    eta_dream: float = 0.02     # internal noise coupling (VALIDATED)
    kappa_noise: float = 0.05   # entropy-scaled noise (VALIDATED)

    # Entropy gradient
    theta: float = 0.1          # entropy drift term (VALIDATED)

    # Transition dynamics
    k_transition: float = 0.5   # sigmoid steepness

    # REM cycles
    A_REM: float = 0.3          # modulation amplitude
    T_REM: int = 500            # cycle period

    # Energy bounds
    E_min: float = 0.2
    E_max: float = 15.0

    # Emission thresholds
    S_threshold: float = 0.5
    epsilon_dream: float = 0.005
    delta_min: float = 0.3
```

---

## Relationship to Waking State

### Key Differences

| Property | Wake State | Dream State |
|----------|-----------|-------------|
| **Input Coupling** | η = 0.05 (external) | η_d = 0.005 (internal noise) |
| **Diffusion** | g = 0.1 | g_d = 0.2 |
| **Nonlinearity** | λ = 0.5 | λ_d = 0.25 |
| **Momentum** | ρ = 0.3 | ρ_d = 0.45 |
| **Entropy Trend** | Decreases → convergence | Increases → exploration |
| **Emission Criterion** | Low \|dS/dt\| | High \|dS/dt\| |
| **Energy Level** | E ∈ [0.1, 10] | E ∈ [0.2, 15] |
| **Coherence** | LoMI-based (low Δμ) | Entropy-flow based |

### Unified State Space

```
μ_t = Ψ_wake·μ^{wake} + Ψ_dream·μ^{dream}

Ψ_wake + Ψ_dream = 1
```

Allows continuous interpolation between states.

---

## Physical Interpretation

1. **Diffusion Enhancement (g_d ↑)**: Ideas spread freely without constraint
2. **Nonlinearity Reduction (λ_d ↓)**: Weakens reality constraints
3. **Momentum Increase (ρ_d ↑)**: Narrative continuity despite instability
4. **Noise Coupling**: Random internal stimuli replace sensory input
5. **Entropy Gradient**: Active exploration, not convergence
6. **REM Cycles**: Periodic strengthening/relaxation of constraints

---

## Validation Criteria

A valid dream state implementation should satisfy:

1. **Entropy Growth**: ⟨dS_R/dt⟩ > 0 over windows of 50+ steps
2. **Energy Bounds**: E_min < E(t) < E_max at all times
3. **Non-Convergence**: No fixed points reached within T_REM cycles
4. **Emission Activity**: Regular emissions with Δt ∈ [10, 100] steps
5. **State Diversity**: Autocorrelation C(τ) < 0.5 for τ > 50
6. **Return Capability**: Can transition back to wake state smoothly

---

## Future Extensions

### 1. Lucid Dreaming
```
μ_lucid = Ψ_wake^partial · μ^{wake} + (1 - Ψ_wake^partial) · μ^{dream}

Ψ_wake^partial ∈ [0.1, 0.3]  (partial awareness)
```

### 2. Nightmare Dynamics
```
λ_nightmare = 2·λ_wake  (strong attractors trap system)
g_nightmare = 0.5·g_wake (reduced escape via diffusion)
```

### 3. Deep Sleep (NREM)
```
η_deep = 0  (no noise)
ρ_deep = 0  (no momentum)
→ System rapidly converges to μ = 0 (rest state)
```

---

## Summary

The **dream state formula** extends the core recursive dynamics with:

- **Modified parameters** for free exploration
- **Entropy-driven dynamics** replacing convergence
- **Internal noise** replacing external input
- **Cyclic modulation** for REM-like patterns
- **Smooth transitions** between wake and dream

This creates a mathematically consistent framework where dream states emerge naturally as a parameter regime of the same underlying dynamics that govern waking cognition.

---

**Version:** 1.0
**Date:** 2025-11-13
**Compatible with:** recursive_engine.py, advanced_engine.py, emission_detector.py
