# Recursive Self-Improvement System - Usage Guide

## Quick Start

### Running the Complete System

```python
from phase6_recursive_improvement import RecursiveSelfImprover

# Create the self-improvement system
improver = RecursiveSelfImprover()

# Run recursive improvement
result = improver.recursive_improve(
    max_iterations=10,      # Maximum improvement cycles
    min_improvement=0.01    # Convergence threshold (1%)
)

# Check results
print(f"Converged: {result['convergence_proof'].converged}")
print(f"Final accuracy: {result['final_accuracy']:.1%}")
print(f"Total improvement: {result['convergence_proof'].total_improvement:+.1%}")
```

## Phase-by-Phase Usage

### Phase 1: Generate Functions with Control Flow

```python
from phase1_control_flow import ControlFlowAttractor
from provable_codegen import CodeSpec

# Define what you want
spec = CodeSpec(
    name="factorial",
    signature="def factorial(n: int) -> int",
    description="Calculate factorial of n",
    examples=[(0, 1), (5, 120), (3, 6)]
)

# Generate with termination proof
attractor = ControlFlowAttractor(n_dims=256)
result = attractor.generate_with_control_flow(spec)

if result['verified']:
    print(result['code'])  # The generated function
    print(f"Provably halts in {result['proof'].max_iterations} iterations")
```

### Phase 2: Build Complex Functions from Simple Ones

```python
from phase2_composition import HierarchicalSynthesizer

# Define a complex function
spec = CodeSpec(
    name="sum_of_squares",
    signature="def sum_of_squares(a: int, b: int) -> int",
    description="Return a² + b²",
    examples=[(3, 4, 25), (1, 2, 5)]
)

# Synthesize from components
synthesizer = HierarchicalSynthesizer()
result = synthesizer.synthesize(spec)

if result['verified']:
    print(result['code'])
    print(f"Built from {len(result['proof'].components_used)} components")
    print(f"Components: {result['proof'].components_used}")
```

### Phase 3: Generate Code Generators

```python
from phase3_meta_programming import MetaProgrammingSystem

# Define a generator function
spec = CodeSpec(
    name="make_multiplier",
    signature="def make_multiplier(factor: int)",
    description="Return a function that multiplies by factor",
    examples=[],
    generator=True
)

# Generate the generator
meta_system = MetaProgrammingSystem()
result = meta_system.generate_generator(spec)

if result['verified']:
    # Execute the generated code
    namespace = {}
    exec(result['code'], namespace)
    make_multiplier = namespace['make_multiplier']

    # Use the generated generator
    times_3 = make_multiplier(3)
    times_5 = make_multiplier(5)

    print(times_3(10))  # 30
    print(times_5(10))  # 50
```

### Phase 4: Analyze System Performance

```python
from phase4_self_analysis import SelfAnalysisSystem

# Analyze the system
analyzer = SelfAnalysisSystem()
analysis = analyzer.analyze()

# View metrics
for component, metrics in analysis['component_metrics'].items():
    print(f"{component}: {metrics.accuracy:.1%} accuracy")

# View bottlenecks
for bottleneck in analysis['bottlenecks']:
    print(f"Bottleneck: {bottleneck.component_name}")
    print(f"  Current: {bottleneck.current_performance:.1%}")
    print(f"  Target: {bottleneck.target_performance:.1%}")
    print(f"  Improvement potential: {bottleneck.gap:.1%}")

# Get improvement specification
improvement_spec = analysis['improvement_spec']
print(f"\nSuggested improvements for {improvement_spec.component_name}:")
for approach in improvement_spec.suggested_approaches:
    print(f"  • {approach}")
```

### Phase 5: Self-Modify a Component

```python
from phase5_self_modification import SelfModificationSystem

# Run one cycle of self-improvement
system = SelfModificationSystem()
result = system.self_improve()

if result['improved']:
    print(f"Improved {result['component']}")
    print(f"Before: {result['old_accuracy']:.1%}")
    print(f"After: {result['new_accuracy']:.1%}")
    print(f"Gain: {result['improvement']:+.1%}")

    # Access the proof
    proof = result['proof']
    print(f"Verified: {proof.verified}")
    print(f"All tests pass: {proof.all_tests_pass}")
    print(f"No regressions: {proof.no_regressions}")
else:
    print("System is already optimal")
```

### Phase 6: Recursive Self-Improvement

```python
from phase6_recursive_improvement import RecursiveSelfImprover

# Create improver
improver = RecursiveSelfImprover()

# Run until convergence
result = improver.recursive_improve(
    max_iterations=10,
    min_improvement=0.01  # Stop if improvement < 1%
)

# Examine the improvement trajectory
for iteration in result['iterations']:
    print(f"Iteration {iteration.iteration}:")
    print(f"  Component: {iteration.component_improved}")
    print(f"  Accuracy: {iteration.old_accuracy:.1%} → {iteration.new_accuracy:.1%}")
    print(f"  Improvement: {iteration.improvement:+.1%}")

# Check convergence proof
proof = result['convergence_proof']
print(f"\nConvergence Proof:")
print(f"  Converged: {proof.converged}")
print(f"  Reason: {proof.convergence_criterion}")
print(f"  Tarski fixed-point: {proof.tarski_fixed_point}")
print(f"  Monotonic: {proof.monotonic}")
print(f"\n{proof.reasoning}")
```

## Integration with Existing Systems

### As a Code Generation Backend

```python
from phase2_composition import HierarchicalSynthesizer
from provable_codegen import CodeSpec

def generate_function(name, signature, description, examples):
    """
    Generate a provably correct function.

    Args:
        name: Function name
        signature: Type signature (e.g., "def foo(x: int) -> int")
        description: Natural language description
        examples: List of input/output pairs

    Returns:
        dict with 'code', 'verified', 'proof'
    """
    spec = CodeSpec(
        name=name,
        signature=signature,
        description=description,
        examples=examples
    )

    synthesizer = HierarchicalSynthesizer()
    return synthesizer.synthesize(spec)

# Example usage
result = generate_function(
    name="is_even",
    signature="def is_even(n: int) -> bool",
    description="Check if number is even",
    examples=[(0, True), (1, False), (4, True), (5, False)]
)

if result['verified']:
    exec(result['code'])
```

### As a Self-Improving Module

```python
class SelfImprovingAI:
    """AI system that improves itself over time"""

    def __init__(self):
        from phase6_recursive_improvement import RecursiveSelfImprover
        self.improver = RecursiveSelfImprover()
        self.version = 1.0

    def improve(self):
        """Run one improvement cycle"""
        result = self.improver.modification_system.self_improve()

        if result['improved']:
            self.version += 0.1
            return {
                'success': True,
                'component': result['component'],
                'improvement': result['improvement'],
                'new_version': self.version
            }
        else:
            return {
                'success': False,
                'reason': 'Already optimal'
            }

    def optimize_until_convergence(self):
        """Improve until no more improvements possible"""
        result = self.improver.recursive_improve()
        return result['convergence_proof']

# Usage
ai = SelfImprovingAI()
proof = ai.optimize_until_convergence()
print(f"Converged to version {ai.version}")
```

## API Reference

### Core Data Structures

#### CodeSpec
```python
@dataclass
class CodeSpec:
    name: str              # Function name
    signature: str         # Type signature
    description: str       # What it does
    examples: List[tuple]  # Input/output pairs
    generator: bool = False  # Is this a generator function?
```

#### ConvergenceProof
```python
@dataclass
class ConvergenceProof:
    converged: bool              # Did it converge?
    iterations: int              # Number of iterations
    initial_accuracy: float      # Starting performance
    final_accuracy: float        # Ending performance
    total_improvement: float     # Total gain
    convergence_criterion: str   # Why it converged
    tarski_fixed_point: bool     # Tarski's theorem applies?
    monotonic: bool              # Monotonically increasing?
    reasoning: str               # Full mathematical proof
```

#### ImprovementProof
```python
@dataclass
class ImprovementProof:
    verified: bool           # Is improvement proven?
    old_accuracy: float      # Before
    new_accuracy: float      # After
    improvement: float       # Gain
    all_tests_pass: bool     # No failures?
    no_regressions: bool     # Nothing broke?
    speed_maintained: bool   # Not slower?
    confidence: float        # Confidence level
    reasoning: str           # Why verified/not verified
```

## Mathematical Foundations

### Lyapunov Convergence
The semantic engine minimizes a Lyapunov function:
```
V(μ) = ||μ - μ_target||²
dV/dt ≤ 0  →  guaranteed convergence
```

### Tarski's Fixed-Point Theorem
Recursive improvement converges because:
1. **Monotonic**: version_{i+1} ≥ version_i
2. **Bounded**: accuracy ≤ 1.0 (perfect)
3. **Therefore**: Converges to fixed point (optimal version)

### Free Energy Minimization
Code generation minimizes variational free energy:
```
F = Accuracy + λ * Complexity
```
Balances correctness vs. simplicity.

## Common Patterns

### Pattern 1: Generate and Verify
```python
# Always check verification before using generated code
result = system.generate(spec)
if result['verified']:
    exec(result['code'])
else:
    print(f"Verification failed: {result['proof']}")
```

### Pattern 2: Iterative Improvement
```python
# Improve until convergence or max iterations
for i in range(max_iterations):
    result = system.self_improve()
    if not result['improved']:
        print(f"Converged after {i} iterations")
        break
```

### Pattern 3: Safe Hot-Swapping
```python
# Only apply improvements if proven safe
proof = verifier.verify_improvement(old_code, new_code, tests)
if proof.verified and proof.no_regressions:
    swapper.apply_improvement(component, new_code, proof)
```

## Troubleshooting

### Low Accuracy
If code generation accuracy is low:
1. Add more examples to the specification
2. Make description more precise
3. Check that examples are consistent
4. Use Phase 4 to identify specific bottlenecks

### Won't Converge
If recursive improvement doesn't converge:
1. Lower min_improvement threshold
2. Increase max_iterations
3. Check that test suite is comprehensive
4. Verify bottleneck detection is working

### Verification Failures
If proofs fail:
1. Check that examples are correct
2. Verify specification is unambiguous
3. Ensure test suite covers edge cases
4. Review generated code manually

## Performance Tips

1. **Start simple**: Use Phase 1 for basic functions before Phase 2
2. **Use caching**: SpecificationAttractor caches encodings
3. **Batch improvements**: Run Phase 6 overnight for complex systems
4. **Profile first**: Always run Phase 4 before Phase 5
5. **Comprehensive tests**: Better test suite = better self-improvement

## Next Steps

1. **Extend to classes**: Modify Phase 2 for object-oriented synthesis
2. **Learn from data**: Replace hand-coded patterns with learned embeddings
3. **Multi-file projects**: Extend Phase 5 to modify multiple files
4. **Distributed improvement**: Run Phase 6 across multiple machines
5. **Human-in-the-loop**: Add approval step before applying improvements

## License & Citation

If you use this system in your research, please cite:

```
Recursive Self-Improvement with Formal Verification
A complete implementation demonstrating provably convergent
self-modification using Tarski's fixed-point theorem.
```

## Support

For issues, questions, or contributions:
- See PROGRESS_TO_SELF_IMPROVEMENT.md for detailed technical documentation
- Review phase*.py source files for implementation details
- Each phase has a `demonstrate_*()` function showing usage
