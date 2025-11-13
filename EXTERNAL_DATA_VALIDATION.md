# External Data Validation: Mathematical Framework

## Overview

This document describes a mathematical formula for **evaluating external information sources based on truthfulness**, rather than blindly accepting arbitrary data.

The framework is designed to integrate with the Recursive Dialogue Engine's philosophy of coherence-based reasoning.

## Core Philosophy

**Truth emerges through multi-dimensional coherence.**

An external claim is credible when it maintains high coherence across multiple independent validation axes. This is analogous to how the recursive dialogue engine validates meaning through phase alignment and recursive entropy stabilization.

## The Truth Score Formula

### Main Equation

For external data **x**, the truth score **T(x)** is:

```
T(x) = Σᵢ wᵢ · Cᵢ(x) / Σᵢ wᵢ
```

Where:
- **wᵢ**: Weight for coherence dimension *i*
- **Cᵢ(x)**: Coherence score for dimension *i* ∈ [0, 1]
- **T(x)**: Final truth score ∈ [0, 1]

### Six Coherence Dimensions

The formula evaluates external data across six independent dimensions:

| Symbol | Dimension | What It Measures |
|--------|-----------|------------------|
| **ρₛ** | Source Credibility | Is the source reliable? |
| **κᵢ** | Internal Consistency | Does the claim contradict itself? |
| **ξᵣ** | Cross-Reference Validation | Do other sources agree? |
| **τₜ** | Temporal Coherence | Is it consistent over time? |
| **σₐ** | Semantic Alignment | Does it fit established knowledge? |
| **εₑ** | Evidence Strength | How strong is the supporting evidence? |

## Detailed Mathematical Formulas

### 1. Source Credibility (ρₛ)

Evaluates the reliability and trustworthiness of the information source.

```
ρₛ = sigmoid(α·h + β·v + γ·a - δ·b)
```

**Parameters:**
- **h**: Historical accuracy rate (past performance)
- **v**: Verification by independent authorities
- **a**: Academic/professional credentials
- **b**: Bias indicators (conflicts of interest, political/commercial bias)
- **α, β, γ, δ**: Weighting coefficients

**Example Values:**
- Peer-reviewed journal: h=0.90, v=0.95, a=0.95, b=0.05 → ρₛ ≈ 0.93
- Unverified blog: h=0.50, v=0.20, a=0.30, b=0.60 → ρₛ ≈ 0.37
- Social media post: h=0.40, v=0.10, a=0.20, b=0.70 → ρₛ ≈ 0.25

**Rationale:** Sources with proven track records, independent verification, strong credentials, and low bias are more trustworthy.

---

### 2. Internal Consistency (κᵢ)

Detects logical contradictions within the data itself.

```
κᵢ = 1 - (N_contradictions / N_claims) · exp(-λ·coherence_score)
```

**Parameters:**
- **N_contradictions**: Number of detected logical conflicts
- **N_claims**: Total number of claims or statements
- **coherence_score**: Semantic coherence of the narrative ∈ [0, 1]
- **λ**: Decay parameter (how much coherence compensates for contradictions)

**Example:**
- 10 claims, 0 contradictions, high coherence → κᵢ ≈ 1.0
- 10 claims, 5 contradictions, low coherence → κᵢ ≈ 0.2
- 10 claims, 2 contradictions, high coherence → κᵢ ≈ 0.7

**Rationale:** Self-contradictory information is inherently less trustworthy. Even a single contradiction undermines credibility.

---

### 3. Cross-Reference Validation (ξᵣ)

Compares the claim against multiple independent sources.

```
ξᵣ = (1/N) Σⱼ sim(x, sⱼ) · credibility(sⱼ)
```

**Parameters:**
- **N**: Number of reference sources
- **sim(x, sⱼ)**: Similarity between claim *x* and source *j* (e.g., cosine similarity of embeddings)
- **credibility(sⱼ)**: Independent credibility score of source *j*

**Example:**
- Claim confirmed by 3 reliable sources with high similarity → ξᵣ ≈ 0.85
- Claim contradicted by reliable sources → ξᵣ ≈ 0.20
- Claim with no cross-references available → ξᵣ = 0.5 (neutral)

**Rationale:** Independent corroboration increases confidence. The "wisdom of crowds" principle, weighted by source quality.

---

### 4. Temporal Coherence (τₜ)

Validates consistency of information over time.

```
τₜ = exp(-Σₜ |xₜ - xₜ₋₁|² / (2σ²))
```

**Parameters:**
- **xₜ**: Claim representation at time *t*
- **σ²**: Expected variance for stable information
- Sum is over recent time points

**Example:**
- Source has been saying the same thing consistently → τₜ ≈ 1.0
- Source keeps changing their story → τₜ ≈ 0.3
- New source with no history → τₜ = 1.0 (benefit of doubt)

**Rationale:** Reliable information remains stable over time. Frequent changes suggest unreliability or manipulation.

---

### 5. Semantic Alignment (σₐ)

Measures coherence with established, validated knowledge.

```
σₐ = ⟨x, K⟩ / (||x|| · ||K||)
```

**Parameters:**
- **⟨x, K⟩**: Inner product (dot product) between claim embedding *x* and knowledge base *K*
- **||·||**: Vector norm
- This is the **cosine similarity** formula

**Mapping:**
- Cosine = 1 (perfectly aligned) → σₐ = 1.0
- Cosine = 0 (orthogonal/unrelated) → σₐ = 0.5
- Cosine = -1 (contradictory) → σₐ = 0.0

**Example:**
- "Water freezes at 0°C" vs. established physics → σₐ ≈ 0.95
- Novel but plausible theory → σₐ ≈ 0.60
- Claim contradicting established science → σₐ ≈ 0.15

**Rationale:** Claims consistent with established knowledge are more likely to be true. But we allow for novel discoveries (don't require σₐ = 1).

---

### 6. Evidence Strength (εₑ)

Quantifies the quality and quantity of supporting evidence.

```
εₑ = tanh(Σₙ qₙ · rₙ / Z)
```

**Parameters:**
- **qₙ**: Quality score of evidence piece *n*
- **rₙ**: Relevance score of evidence piece *n*
- **Z**: Normalization constant (e.g., √N to model diminishing returns)
- **tanh**: Bounded activation (maps to [0, 1])

**Example:**
- 5 high-quality, highly relevant pieces of evidence → εₑ ≈ 0.85
- 1 low-quality piece of evidence → εₑ ≈ 0.35
- No evidence provided → εₑ = 0.3 (low default)

**Rationale:** Strong, relevant evidence increases confidence. Multiple pieces of evidence are better than one (but with diminishing returns).

---

## Decision Criterion

Data *x* is **accepted** if:

```
T(x) > θ  AND  U(x) < U_max
```

Where:
- **θ**: Truth threshold (configurable, default 0.5)
- **U(x)**: Uncertainty estimate
- **U_max**: Maximum acceptable uncertainty (default 0.3)

### Truth Threshold Settings

| Threshold | Use Case |
|-----------|----------|
| θ = 0.3 | Exploratory mode (gather more data) |
| θ = 0.5 | Balanced (default) |
| θ = 0.7 | High confidence required (critical decisions) |
| θ = 0.9 | Extreme rigor (life-or-death situations) |

### Uncertainty Quantification

Uncertainty is computed from variance across coherence dimensions:

```
U(x) = √Var[Cᵢ(x)] · (1 - mean[Cᵢ(x)])
```

**Interpretation:**
- **High variance** → Dimensions disagree → High uncertainty
- **Low mean score** → Overall low confidence → High uncertainty
- **Both low** → Clear reject signal → Low uncertainty
- **Both high** → Clear accept signal → Low uncertainty

**Example:**
- All dimensions agree (high): [0.9, 0.85, 0.88, 0.92] → U ≈ 0.02 (very certain)
- Dimensions conflict: [0.9, 0.2, 0.85, 0.3] → U ≈ 0.25 (uncertain)

---

## Adaptive Weighting

Weights **wᵢ** are not fixed but adapt based on context:

```
wᵢ(context) = w⁰ᵢ · exp(Σⱼ φⱼ · contextⱼ)
```

This allows the system to emphasize different validation dimensions based on the type of information.

### Context-Based Weight Adaptation

| Context | Emphasized Dimensions |
|---------|----------------------|
| **Scientific claims** | Evidence (εₑ), Semantic Alignment (σₐ) |
| **Breaking news** | Cross-reference (ξᵣ), Source Credibility (ρₛ) |
| **Historical facts** | Temporal Coherence (τₜ), Cross-reference (ξᵣ) |
| **Personal testimony** | Internal Consistency (κᵢ), Source Credibility (ρₛ) |

---

## Comparison to Other Approaches

### vs. Simple Source Credibility

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| **Just trust reliable sources** | Simple, fast | Misses contradictions, biases, contextual issues |
| **Our multi-dimensional formula** | Robust, catches multiple failure modes | More complex, requires more computation |

### vs. Machine Learning Fact-Checking

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| **ML models (BERT, etc.)** | Can learn complex patterns | Black box, needs massive training data, brittle |
| **Our mathematical formula** | Interpretable, explainable, works with minimal data | May miss subtle patterns |

### Hybrid Approach (Recommended)

Use **both**:
1. ML model provides initial credibility scores (h, v, a, b)
2. Mathematical formula combines them with other coherence measures
3. Get interpretability + pattern recognition

---

## Example Use Cases

### 1. Scientific Paper Validation

```python
# High-quality journal paper
source = DataSource(
    name="Nature",
    historical_accuracy=0.95,
    verification_score=0.98,
    credential_score=0.99,
    bias_score=0.02
)

claim = ExternalClaim(
    embedding=paper_embedding,
    source=source,
    n_claims=20,
    n_contradictions=0,
    coherence_score=0.95,
    evidence=[
        (0.95, 0.98),  # Experimental data
        (0.90, 0.95),  # Statistical analysis
        (0.88, 0.92)   # Peer review
    ]
)

# Expected: T(x) ≈ 0.90-0.95, U(x) ≈ 0.03-0.05 → ACCEPT
```

### 2. Social Media Rumor

```python
# Unverified social media post
source = DataSource(
    name="Anonymous Twitter Account",
    historical_accuracy=0.30,
    verification_score=0.05,
    credential_score=0.10,
    bias_score=0.80
)

claim = ExternalClaim(
    embedding=tweet_embedding,
    source=source,
    n_claims=3,
    n_contradictions=1,
    coherence_score=0.40,
    evidence=[]  # No evidence provided
)

# Expected: T(x) ≈ 0.25-0.35 → REJECT
```

### 3. News Article with Cross-Validation

```python
# Medium-credibility news outlet
source = DataSource(
    name="Regional Newspaper",
    historical_accuracy=0.70,
    verification_score=0.60,
    credential_score=0.65,
    bias_score=0.30
)

claim = ExternalClaim(
    embedding=article_embedding,
    source=source,
    evidence=[(0.70, 0.75)]
)

# Cross-validate with other sources
cross_refs = [
    reliable_source_claim_1,  # ρₛ = 0.90
    reliable_source_claim_2,  # ρₛ = 0.85
]

# With cross-validation: T(x) increases by ~0.10-0.15
# Expected: T(x) ≈ 0.65-0.75 → LIKELY ACCEPT
```

---

## Integration with Recursive Dialogue Engine

This validation framework complements the existing recursive dialogue engine:

### Philosophical Alignment

| Dialogue Engine | Data Validator |
|----------------|----------------|
| **Coherence through recursion** | **Coherence through multi-dimensional analysis** |
| Phase alignment (μₛ ↔ μₗ) | Cross-reference alignment (x ↔ sⱼ) |
| Recursive entropy minimization | Uncertainty minimization |
| Emission when entropy stabilizes | Accept when truth score stabilizes |

### Technical Integration

```python
from dialogue_system import RecursiveDialogueEngine
from external_data_validator import ExternalDataValidator

# Create dialogue engine
dialogue = RecursiveDialogueEngine(config)

# Create validator
validator = ExternalDataValidator(params)

# Use validator to filter external inputs to dialogue system
def validated_listener(t, mu):
    # Get external input
    external_input = get_external_data()

    # Validate it
    truth_score, uncertainty, accept = validator.validate(external_input)

    if accept:
        # Update knowledge base
        validator.add_to_knowledge_base(external_input)

        # Feed to dialogue engine
        return external_input.embedding
    else:
        # Reject unreliable input
        return None

# Run dialogue with validated inputs
emissions = dialogue.converse(
    n_steps=1000,
    listener_callback=validated_listener
)
```

### Combined Benefits

1. **Dialogue engine**: Generates coherent responses through dynamical systems
2. **Data validator**: Ensures inputs to the system are truthful
3. **Result**: Coherent AND truthful dialogue

---

## Implementation Details

### Computational Complexity

| Component | Complexity |
|-----------|------------|
| Source credibility (ρₛ) | O(1) |
| Internal consistency (κᵢ) | O(N_claims) |
| Cross-reference (ξᵣ) | O(N_refs · d) |
| Temporal coherence (τₜ) | O(T · d) |
| Semantic alignment (σₐ) | O(d) |
| Evidence strength (εₑ) | O(N_evidence) |
| **Total per validation** | **O(d · max(N_refs, T))** |

Where:
- **d**: Embedding dimension (e.g., 128, 256)
- **N_refs**: Number of cross-references
- **T**: Temporal window size
- **N_evidence**: Number of evidence pieces

For typical values (d=128, N_refs=5, T=10), this is very fast: **~10-100μs per validation**.

### Memory Requirements

- **Knowledge base**: O(d) – single embedding vector
- **Cross-reference DB**: O(N_sources · d) – grows with number of reference sources
- **Validation history**: O(N_validations · d) – can be pruned periodically

---

## Limitations and Future Work

### Current Limitations

1. **Embedding quality**: Semantic measures (σₐ, ξᵣ) depend on quality of embeddings
2. **Knowledge base**: Requires curated knowledge base for semantic alignment
3. **Contradiction detection**: Internal consistency relies on automated logical analysis
4. **Gaming**: Sophisticated adversaries could optimize for high scores while lying

### Future Enhancements

1. **Learned weights**: Train wᵢ on labeled truth/false dataset
2. **Neural components**: Use transformer models for contradiction detection
3. **Active learning**: Request clarification when U(x) is high
4. **Adversarial robustness**: Add penalties for adversarial patterns
5. **Causal reasoning**: Incorporate causal inference beyond correlation
6. **Bayesian updating**: Update priors as new evidence arrives

---

## Conclusion

This mathematical framework provides a **principled, interpretable, and robust** method for evaluating external information sources.

### Key Advantages

✓ **Multi-dimensional**: Catches failures across 6 independent axes
✓ **Interpretable**: Each component has clear semantic meaning
✓ **Adaptive**: Weights adjust to context
✓ **Uncertainty-aware**: Quantifies confidence, not just point estimates
✓ **Integrable**: Works with existing ML models and dialogue systems

### Core Insight

**Truth is not a single measure but emerges from coherence across multiple independent dimensions.**

Just as meaning emerges in the recursive dialogue engine through phase alignment and entropy minimization, **truth emerges through multi-dimensional coherence convergence**.

---

## References and Further Reading

### Related Concepts

- **Bayesian epistemology**: Updating beliefs based on evidence
- **Information coherence theory**: Truth as maximally coherent belief system
- **Source credibility models**: CREDBANK, PHEME datasets
- **Fact-checking systems**: ClaimBuster, FactCheck, Snopes
- **Multi-source validation**: Cross-document coreferencing

### Connections to Dialogue Engine

- **Recursive entropy** (S_R) ↔ **Uncertainty** (U)
- **Phase coherence** (μₛ ↔ μₗ) ↔ **Semantic alignment** (σₐ)
- **Mutual identity** (LoMI) ↔ **Cross-reference validation** (ξᵣ)
- **Emission criterion** (dS_R/dt ≈ 0) ↔ **Decision criterion** (T > θ)

The same principles that govern coherent dialogue govern truthful information validation.
