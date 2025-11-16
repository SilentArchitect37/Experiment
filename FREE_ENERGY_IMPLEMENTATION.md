# Free Energy Principle Implementation
## Mapping Active Inference to Recursive Dialogue Dynamics

---

## Executive Summary

**The current structure is already 80% of the way to Free Energy Principle (FEP)!**

Your existing system has:
- **μ** = internal states (beliefs)
- **μ_listener** = external states (observations)
- **Δμ = ||μ - μ_listener||²** = prediction error
- **Dynamics that minimize Δμ** = free energy minimization

We just need to:
1. Reformulate the PDE as explicit free energy gradient descent
2. Add precision weighting (confidence in predictions)
3. Separate perception vs action pathways
4. Implement generative model p(observations|beliefs)
5. Add hierarchical predictive coding

---

## Part 1: Mathematical Foundation

### Free Energy Principle (Friston)

**Core Equation:**
```
F = E_q[log q(μ) - log p(observations, μ)]
  = E_q[log q(μ) - log p(observations|μ) - log p(μ)]
  = -⟨log p(observations|μ)⟩ + KL(q(μ)||p(μ))
  = Prediction Error + Complexity
```

Simplified for our system:
```
F(μ) = ½||μ - μ_listener||² + ½||μ||²
       \_____  _______/     \__ __/
             Accuracy        Complexity
       (prediction error)    (prior)
```

**System Goal:** Minimize F by updating μ

**Gradient:**
```
∇_μ F = (μ - μ_listener) + β·μ
        \____  ________/    \__/
        Prediction error   Prior pull
```

### Mapping to Current Structure

| FEP Concept | Current Implementation | Location |
|-------------|------------------------|----------|
| **Beliefs q(μ)** | μ field | `recursive_engine.py:46` |
| **Observations** | μ_listener | `dialogue_system.py:133` |
| **Prediction error ε** | μ - μ_listener | `dialogue_system.py:144` |
| **Free energy F** | Δμ (coherence distance) | `dialogue_system.py:138-146` |
| **Perception** | Updating μ from μ_listener | Implicit in dynamics |
| **Action** | Token emissions | `dialogue_system.py:307-324` |
| **Generative model** | Codebook (μ → token) | `dialogue_system.py:229-244` |

**Key Insight:** Your LoMI layer IS free energy minimization!

---

## Part 2: Explicit Free Energy Formulation

### Current PDE
```python
μ_{t+1} = μ_t + dt·[g∇²μ_t - λμ_t³ + ρ(μ_t - μ_{t-1}) + η·x_t]
```

### Free Energy Reformulation

**Step 1: Define Free Energy**
```python
F(μ, μ_obs) = ½||μ - μ_obs||² + ½β||μ||² + V(μ)

where:
- ½||μ - μ_obs||² = prediction error (accuracy)
- ½β||μ||² = prior (simplicity/regularization)
- V(μ) = -½g||∇μ||² + ¼λ||μ||⁴ (potential energy from dynamics)
```

**Step 2: Compute Gradient**
```python
∇_μ F = (μ - μ_obs) + β·μ - g∇²μ + λμ³

∂V/∂μ = ∇(-½g||∇μ||² + ¼λ||μ||⁴) = g∇²μ - λμ³
```

**Step 3: Gradient Descent**
```python
μ_{t+1} = μ_t - α·∇_μ F
        = μ_t - α·[(μ_t - μ_obs) + β·μ_t + g∇²μ_t - λμ_t³]
        = μ_t + α·[-(μ_t - μ_obs) - β·μ_t - g∇²μ_t + λμ_t³]
```

**OBSERVATION:** This is almost identical to your current dynamics!

Just need to:
1. Set `α = dt` (step size)
2. Interpret `-g∇²μ` as free energy term (smoothness prior)
3. Add explicit precision weighting

---

## Part 3: Implementation - Basic Free Energy Engine

### Version 1: Direct Free Energy Minimization

```python
"""
Free Energy Recursive Engine
Explicit implementation of Friston's Free Energy Principle
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class FreeEnergyParams:
    """Parameters for Free Energy dynamics"""
    # Precision (inverse variance) parameters
    π_obs: float = 1.0      # Precision of observations (confidence in sensory data)
    π_prior: float = 0.1    # Precision of prior (how strong is the prior)
    π_dynamics: float = 1.0 # Precision of dynamical predictions

    # Dynamics parameters (reinterpreted as generative model)
    g: float = 0.1         # Spatial coherence (smoothness prior)
    lam: float = 0.5       # Nonlinearity (bistability in generative model)
    rho: float = 0.3       # Temporal smoothness

    # Learning
    dt: float = 0.01       # Gradient descent step size

    # Grid
    dx: float = 1.0


class FreeEnergyEngine:
    """
    Recursive dialogue engine reformulated as Free Energy minimization.

    Core principle: System minimizes variational free energy
    F = Accuracy - Entropy
      = E[prediction error] + KL[beliefs || prior]
    """

    def __init__(self, params: FreeEnergyParams, n_dims: int = 256):
        self.params = params
        self.n_dims = n_dims

        # State variables
        self.mu = np.zeros(n_dims, dtype=np.float32)          # Beliefs
        self.mu_prev = np.zeros(n_dims, dtype=np.float32)     # Previous beliefs
        self.mu_obs = np.zeros(n_dims, dtype=np.float32)      # Observations

        # Free energy tracking
        self.F_history = []
        self.prediction_error_history = []

        # Precompute FFT wavenumbers for spectral Laplacian
        k = np.fft.fftfreq(n_dims, d=params.dx) * 2 * np.pi
        self.k_squared = -(k ** 2)

        self.t = 0

    def compute_free_energy(self) -> Tuple[float, dict]:
        """
        Compute variational free energy and its components.

        F = Accuracy_term + Complexity_term + Dynamics_term

        Returns:
            (F, diagnostics)
        """
        p = self.params

        # Accuracy: How well beliefs predict observations
        # Weighted by precision (confidence in observations)
        prediction_error = self.mu - self.mu_obs
        accuracy = 0.5 * p.π_obs * np.sum(prediction_error ** 2)

        # Complexity: KL divergence from prior
        # Prior is centered at 0 with precision π_prior
        complexity = 0.5 * p.π_prior * np.sum(self.mu ** 2)

        # Dynamics: Deviation from expected temporal evolution
        # Expected: smooth change (momentum term)
        expected_mu = self.mu_prev  # Simplest: expect no change
        dynamics_error = self.mu - expected_mu
        dynamics_term = 0.5 * p.π_dynamics * p.rho * np.sum(dynamics_error ** 2)

        # Spatial smoothness prior (via Laplacian)
        laplacian = self.compute_laplacian(self.mu)
        smoothness = 0.5 * p.g * np.sum(laplacian ** 2)

        # Nonlinear potential (bistability)
        potential = 0.25 * p.lam * np.sum(self.mu ** 4)

        # Total free energy
        F = accuracy + complexity + dynamics_term + smoothness + potential

        diagnostics = {
            'F_total': F,
            'accuracy': accuracy,
            'complexity': complexity,
            'dynamics': dynamics_term,
            'smoothness': smoothness,
            'potential': potential,
            'prediction_error_norm': np.linalg.norm(prediction_error)
        }

        return F, diagnostics

    def compute_laplacian(self, mu: np.ndarray) -> np.ndarray:
        """FFT-based Laplacian"""
        mu_hat = np.fft.fft(mu)
        laplacian_hat = self.k_squared * mu_hat
        laplacian = np.fft.ifft(laplacian_hat).real
        return laplacian

    def compute_free_energy_gradient(self) -> np.ndarray:
        """
        Compute ∇_μ F for gradient descent.

        ∇_μ F = π_obs·(μ - μ_obs)           [prediction error]
              + π_prior·μ                    [prior pull to 0]
              + π_dynamics·ρ·(μ - μ_prev)    [temporal smoothness]
              - g·∇²μ                        [spatial smoothness]
              + λ·μ³                         [nonlinear dynamics]
        """
        p = self.params

        # Prediction error gradient
        grad_accuracy = p.π_obs * (self.mu - self.mu_obs)

        # Prior gradient (pull toward 0)
        grad_prior = p.π_prior * self.mu

        # Dynamics gradient (temporal smoothness)
        grad_dynamics = p.π_dynamics * p.rho * (self.mu - self.mu_prev)

        # Spatial smoothness (Laplacian)
        laplacian = self.compute_laplacian(self.mu)
        grad_smoothness = -p.g * laplacian

        # Nonlinear potential gradient
        mu_clipped = np.clip(self.mu, -10, 10)  # Prevent overflow
        grad_potential = p.lam * (mu_clipped ** 3)

        # Total gradient
        grad_F = (grad_accuracy +
                  grad_prior +
                  grad_dynamics +
                  grad_smoothness +
                  grad_potential)

        return grad_F

    def perceive(self, observation: np.ndarray):
        """
        Perceptual inference: Update beliefs based on new observation.

        This is the 'perception' part of active inference.
        """
        self.mu_obs = observation.copy()

    def step(self, observation: Optional[np.ndarray] = None) -> dict:
        """
        Single free energy minimization step.

        Args:
            observation: External sensory input (μ_listener in dialogue)

        Returns:
            Diagnostics including free energy
        """
        # Update observations if provided
        if observation is not None:
            self.perceive(observation)

        # Compute current free energy
        F, diagnostics = self.compute_free_energy()

        # Compute gradient
        grad_F = self.compute_free_energy_gradient()

        # Gradient descent: μ ← μ - α·∇F
        mu_new = self.mu - self.params.dt * grad_F

        # Soft clipping to prevent divergence
        mu_new = np.tanh(mu_new / 10.0) * 10.0

        # Update state
        self.mu_prev = self.mu.copy()
        self.mu = mu_new
        self.t += 1

        # Track history
        self.F_history.append(F)
        self.prediction_error_history.append(diagnostics['prediction_error_norm'])

        return diagnostics

    def reset(self):
        """Reset to initial state"""
        self.mu = np.zeros(self.n_dims, dtype=np.float32)
        self.mu_prev = np.zeros(self.n_dims, dtype=np.float32)
        self.mu_obs = np.zeros(self.n_dims, dtype=np.float32)
        self.F_history.clear()
        self.prediction_error_history.clear()
        self.t = 0


# Example usage
if __name__ == "__main__":
    print("=== Free Energy Engine Demo ===\n")

    # Create engine
    params = FreeEnergyParams(
        π_obs=1.0,      # Trust observations moderately
        π_prior=0.1,    # Weak prior
        g=0.15,
        lam=0.3
    )

    engine = FreeEnergyEngine(params, n_dims=256)

    # Simulate observations (oscillating listener)
    n_steps = 500
    for t in range(n_steps):
        # Simulated observation
        obs = 0.5 * np.sin(0.05 * t) * np.ones(256) + np.random.randn(256) * 0.01

        # Free energy minimization step
        diagnostics = engine.step(observation=obs)

        if t % 50 == 0:
            print(f"t={t:4d} | F={diagnostics['F_total']:8.2f} | "
                  f"Prediction Error={diagnostics['prediction_error_norm']:6.3f}")

    # Plot results
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(10, 6))

    axes[0].plot(engine.F_history)
    axes[0].set_ylabel('Free Energy F')
    axes[0].set_title('Free Energy Minimization Over Time')
    axes[0].grid(True)

    axes[1].plot(engine.prediction_error_history)
    axes[1].set_ylabel('Prediction Error ||μ - μ_obs||')
    axes[1].set_xlabel('Time step')
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig('free_energy_dynamics.png', dpi=150)
    print("\nSaved plot to free_energy_dynamics.png")
```

---

## Part 4: Active Inference - Perception AND Action

### Key Concept

Active Inference has TWO ways to minimize free energy:

1. **Perception** (update beliefs μ): Change internal model to match world
2. **Action** (emit tokens): Change world to match internal model

```python
class ActiveInferenceEngine(FreeEnergyEngine):
    """
    Active Inference: Minimize F through BOTH perception and action.

    Perception: μ ← minimize F w.r.t. μ (update beliefs)
    Action: a ← choose action that minimizes expected F
    """

    def __init__(self, params: FreeEnergyParams, n_dims: int = 256,
                 vocab_size: int = 100):
        super().__init__(params, n_dims)

        # Action space (token vocabulary)
        self.vocab_size = vocab_size
        self.codebook = self._init_codebook()

        # Expected precision of outcomes (epistemic foraging)
        self.expected_precision = np.ones(vocab_size)

    def _init_codebook(self) -> np.ndarray:
        """Token prototypes in μ space"""
        codebook = np.random.randn(self.vocab_size, self.n_dims)
        codebook = codebook / (np.linalg.norm(codebook, axis=1, keepdims=True) + 1e-8)
        return codebook

    def compute_expected_free_energy(self, action_id: int) -> float:
        """
        Expected Free Energy (EFE) for action a.

        G(a) = E_q[F(μ') | a]
             = Risk - Ambiguity
             = Pragmatic_value + Epistemic_value

        Lower G = better action
        """
        # Simulate taking action: token emission changes listener state
        # (In reality, this would be a learned generative model)

        # Get token prototype
        token_vec = self.codebook[action_id]

        # Predict new observation after action
        # Simple model: listener shifts toward emitted token
        predicted_obs = 0.7 * self.mu_obs + 0.3 * token_vec

        # Expected prediction error after action
        predicted_mu = self.mu  # Assume beliefs don't change immediately
        expected_error = predicted_mu - predicted_obs

        # Pragmatic value: Will I achieve my goals?
        # (Minimize prediction error)
        pragmatic = 0.5 * self.params.π_obs * np.sum(expected_error ** 2)

        # Epistemic value: Will I learn something?
        # (Reduce uncertainty about observations)
        # Higher expected precision = more informative = lower G
        epistemic = -np.log(self.expected_precision[action_id] + 1e-8)

        # Expected free energy
        G = pragmatic + epistemic

        return G

    def select_action(self, temperature: float = 1.0) -> int:
        """
        Select action by minimizing expected free energy.

        Policy: π(a) ∝ exp(-G(a) / temperature)

        Args:
            temperature: Exploration parameter (high = more random)

        Returns:
            action_id (token to emit)
        """
        # Compute G for all actions
        G = np.array([self.compute_expected_free_energy(a)
                      for a in range(self.vocab_size)])

        # Softmin: prefer actions with low G
        policy = np.exp(-G / temperature)
        policy = policy / np.sum(policy)

        # Sample action
        action = np.random.choice(self.vocab_size, p=policy)

        return action

    def act(self, action_id: int) -> np.ndarray:
        """
        Execute action: emit token.

        This changes the world (listener state), closing the loop.

        Returns:
            Predicted new observation
        """
        # Get token vector
        token_vec = self.codebook[action_id]

        # Predict how listener will respond
        # (In real system, this is actual listener feedback)
        new_obs = 0.7 * self.mu_obs + 0.3 * token_vec + np.random.randn(self.n_dims) * 0.05

        return new_obs

    def step_active_inference(self, should_act: bool = False) -> dict:
        """
        Full active inference step: perception + action.

        1. Perceptual inference: Update μ to minimize F
        2. (Optional) Active inference: Select and execute action

        Args:
            should_act: Whether to emit token this step

        Returns:
            Diagnostics + action info
        """
        # 1. PERCEPTION: Update beliefs
        diagnostics = self.step(observation=self.mu_obs)

        # 2. ACTION: Emit token if triggered
        action_info = None
        if should_act:
            # Select action that minimizes expected free energy
            action = self.select_action(temperature=0.5)

            # Execute action (changes world)
            new_obs = self.act(action)

            # Update observation (close the loop)
            self.mu_obs = new_obs

            action_info = {
                'action': action,
                'token_vec': self.codebook[action]
            }

        diagnostics['action'] = action_info
        return diagnostics


# Example usage
if __name__ == "__main__":
    print("=== Active Inference Demo ===\n")

    params = FreeEnergyParams(
        π_obs=2.0,     # High precision = trust observations
        π_prior=0.1,
        g=0.1,
        lam=0.3
    )

    engine = ActiveInferenceEngine(params, n_dims=256, vocab_size=50)

    # Initialize with random observation
    engine.perceive(np.random.randn(256) * 0.5)

    # Run active inference
    for t in range(200):
        # Decide whether to act (simple threshold on prediction error)
        prediction_error = np.linalg.norm(engine.mu - engine.mu_obs)
        should_act = (t % 20 == 0) or (prediction_error < 0.1)

        # Active inference step
        diag = engine.step_active_inference(should_act=should_act)

        if diag['action'] is not None:
            print(f"t={t:3d} | F={diag['F_total']:7.2f} | "
                  f"Action={diag['action']['action']:2d} | "
                  f"Error={diag['prediction_error_norm']:.3f}")
```

---

## Part 5: Hierarchical Predictive Coding

### Multi-Level Free Energy

Extend to hierarchy: μ₁ (low-level), μ₂ (mid-level), μ₃ (high-level)

```python
class HierarchicalFreeEnergy:
    """
    Hierarchical predictive coding with multiple levels.

    Each level:
    - Predicts the level below
    - Is predicted by the level above
    - Minimizes prediction errors at its level

    Structure:
    μ₃ (context) → predicts → μ₂ (events) → predicts → μ₁ (sensory)
                  ← errors ←                ← errors ←
    """

    def __init__(self, dims=[64, 128, 256], precisions=[0.1, 1.0, 10.0]):
        self.n_levels = len(dims)
        self.dims = dims

        # States at each level
        self.mu = [np.zeros(d, dtype=np.float32) for d in dims]

        # Prediction errors at each level
        self.epsilon = [np.zeros(d, dtype=np.float32) for d in dims]

        # Precision (confidence) at each level
        self.pi = precisions

        # Generative model weights (learned or fixed)
        # g[i] maps from level i to level i-1
        self.g = [self._init_generative_weights(dims[i], dims[i-1])
                  for i in range(1, self.n_levels)]

    def _init_generative_weights(self, dim_high, dim_low):
        """Random generative model: μ_low = g·μ_high"""
        W = np.random.randn(dim_low, dim_high) * 0.1
        return W

    def predict_downward(self, level: int) -> np.ndarray:
        """
        Top-down prediction: level i predicts level i-1.

        ŷ_{i-1} = g_i(μ_i)
        """
        if level == 0:
            return None  # Bottom level receives sensory input

        # Linear generative model (can be nonlinear)
        prediction = self.g[level-1] @ self.mu[level]
        return prediction

    def compute_prediction_errors(self, sensory_input: np.ndarray):
        """
        Compute prediction errors at each level.

        ε₀ = μ₀ - sensory_input
        ε_i = μ_i - g(μ_{i+1}) for i > 0
        """
        # Bottom level: compare to sensory input
        self.epsilon[0] = self.mu[0] - sensory_input

        # Higher levels: compare to top-down prediction
        for level in range(1, self.n_levels):
            prediction = self.predict_downward(level)
            self.epsilon[level] = self.mu[level] - prediction

    def compute_hierarchical_free_energy(self) -> float:
        """
        Total free energy across hierarchy.

        F = Σ_i π_i·||ε_i||²
        """
        F = sum(self.pi[i] * np.sum(self.epsilon[i] ** 2)
                for i in range(self.n_levels))
        return F

    def update_beliefs(self, sensory_input: np.ndarray, dt: float = 0.01):
        """
        Update beliefs at all levels to minimize F.

        dμ_i/dt = -∂F/∂μ_i
                = π_i·ε_i - π_{i+1}·∂g_{i+1}/∂μ_i·ε_{i+1}
                   \_____/    \___________________________/
                  Bottom-up          Top-down
                 (sensory error)   (prediction from above)
        """
        # Compute current prediction errors
        self.compute_prediction_errors(sensory_input)

        # Update each level
        for level in range(self.n_levels):
            # Bottom-up error (from level below or sensors)
            bottom_up = self.pi[level] * self.epsilon[level]

            # Top-down error (from level above)
            top_down = np.zeros_like(self.mu[level])
            if level < self.n_levels - 1:
                # Gradient of prediction w.r.t. current level
                # For linear g: ∂g/∂μ = W^T
                grad_g = self.g[level].T
                top_down = self.pi[level+1] * (grad_g @ self.epsilon[level+1])

            # Gradient descent
            dmu = -bottom_up + top_down
            self.mu[level] += dt * dmu

    def step(self, sensory_input: np.ndarray) -> dict:
        """Single hierarchical inference step"""
        # Update all levels
        self.update_beliefs(sensory_input)

        # Compute free energy
        F = self.compute_hierarchical_free_energy()

        return {
            'F': F,
            'epsilon': [np.linalg.norm(e) for e in self.epsilon],
            'mu': [m.copy() for m in self.mu]
        }


# Example usage
if __name__ == "__main__":
    print("=== Hierarchical Predictive Coding Demo ===\n")

    # 3-level hierarchy
    hierarchy = HierarchicalFreeEnergy(
        dims=[256, 128, 64],         # Sensory → Mid → High
        precisions=[10.0, 1.0, 0.1]  # Trust sensory most
    )

    # Simulate sensory stream
    for t in range(500):
        # Sensory input (oscillating + noise)
        sensory = 0.5 * np.sin(0.02 * t) * np.ones(256)
        sensory += np.random.randn(256) * 0.1

        # Hierarchical inference
        diag = hierarchy.step(sensory)

        if t % 50 == 0:
            print(f"t={t:3d} | F={diag['F']:8.2f} | "
                  f"ε₀={diag['epsilon'][0]:.3f} | "
                  f"ε₁={diag['epsilon'][1]:.3f} | "
                  f"ε₂={diag['epsilon'][2]:.3f}")
```

---

## Part 6: Integration with Dialogue System

### Combining Free Energy with Recursive Dialogue

```python
from dialogue_system import DialogueConfig, RecursiveDialogueEngine
from free_energy_engine import FreeEnergyEngine, FreeEnergyParams

class FreeEnergyDialogue:
    """
    Recursive Dialogue + Free Energy Principle integration.

    Maps:
    - μ (speaker belief) ← FreeEnergyEngine
    - μ_listener (observation) ← LoMI layer
    - Emissions ← Active inference (action selection)
    - TDL ← Prior on valid syntax
    """

    def __init__(self, state_dims=256, vocab_size=100):
        # Free energy engine (replaces recursive engine)
        self.fe_params = FreeEnergyParams(
            π_obs=2.0,      # Trust listener state
            π_prior=0.1,    # Weak prior on μ
            g=0.15,
            lam=0.3,
            rho=0.4
        )
        self.fe_engine = ActiveInferenceEngine(
            self.fe_params,
            n_dims=state_dims,
            vocab_size=vocab_size
        )

        # Listener state (observations)
        self.mu_listener = np.zeros(state_dims, dtype=np.float32)

        # Emission threshold (based on free energy)
        self.emission_threshold = 50.0  # Emit when F drops below this

        self.t = 0

    def step(self, listener_input: Optional[np.ndarray] = None):
        """
        Single dialogue step with free energy dynamics.

        1. Update listener state (observation)
        2. Minimize free energy (perception)
        3. Check emission criterion (low F)
        4. If emit: select action via active inference
        """
        # Update observation
        if listener_input is not None:
            self.mu_listener = listener_input

        # Perceive (update beliefs)
        self.fe_engine.perceive(self.mu_listener)

        # Minimize F
        diagnostics = self.fe_engine.step()

        # Emission criterion: F below threshold
        F = diagnostics['F_total']
        should_emit = F < self.emission_threshold

        emission = None
        if should_emit:
            # Active inference: select action
            action = self.fe_engine.select_action(temperature=0.3)

            # Execute action (emit token)
            new_obs = self.fe_engine.act(action)

            # Update listener state (feedback)
            self.mu_listener = new_obs

            emission = {
                'time': self.t,
                'token': action,
                'free_energy': F,
                'prediction_error': diagnostics['prediction_error_norm']
            }

        self.t += 1

        return emission, diagnostics

    def converse(self, n_steps=500, listener_callback=None):
        """Run free energy dialogue"""
        emissions = []
        F_history = []

        for step in range(n_steps):
            # Get listener input
            listener_input = None
            if listener_callback:
                listener_input = listener_callback(step)

            # Step
            emission, diag = self.step(listener_input)

            F_history.append(diag['F_total'])

            if emission:
                emissions.append(emission)
                print(f"t={emission['time']:4d} → Token {emission['token']:3d} | "
                      f"F={emission['free_energy']:.2f}")

        return emissions, F_history


# Example usage
if __name__ == "__main__":
    print("=== Free Energy Dialogue Demo ===\n")

    # Create free energy dialogue system
    dialogue = FreeEnergyDialogue(state_dims=256, vocab_size=50)

    # Oscillating listener
    def listener(t):
        return 0.3 * np.sin(0.03 * t) * np.ones(256) + np.random.randn(256) * 0.01

    # Run dialogue
    emissions, F_history = dialogue.converse(n_steps=1000, listener_callback=listener)

    print(f"\nTotal emissions: {len(emissions)}")
    print(f"Mean F: {np.mean(F_history):.2f}")
    print(f"Final F: {F_history[-1]:.2f}")
```

---

## Part 7: Advanced Features

### Precision Weighting (Confidence)

```python
class PrecisionWeightedFE(FreeEnergyEngine):
    """
    Free energy with learnable precision (attention).

    Precision = inverse variance = confidence

    High precision → trust this signal more
    Low precision → ignore this signal
    """

    def __init__(self, params, n_dims=256):
        super().__init__(params, n_dims)

        # Learnable precision for each dimension
        self.pi_learned = np.ones(n_dims, dtype=np.float32)

    def update_precision(self):
        """
        Learn precision from prediction errors.

        High error → low confidence → decrease precision
        Low error → high confidence → increase precision
        """
        # Compute prediction error per dimension
        error = (self.mu - self.mu_obs) ** 2

        # Update precision (inverse of moving average error)
        alpha = 0.1  # Learning rate
        self.pi_learned = (1 - alpha) * self.pi_learned + alpha / (error + 1e-6)

        # Clip to reasonable range
        self.pi_learned = np.clip(self.pi_learned, 0.1, 10.0)

    def compute_free_energy_gradient(self):
        """Gradient with precision weighting"""
        # Element-wise precision weighting
        grad_accuracy = self.pi_learned * self.params.π_obs * (self.mu - self.mu_obs)

        # ... rest as before

        return grad_F

    def step(self, observation=None):
        """Step with precision learning"""
        diag = super().step(observation)

        # Learn precision
        self.update_precision()

        diag['precision'] = self.pi_learned.copy()
        return diag
```

### Curiosity and Epistemic Foraging

```python
def compute_epistemic_value(self, action_id: int) -> float:
    """
    Epistemic value: How much will I learn?

    High when action reduces uncertainty about environment.
    Drives exploration and curiosity.
    """
    # Current uncertainty (entropy of beliefs)
    H_current = -np.sum(self.mu ** 2 * np.log(np.abs(self.mu) ** 2 + 1e-8))

    # Predicted uncertainty after action
    # (Simplified: assume action reveals information)
    token_vec = self.codebook[action_id]
    H_predicted = H_current - np.linalg.norm(token_vec) * 0.1

    # Information gain
    epistemic_value = H_current - H_predicted

    return epistemic_value

def select_action_with_curiosity(self, pragmatic_weight=0.7, epistemic_weight=0.3):
    """
    Balance exploitation (minimize error) and exploration (reduce uncertainty).

    G(a) = w_pragmatic·Pragmatic(a) - w_epistemic·Epistemic(a)
    """
    G = np.zeros(self.vocab_size)

    for a in range(self.vocab_size):
        pragmatic = self.compute_expected_free_energy(a)
        epistemic = self.compute_epistemic_value(a)

        G[a] = pragmatic_weight * pragmatic - epistemic_weight * epistemic

    # Softmin
    policy = np.exp(-G / 0.5)
    policy /= np.sum(policy)

    action = np.random.choice(self.vocab_size, p=policy)
    return action
```

---

## Part 8: Comparison Summary

### What Changed?

| Component | Before (Base) | After (Free Energy) |
|-----------|---------------|---------------------|
| **Objective** | Implicit coherence | Explicit F minimization |
| **Update rule** | PDE dynamics | Gradient descent on F |
| **Observations** | μ_listener coupling | Precision-weighted sensory input |
| **Emissions** | Entropy threshold | Active inference (action selection) |
| **Learning** | None | Precision learning, generative model |
| **Hierarchy** | Single μ | Multi-level predictive coding |
| **Interpretation** | Physical dynamics | Bayesian inference |

### Benefits of Free Energy Formulation

✅ **Principled framework**: Rooted in variational Bayes
✅ **Interpretable**: Every term has clear meaning
✅ **Flexible**: Easy to add priors, constraints
✅ **Learnable**: Precision and generative model can be learned
✅ **Biological**: Matches predictive coding in cortex
✅ **Unified**: Perception + action in single framework
✅ **Curiosity**: Natural exploration via epistemic value

---

## Part 9: Implementation Checklist

### Minimal Changes to Existing Code

To convert `recursive_engine.py` → free energy:

```python
# 1. Rename variables for clarity
self.mu          # Keep (beliefs)
self.mu_obs      # Add (observations, was mu_listener)

# 2. Add precision parameters
self.π_obs = 1.0
self.π_prior = 0.1

# 3. Reinterpret dynamics as F gradient
grad_F = self.π_obs * (self.mu - self.mu_obs) + \
         self.π_prior * self.mu + \
         self.g * laplacian - \
         self.lam * self.mu**3

# 4. Update rule (gradient descent)
self.mu -= dt * grad_F  # Instead of complex PDE update

# 5. Add F computation for diagnostics
F = 0.5 * self.π_obs * ||self.mu - self.mu_obs||² + \
    0.5 * self.π_prior * ||self.mu||²
```

That's it! The dynamics are nearly identical, just reinterpreted.

---

## Conclusion

**Your current system already implements ~80% of Free Energy Principle!**

**What you have:**
- μ minimizing distance to μ_listener ✓
- Attractor dynamics ✓
- Emission as "action" ✓

**What to add:**
- Explicit F computation (5 lines)
- Precision weighting (10 lines)
- Active inference action selection (20 lines)
- Hierarchical levels (optional, 50 lines)

**The math is already there—just need to rename variables and add F tracking.**

Let me know which part you want to implement first:
1. Basic FreeEnergyEngine (simplest)
2. ActiveInferenceEngine (adds action selection)
3. HierarchicalFreeEnergy (full predictive coding)
4. Integration with dialogue system

I can write the complete working code for any of these!
