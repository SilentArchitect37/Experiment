"""
External Data Validation Framework
====================================

Mathematical formula for evaluating external information sources based on
truthfulness rather than just accepting arbitrary data.

Core Philosophy:
---------------
Truth emerges through multi-dimensional coherence: an external claim is
credible when it maintains high coherence across multiple validation axes.

Mathematical Foundation:
-----------------------

Truth Score T(x) for external data x:

    T(x) = Σᵢ wᵢ · Cᵢ(x) / Σᵢ wᵢ

Where Cᵢ(x) are coherence measures across different dimensions:

    C₁: Source Credibility (ρₛ)
    C₂: Internal Consistency (κᵢ)
    C₃: Cross-Reference Validation (ξᵣ)
    C₄: Temporal Coherence (τₜ)
    C₅: Semantic Alignment (σₐ)
    C₆: Evidence Strength (εₑ)

Each coherence measure ∈ [0, 1], with the final truth score T(x) ∈ [0, 1].

Detailed Formulas:
------------------

1. SOURCE CREDIBILITY (ρₛ):
   Evaluates the reliability of the information source

   ρₛ = sigmoid(α·h + β·v + γ·a - δ·b)

   Where:
   - h: Historical accuracy rate of source
   - v: Verification by independent authorities
   - a: Academic/professional credentials
   - b: Bias indicators (conflicts of interest, etc.)
   - α, β, γ, δ: Weighting parameters

2. INTERNAL CONSISTENCY (κᵢ):
   Checks for logical contradictions within the data

   κᵢ = 1 - (N_contradictions / N_claims) · exp(-λ·coherence_score)

   Where:
   - N_contradictions: Number of detected logical conflicts
   - N_claims: Total number of claims
   - coherence_score: Semantic coherence of the narrative
   - λ: Decay parameter

3. CROSS-REFERENCE VALIDATION (ξᵣ):
   Compares data against multiple independent sources

   ξᵣ = (1/N) Σⱼ sim(x, sⱼ) · credibility(sⱼ)

   Where:
   - N: Number of reference sources
   - sim(x, sⱼ): Similarity between claim x and source j
   - credibility(sⱼ): Independent credibility of source j

4. TEMPORAL COHERENCE (τₜ):
   Validates consistency over time

   τₜ = exp(-Σₜ |xₜ - xₜ₋₁|² / (2σ²))

   Where:
   - xₜ: Claim at time t
   - σ²: Expected variance for stable information

5. SEMANTIC ALIGNMENT (σₐ):
   Measures coherence with established knowledge

   σₐ = ⟨x, K⟩ / (||x|| · ||K||)

   Where:
   - ⟨x, K⟩: Inner product between claim embedding and knowledge base
   - ||·||: Vector norms (cosine similarity)

6. EVIDENCE STRENGTH (εₑ):
   Quantifies the quality and quantity of supporting evidence

   εₑ = tanh(Σₙ qₙ · rₙ / Z)

   Where:
   - qₙ: Quality score of evidence piece n
   - rₙ: Relevance score of evidence piece n
   - Z: Normalization constant

ADAPTIVE WEIGHTING:
------------------

Weights wᵢ are not fixed but adapt based on context:

    wᵢ(context) = w⁰ᵢ · exp(Σⱼ φⱼ · contextⱼ)

This allows the system to emphasize different validation dimensions
based on the type of information being evaluated.

DECISION THRESHOLD:
------------------

Accept data x if T(x) > θ, where θ is a configurable threshold:
- θ = 0.5: Balanced (default)
- θ = 0.7: High confidence required
- θ = 0.3: More permissive (exploration mode)

UNCERTAINTY QUANTIFICATION:
--------------------------

Truth score comes with uncertainty estimate:

    U(x) = √(Var[Cᵢ(x)]) · (1 - mean[Cᵢ(x)])

High uncertainty indicates need for additional validation.

"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import warnings


@dataclass
class ValidationParams:
    """Parameters for external data validation"""

    # Coherence measure weights (default equal weighting)
    w_source: float = 1.0        # Source credibility weight
    w_internal: float = 1.0      # Internal consistency weight
    w_cross_ref: float = 1.0     # Cross-reference weight
    w_temporal: float = 1.0      # Temporal coherence weight
    w_semantic: float = 1.0      # Semantic alignment weight
    w_evidence: float = 1.0      # Evidence strength weight

    # Source credibility parameters (ρₛ)
    alpha: float = 0.4    # Historical accuracy weight
    beta: float = 0.3     # Verification weight
    gamma: float = 0.2    # Credentials weight
    delta: float = 0.3    # Bias penalty weight

    # Internal consistency parameters (κᵢ)
    lambda_decay: float = 1.0    # Coherence decay rate

    # Temporal coherence parameters (τₜ)
    sigma_temporal: float = 0.5  # Expected temporal variance

    # Decision threshold
    truth_threshold: float = 0.5  # Minimum score to accept data

    # Uncertainty tolerance
    max_uncertainty: float = 0.3  # Maximum acceptable uncertainty


@dataclass
class DataSource:
    """Represents an external information source"""

    # Source identity
    name: str

    # Credibility factors
    historical_accuracy: float = 0.5    # h ∈ [0, 1]
    verification_score: float = 0.5     # v ∈ [0, 1]
    credential_score: float = 0.5       # a ∈ [0, 1]
    bias_score: float = 0.0             # b ∈ [0, 1], lower is better

    # Historical data
    past_claims: List[np.ndarray] = None

    def __post_init__(self):
        if self.past_claims is None:
            self.past_claims = []


@dataclass
class ExternalClaim:
    """Represents a claim from an external source"""

    # Content
    embedding: np.ndarray          # Semantic embedding of claim
    evidence: List[Tuple[float, float]] = None  # [(quality, relevance), ...]

    # Metadata
    source: DataSource = None
    timestamp: float = 0.0

    # Internal structure
    n_claims: int = 1              # Number of sub-claims
    n_contradictions: int = 0      # Detected logical conflicts
    coherence_score: float = 1.0   # Narrative coherence [0, 1]

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


class ExternalDataValidator:
    """
    Validates external information using multi-dimensional coherence analysis

    Usage:
        validator = ExternalDataValidator(params)

        # Define a source
        source = DataSource(
            name="Scientific Journal",
            historical_accuracy=0.85,
            verification_score=0.90,
            credential_score=0.95,
            bias_score=0.05
        )

        # Create a claim
        claim = ExternalClaim(
            embedding=np.random.randn(128),
            source=source,
            evidence=[(0.8, 0.9), (0.7, 0.8)]
        )

        # Validate
        truth_score, uncertainty, accept = validator.validate(claim)
    """

    def __init__(self, params: Optional[ValidationParams] = None,
                 knowledge_base: Optional[np.ndarray] = None):
        """
        Initialize validator

        Args:
            params: Validation parameters
            knowledge_base: Semantic embedding of established knowledge
        """
        self.params = params or ValidationParams()

        # Knowledge base for semantic alignment
        if knowledge_base is not None:
            self.knowledge_base = knowledge_base
        else:
            # Initialize with random baseline (should be replaced with real KB)
            self.knowledge_base = np.random.randn(128)

        # Normalize knowledge base
        kb_norm = np.linalg.norm(self.knowledge_base)
        if kb_norm > 0:
            self.knowledge_base = self.knowledge_base / kb_norm

        # Cross-reference database
        self.reference_sources: List[Tuple[DataSource, np.ndarray]] = []

        # Validation history
        self.validation_history: List[Dict] = []

    def validate(self, claim: ExternalClaim,
                 cross_references: Optional[List[ExternalClaim]] = None) -> Tuple[float, float, bool]:
        """
        Compute truth score for external claim

        Args:
            claim: The claim to validate
            cross_references: Optional list of claims from other sources for comparison

        Returns:
            (truth_score, uncertainty, accept_decision)
        """

        # Compute all coherence measures
        coherence_scores = {}

        # C₁: Source credibility
        coherence_scores['source'] = self._compute_source_credibility(claim)

        # C₂: Internal consistency
        coherence_scores['internal'] = self._compute_internal_consistency(claim)

        # C₃: Cross-reference validation
        coherence_scores['cross_ref'] = self._compute_cross_reference(claim, cross_references)

        # C₄: Temporal coherence
        coherence_scores['temporal'] = self._compute_temporal_coherence(claim)

        # C₅: Semantic alignment
        coherence_scores['semantic'] = self._compute_semantic_alignment(claim)

        # C₆: Evidence strength
        coherence_scores['evidence'] = self._compute_evidence_strength(claim)

        # Compute weighted truth score
        truth_score = self._compute_truth_score(coherence_scores)

        # Compute uncertainty
        uncertainty = self._compute_uncertainty(coherence_scores)

        # Make decision
        accept = (truth_score > self.params.truth_threshold and
                 uncertainty < self.params.max_uncertainty)

        # Log validation
        self.validation_history.append({
            'claim': claim,
            'coherence_scores': coherence_scores,
            'truth_score': truth_score,
            'uncertainty': uncertainty,
            'accept': accept
        })

        return truth_score, uncertainty, accept

    def _sigmoid(self, x: float) -> float:
        """Numerically stable sigmoid"""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def _compute_source_credibility(self, claim: ExternalClaim) -> float:
        """
        C₁: Source credibility

        ρₛ = sigmoid(α·h + β·v + γ·a - δ·b)
        """
        if claim.source is None:
            return 0.5  # Neutral if no source info

        p = self.params
        s = claim.source

        score = (p.alpha * s.historical_accuracy +
                p.beta * s.verification_score +
                p.gamma * s.credential_score -
                p.delta * s.bias_score)

        return self._sigmoid(score)

    def _compute_internal_consistency(self, claim: ExternalClaim) -> float:
        """
        C₂: Internal consistency

        κᵢ = 1 - (N_contradictions / N_claims) · exp(-λ·coherence_score)
        """
        if claim.n_claims == 0:
            return 1.0

        contradiction_ratio = claim.n_contradictions / claim.n_claims
        coherence_factor = np.exp(-self.params.lambda_decay * claim.coherence_score)

        consistency = 1.0 - contradiction_ratio * coherence_factor

        return np.clip(consistency, 0.0, 1.0)

    def _compute_cross_reference(self, claim: ExternalClaim,
                                cross_references: Optional[List[ExternalClaim]]) -> float:
        """
        C₃: Cross-reference validation

        ξᵣ = (1/N) Σⱼ sim(x, sⱼ) · credibility(sⱼ)
        """
        if cross_references is None or len(cross_references) == 0:
            # No cross-references available - return neutral score
            return 0.5

        total_score = 0.0

        for ref_claim in cross_references:
            # Compute similarity (cosine similarity of embeddings)
            similarity = self._cosine_similarity(claim.embedding, ref_claim.embedding)

            # Get reference source credibility
            ref_credibility = self._compute_source_credibility(ref_claim)

            total_score += similarity * ref_credibility

        return total_score / len(cross_references)

    def _compute_temporal_coherence(self, claim: ExternalClaim) -> float:
        """
        C₄: Temporal coherence

        τₜ = exp(-Σₜ |xₜ - xₜ₋₁|² / (2σ²))
        """
        if claim.source is None or len(claim.source.past_claims) == 0:
            return 1.0  # No history, assume coherent

        # Compare with past claims from same source
        total_divergence = 0.0
        n_comparisons = 0

        for past_claim_embedding in claim.source.past_claims[-5:]:  # Last 5 claims
            divergence = np.sum((claim.embedding - past_claim_embedding) ** 2)
            total_divergence += divergence
            n_comparisons += 1

        if n_comparisons == 0:
            return 1.0

        avg_divergence = total_divergence / n_comparisons
        sigma_sq = self.params.sigma_temporal ** 2

        coherence = np.exp(-avg_divergence / (2 * sigma_sq))

        return coherence

    def _compute_semantic_alignment(self, claim: ExternalClaim) -> float:
        """
        C₅: Semantic alignment with knowledge base

        σₐ = ⟨x, K⟩ / (||x|| · ||K||)
        """
        # Cosine similarity with knowledge base
        alignment = self._cosine_similarity(claim.embedding, self.knowledge_base)

        # Map from [-1, 1] to [0, 1]
        # -1 (opposite) → 0, 0 (orthogonal) → 0.5, 1 (aligned) → 1
        return (alignment + 1.0) / 2.0

    def _compute_evidence_strength(self, claim: ExternalClaim) -> float:
        """
        C₆: Evidence strength

        εₑ = tanh(Σₙ qₙ · rₙ / Z)
        """
        if len(claim.evidence) == 0:
            return 0.3  # Low score if no evidence provided

        total_strength = 0.0

        for quality, relevance in claim.evidence:
            total_strength += quality * relevance

        # Normalize by number of evidence pieces (diminishing returns)
        Z = np.sqrt(len(claim.evidence))

        strength = np.tanh(total_strength / Z)

        return strength

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return np.dot(a, b) / (norm_a * norm_b)

    def _compute_truth_score(self, coherence_scores: Dict[str, float]) -> float:
        """
        Compute weighted truth score

        T(x) = Σᵢ wᵢ · Cᵢ(x) / Σᵢ wᵢ
        """
        p = self.params

        weights = {
            'source': p.w_source,
            'internal': p.w_internal,
            'cross_ref': p.w_cross_ref,
            'temporal': p.w_temporal,
            'semantic': p.w_semantic,
            'evidence': p.w_evidence
        }

        weighted_sum = sum(weights[k] * coherence_scores[k] for k in weights.keys())
        total_weight = sum(weights.values())

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _compute_uncertainty(self, coherence_scores: Dict[str, float]) -> float:
        """
        Compute uncertainty estimate

        U(x) = √(Var[Cᵢ(x)]) · (1 - mean[Cᵢ(x)])
        """
        scores = np.array(list(coherence_scores.values()))

        variance = np.var(scores)
        mean_score = np.mean(scores)

        # High variance OR low mean → high uncertainty
        uncertainty = np.sqrt(variance) * (1.0 - mean_score)

        return np.clip(uncertainty, 0.0, 1.0)

    def add_to_knowledge_base(self, claim: ExternalClaim):
        """
        Add validated claim to knowledge base

        Updates KB embedding using exponential moving average
        """
        alpha = 0.1  # Learning rate

        self.knowledge_base = (1 - alpha) * self.knowledge_base + alpha * claim.embedding

        # Renormalize
        kb_norm = np.linalg.norm(self.knowledge_base)
        if kb_norm > 0:
            self.knowledge_base = self.knowledge_base / kb_norm

    def add_cross_reference(self, source: DataSource, embedding: np.ndarray):
        """Add a reference source for cross-validation"""
        self.reference_sources.append((source, embedding))

    def get_validation_stats(self) -> Dict:
        """Get statistics about validation history"""
        if len(self.validation_history) == 0:
            return {}

        truth_scores = [v['truth_score'] for v in self.validation_history]
        uncertainties = [v['uncertainty'] for v in self.validation_history]
        accept_rate = sum(v['accept'] for v in self.validation_history) / len(self.validation_history)

        return {
            'n_validations': len(self.validation_history),
            'mean_truth_score': np.mean(truth_scores),
            'std_truth_score': np.std(truth_scores),
            'mean_uncertainty': np.mean(uncertainties),
            'accept_rate': accept_rate
        }


def create_demo_scenario():
    """Demonstrate the validation framework"""

    print("=" * 70)
    print("EXTERNAL DATA VALIDATION FRAMEWORK - DEMO")
    print("=" * 70)
    print()

    # Create validator
    params = ValidationParams(
        truth_threshold=0.6,  # Require 60% confidence
        max_uncertainty=0.25
    )

    validator = ExternalDataValidator(params)

    # Define sources
    reliable_source = DataSource(
        name="Peer-Reviewed Journal",
        historical_accuracy=0.90,
        verification_score=0.95,
        credential_score=0.95,
        bias_score=0.05
    )

    questionable_source = DataSource(
        name="Unverified Blog",
        historical_accuracy=0.50,
        verification_score=0.20,
        credential_score=0.30,
        bias_score=0.60
    )

    # Test Case 1: High credibility claim with strong evidence
    print("Test 1: High Credibility Source with Strong Evidence")
    print("-" * 70)

    claim1 = ExternalClaim(
        embedding=np.random.randn(128),
        source=reliable_source,
        n_claims=5,
        n_contradictions=0,
        coherence_score=0.95,
        evidence=[
            (0.9, 0.95),  # High quality, highly relevant
            (0.85, 0.90),
            (0.80, 0.85)
        ]
    )

    truth1, uncertainty1, accept1 = validator.validate(claim1)

    print(f"Truth Score: {truth1:.3f}")
    print(f"Uncertainty: {uncertainty1:.3f}")
    print(f"Decision: {'ACCEPT' if accept1 else 'REJECT'}")
    print()

    # Test Case 2: Low credibility source
    print("Test 2: Low Credibility Source")
    print("-" * 70)

    claim2 = ExternalClaim(
        embedding=np.random.randn(128),
        source=questionable_source,
        n_claims=3,
        n_contradictions=1,
        coherence_score=0.60,
        evidence=[
            (0.4, 0.5)  # Low quality evidence
        ]
    )

    truth2, uncertainty2, accept2 = validator.validate(claim2)

    print(f"Truth Score: {truth2:.3f}")
    print(f"Uncertainty: {uncertainty2:.3f}")
    print(f"Decision: {'ACCEPT' if accept2 else 'REJECT'}")
    print()

    # Test Case 3: Medium source with cross-validation
    print("Test 3: Cross-Reference Validation")
    print("-" * 70)

    medium_source = DataSource(
        name="News Outlet",
        historical_accuracy=0.70,
        verification_score=0.65,
        credential_score=0.60,
        bias_score=0.25
    )

    claim3 = ExternalClaim(
        embedding=np.random.randn(128),
        source=medium_source,
        n_claims=2,
        n_contradictions=0,
        coherence_score=0.80,
        evidence=[(0.7, 0.8)]
    )

    # Create similar claims from other sources for cross-validation
    cross_refs = [
        ExternalClaim(
            embedding=claim3.embedding + np.random.randn(128) * 0.1,  # Similar
            source=reliable_source
        ),
        ExternalClaim(
            embedding=claim3.embedding + np.random.randn(128) * 0.15,  # Similar
            source=reliable_source
        )
    ]

    truth3, uncertainty3, accept3 = validator.validate(claim3, cross_references=cross_refs)

    print(f"Truth Score: {truth3:.3f}")
    print(f"Uncertainty: {uncertainty3:.3f}")
    print(f"Decision: {'ACCEPT' if accept3 else 'REJECT'}")
    print(f"(Cross-validated against {len(cross_refs)} reliable sources)")
    print()

    # Test Case 4: Contradictory claim
    print("Test 4: Internally Contradictory Claim")
    print("-" * 70)

    claim4 = ExternalClaim(
        embedding=np.random.randn(128),
        source=reliable_source,  # Even from reliable source
        n_claims=10,
        n_contradictions=5,  # Half the claims contradict each other
        coherence_score=0.30,
        evidence=[(0.8, 0.9)]
    )

    truth4, uncertainty4, accept4 = validator.validate(claim4)

    print(f"Truth Score: {truth4:.3f}")
    print(f"Uncertainty: {uncertainty4:.3f}")
    print(f"Decision: {'ACCEPT' if accept4 else 'REJECT'}")
    print()

    # Summary statistics
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    stats = validator.get_validation_stats()
    print(f"Total validations: {stats['n_validations']}")
    print(f"Mean truth score: {stats['mean_truth_score']:.3f} ± {stats['std_truth_score']:.3f}")
    print(f"Mean uncertainty: {stats['mean_uncertainty']:.3f}")
    print(f"Accept rate: {stats['accept_rate']:.1%}")
    print()

    return validator


if __name__ == "__main__":
    validator = create_demo_scenario()

    print("\n" + "=" * 70)
    print("FORMULA SUMMARY")
    print("=" * 70)
    print("""
Truth Score T(x) combines six coherence dimensions:

    T(x) = Σᵢ wᵢ · Cᵢ(x) / Σᵢ wᵢ

Where:
    C₁ (ρₛ): Source Credibility      → Evaluates source reliability
    C₂ (κᵢ): Internal Consistency    → Detects logical contradictions
    C₃ (ξᵣ): Cross-Reference Valid.  → Compares with other sources
    C₄ (τₜ): Temporal Coherence      → Checks consistency over time
    C₅ (σₐ): Semantic Alignment      → Matches established knowledge
    C₆ (εₑ): Evidence Strength       → Quantifies supporting evidence

Decision: Accept if T(x) > θ AND U(x) < max_uncertainty

This framework doesn't just accept external data blindly—it judges
truthfulness through multi-dimensional coherence analysis.
    """)
