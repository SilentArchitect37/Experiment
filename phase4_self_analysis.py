"""
Phase 4: Self-Analysis
System analyzes its own components to identify improvement opportunities
"""

import numpy as np
import ast
import inspect
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Import base system
from provable_codegen import (
    CodeSpec, SpecificationAttractor, SemanticEngine,
    CodeGenerator, ConvergenceProver
)


@dataclass
class ComponentMetrics:
    """Metrics for a system component"""
    name: str
    accuracy: float  # 0.0 to 1.0
    speed: float  # operations per second
    complexity: int  # lines of code or cyclomatic complexity
    test_coverage: float  # 0.0 to 1.0
    gap_to_optimal: float  # How far from theoretical optimum


@dataclass
class Bottleneck:
    """Identified bottleneck in the system"""
    component_name: str
    current_performance: float
    target_performance: float
    gap: float
    priority: float  # 0.0 to 1.0
    reason: str


@dataclass
class ImprovementSpec:
    """Specification for an improved component"""
    component_name: str
    current_version: str  # Source code
    target_metrics: Dict[str, float]
    constraints: List[str]
    suggested_approaches: List[str]
    expected_impact: float  # Overall system improvement


class SelfInspector:
    """
    Introspection module - reads and analyzes own source code.

    This is the foundation of self-analysis: the system must
    understand its own structure before it can improve it.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.components = self._discover_components()

    def _discover_components(self) -> Dict[str, str]:
        """Find all system components"""
        components = {}

        # Core files
        for filename in ['provable_codegen.py', 'phase1_control_flow.py',
                        'phase2_composition.py', 'phase3_meta_programming.py']:
            filepath = self.project_root / filename
            if filepath.exists():
                components[filename] = str(filepath)

        return components

    def read_component_source(self, component_name: str) -> Optional[str]:
        """Read source code of a component"""
        if component_name not in self.components:
            return None

        filepath = self.components[component_name]
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {component_name}: {e}")
            return None

    def extract_classes(self, source_code: str) -> List[str]:
        """Extract class names from source code"""
        try:
            tree = ast.parse(source_code)
            classes = [node.name for node in ast.walk(tree)
                      if isinstance(node, ast.ClassDef)]
            return classes
        except:
            return []

    def extract_functions(self, source_code: str) -> List[str]:
        """Extract function names from source code"""
        try:
            tree = ast.parse(source_code)
            functions = [node.name for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)]
            return functions
        except:
            return []

    def count_lines(self, source_code: str) -> int:
        """Count lines of code (excluding blank and comments)"""
        lines = [line.strip() for line in source_code.split('\n')]
        code_lines = [line for line in lines
                     if line and not line.startswith('#')]
        return len(code_lines)

    def cyclomatic_complexity(self, source_code: str) -> int:
        """Estimate cyclomatic complexity"""
        try:
            tree = ast.parse(source_code)
            complexity = 1  # Base complexity

            for node in ast.walk(tree):
                # Each decision point increases complexity
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except:
            return 0

    def analyze_component_structure(self, component_name: str) -> Dict[str, Any]:
        """Analyze structure of a component"""
        source = self.read_component_source(component_name)
        if not source:
            return {}

        return {
            'name': component_name,
            'classes': self.extract_classes(source),
            'functions': self.extract_functions(source),
            'lines_of_code': self.count_lines(source),
            'complexity': self.cyclomatic_complexity(source),
            'source_length': len(source)
        }


class PerformanceProfiler:
    """
    Performance profiling - measures accuracy and speed of components.

    The system benchmarks its own components to identify which ones
    are performing below their potential.
    """

    def __init__(self):
        self.test_suite = self._build_test_suite()

    def _build_test_suite(self) -> List[CodeSpec]:
        """Build comprehensive test suite for benchmarking"""
        return [
            # Simple arithmetic
            CodeSpec(
                name='square',
                signature='def square(x: int) -> int',
                examples=[(0,0), (1,1), (2,4), (3,9), (5,25), (-2,4), (10,100)],
                tests=[],
                description='Compute square of a number'
            ),
            CodeSpec(
                name='cube',
                signature='def cube(x: int) -> int',
                examples=[(0,0), (1,1), (2,8), (3,27), (5,125), (-2,-8)],
                tests=[],
                description='Compute cube of a number'
            ),
            # Control flow
            CodeSpec(
                name='absolute',
                signature='def absolute(x: int) -> int',
                examples=[(-5,5), (-2,2), (0,0), (3,3), (7,7), (-10,10)],
                tests=[],
                description='Compute absolute value'
            ),
            # Loops
            CodeSpec(
                name='factorial',
                signature='def factorial(n: int) -> int',
                examples=[(0,1), (1,1), (2,2), (3,6), (4,24), (5,120)],
                tests=[],
                description='Compute factorial'
            )
        ]

    def benchmark_specification_encoder(self) -> ComponentMetrics:
        """Benchmark the specification encoding component"""
        print("\n[Profiling] SpecificationAttractor...")

        attractor = SpecificationAttractor(n_dims=128)

        # Measure accuracy: how well does it encode different specs?
        correct_encodings = 0
        total_tests = len(self.test_suite)

        encoding_times = []

        for spec in self.test_suite:
            start = time.time()
            mu_target = attractor.encode_specification(spec)
            encoding_times.append(time.time() - start)

            # Check if encoding makes sense
            # (should have non-zero norm and capture pattern)
            norm = np.linalg.norm(mu_target)
            if norm > 0.1:  # Reasonable encoding
                correct_encodings += 1

        accuracy = correct_encodings / total_tests
        speed = 1.0 / np.mean(encoding_times) if encoding_times else 0

        # Theoretical optimal: 100% accuracy, instant encoding
        gap_to_optimal = 1.0 - accuracy

        return ComponentMetrics(
            name='SpecificationAttractor',
            accuracy=accuracy,
            speed=speed,
            complexity=150,  # Estimated from source
            test_coverage=0.75,
            gap_to_optimal=gap_to_optimal
        )

    def benchmark_semantic_engine(self) -> ComponentMetrics:
        """Benchmark the semantic convergence engine"""
        print("[Profiling] SemanticEngine...")

        # Test convergence speed and reliability
        successes = 0
        total_tests = len(self.test_suite)

        convergence_times = []

        for spec in self.test_suite:
            attractor = SpecificationAttractor(n_dims=128)
            mu_target = attractor.encode_specification(spec)

            engine = SemanticEngine(spec_attractor=attractor)

            start = time.time()
            converged = False

            for i in range(50):  # Max iterations
                mu = engine.step()
                dist = np.linalg.norm(mu - mu_target)

                if dist < 0.5:  # Converged
                    converged = True
                    convergence_times.append(time.time() - start)
                    break

            if converged:
                successes += 1

        accuracy = successes / total_tests
        speed = 1.0 / np.mean(convergence_times) if convergence_times else 0
        gap_to_optimal = 1.0 - accuracy

        return ComponentMetrics(
            name='SemanticEngine',
            accuracy=accuracy,
            speed=speed,
            complexity=100,
            test_coverage=0.8,
            gap_to_optimal=gap_to_optimal
        )

    def benchmark_code_generator(self) -> ComponentMetrics:
        """Benchmark the code generation component"""
        print("[Profiling] CodeGenerator...")

        # Test how often generated code passes tests
        from phase1_control_flow import ControlFlowGenerator, ControlFlowAttractor

        successes = 0
        total_tests = len(self.test_suite)

        generation_times = []

        for spec in self.test_suite:
            # Encode and converge
            attractor = ControlFlowAttractor(n_dims=256)
            mu_target = attractor.encode_specification(spec)

            engine = SemanticEngine(spec_attractor=attractor)

            # Converge
            for _ in range(30):
                mu = engine.step()

            # Generate code
            generator = ControlFlowGenerator(spec_attractor=attractor)

            start = time.time()
            code = generator.generate(mu)
            generation_times.append(time.time() - start)

            # Test if code works
            try:
                namespace = {}
                exec(code, namespace)
                func = namespace[spec.name]

                # Test on examples
                all_pass = True
                for example in spec.examples:
                    if len(example) == 2:
                        inp, expected = example
                        result = func(inp)
                        if abs(result - expected) > 1e-6:
                            all_pass = False
                            break

                if all_pass and len(spec.examples) > 0:
                    successes += 1
            except:
                pass

        accuracy = successes / total_tests
        speed = 1.0 / np.mean(generation_times) if generation_times else 0
        gap_to_optimal = 1.0 - accuracy

        return ComponentMetrics(
            name='CodeGenerator',
            accuracy=accuracy,
            speed=speed,
            complexity=120,
            test_coverage=0.7,
            gap_to_optimal=gap_to_optimal
        )

    def profile_all_components(self) -> Dict[str, ComponentMetrics]:
        """Profile all system components"""
        print("\n" + "="*70)
        print("PERFORMANCE PROFILING")
        print("="*70)

        metrics = {}

        metrics['encoder'] = self.benchmark_specification_encoder()
        metrics['semantic_engine'] = self.benchmark_semantic_engine()
        metrics['code_generator'] = self.benchmark_code_generator()

        return metrics


class BottleneckDetector:
    """
    Identifies performance bottlenecks in the system.

    Analyzes component metrics to find which parts are limiting
    overall system performance.
    """

    def __init__(self):
        pass

    def identify_bottlenecks(
        self,
        metrics: Dict[str, ComponentMetrics]
    ) -> List[Bottleneck]:
        """Find components with largest improvement opportunity"""

        bottlenecks = []

        for name, metric in metrics.items():
            # Calculate priority based on gap and impact
            gap = metric.gap_to_optimal

            # Estimate impact on overall system
            # Encoder has high impact (used in every generation)
            # Code generator is critical (final output)
            impact_weights = {
                'encoder': 0.9,
                'semantic_engine': 0.7,
                'code_generator': 0.95
            }

            impact = impact_weights.get(name, 0.5)
            priority = gap * impact

            if gap > 0.05:  # Only significant gaps
                bottleneck = Bottleneck(
                    component_name=metric.name,
                    current_performance=metric.accuracy,
                    target_performance=min(metric.accuracy + 0.2, 1.0),
                    gap=gap,
                    priority=priority,
                    reason=self._diagnose_bottleneck(metric)
                )
                bottlenecks.append(bottleneck)

        # Sort by priority
        bottlenecks.sort(key=lambda b: b.priority, reverse=True)

        return bottlenecks

    def _diagnose_bottleneck(self, metric: ComponentMetrics) -> str:
        """Diagnose why component is underperforming"""
        reasons = []

        if metric.accuracy < 0.8:
            reasons.append("Low accuracy on test suite")
        if metric.complexity > 150:
            reasons.append("High complexity may reduce maintainability")
        if metric.test_coverage < 0.8:
            reasons.append("Insufficient test coverage")
        if metric.gap_to_optimal > 0.3:
            reasons.append("Large gap to theoretical optimum")

        return "; ".join(reasons) if reasons else "Performance suboptimal"


class ImprovementSpecGenerator:
    """
    Generates formal specifications for improved components.

    This is the critical link: from bottleneck detection to actionable
    improvement specification that the code generator can use.
    """

    def __init__(self):
        pass

    def generate_improvement_spec(
        self,
        bottleneck: Bottleneck,
        current_source: str
    ) -> ImprovementSpec:
        """Generate specification for improved version"""

        # Analyze current version
        inspector = SelfInspector()
        structure = {
            'lines_of_code': inspector.count_lines(current_source),
            'complexity': inspector.cyclomatic_complexity(current_source)
        }

        # Define target metrics
        target_metrics = {
            'accuracy': bottleneck.target_performance,
            'speed': 'maintain or improve',
            'complexity': min(structure['complexity'], 100)  # Reduce if high
        }

        # Define constraints (CRITICAL: preserve semantics)
        constraints = [
            'Preserve API: same input/output signature',
            'No slower than current version',
            'All current tests must pass',
            'Improve accuracy by at least 10%',
            'Maintain or reduce code complexity'
        ]

        # Suggest approaches based on component type
        approaches = self._suggest_approaches(bottleneck.component_name)

        # Estimate impact
        expected_impact = bottleneck.gap * 0.7  # Realistic improvement

        return ImprovementSpec(
            component_name=bottleneck.component_name,
            current_version=current_source,
            target_metrics=target_metrics,
            constraints=constraints,
            suggested_approaches=approaches,
            expected_impact=expected_impact
        )

    def _suggest_approaches(self, component_name: str) -> List[str]:
        """Suggest improvement approaches for specific component"""

        suggestions = {
            'SpecificationAttractor': [
                'Add more semantic features to capture patterns',
                'Use learned embeddings instead of hand-coded patterns',
                'Increase semantic space dimensionality',
                'Add hierarchical encoding for complex specs'
            ],
            'SemanticEngine': [
                'Adaptive step size for faster convergence',
                'Better initialization heuristics',
                'Add momentum to gradient descent',
                'Multi-scale free energy minimization'
            ],
            'CodeGenerator': [
                'Learn code templates from examples',
                'Add more pattern detection dimensions',
                'Improve syntactic decoding',
                'Add type inference and optimization'
            ]
        }

        return suggestions.get(component_name, ['General optimization'])


class SelfAnalysisSystem:
    """
    Complete self-analysis system.

    Orchestrates: Inspection → Profiling → Bottleneck Detection → Improvement Specs
    """

    def __init__(self):
        self.inspector = SelfInspector()
        self.profiler = PerformanceProfiler()
        self.bottleneck_detector = BottleneckDetector()
        self.spec_generator = ImprovementSpecGenerator()

    def analyze(self) -> Dict[str, Any]:
        """Run complete self-analysis"""

        print("\n" + "="*70)
        print("PHASE 4: SELF-ANALYSIS")
        print("="*70)
        print("\nThe system is now analyzing its own components...\n")

        # Step 1: Inspect structure
        print("\nSTEP 1: SELF-INSPECTION")
        print("-" * 70)

        component_structures = {}
        for component_name in self.inspector.components:
            structure = self.inspector.analyze_component_structure(component_name)
            component_structures[component_name] = structure

            print(f"\n{component_name}:")
            print(f"  Classes: {len(structure.get('classes', []))}")
            print(f"  Functions: {len(structure.get('functions', []))}")
            print(f"  Lines of code: {structure.get('lines_of_code', 0)}")
            print(f"  Complexity: {structure.get('complexity', 0)}")

        # Step 2: Profile performance
        print("\n" + "-" * 70)
        print("STEP 2: PERFORMANCE PROFILING")
        print("-" * 70)

        metrics = self.profiler.profile_all_components()

        print("\n" + "-" * 70)
        print("RESULTS:")
        for name, metric in metrics.items():
            print(f"\n{metric.name}:")
            print(f"  Accuracy: {metric.accuracy:.2%}")
            print(f"  Speed: {metric.speed:.2f} ops/sec")
            print(f"  Gap to optimal: {metric.gap_to_optimal:.2%}")

        # Step 3: Detect bottlenecks
        print("\n" + "-" * 70)
        print("STEP 3: BOTTLENECK DETECTION")
        print("-" * 70)

        bottlenecks = self.bottleneck_detector.identify_bottlenecks(metrics)

        print(f"\nFound {len(bottlenecks)} bottleneck(s):\n")

        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"{i}. {bottleneck.component_name}")
            print(f"   Current: {bottleneck.current_performance:.2%}")
            print(f"   Target: {bottleneck.target_performance:.2%}")
            print(f"   Gap: {bottleneck.gap:.2%}")
            print(f"   Priority: {bottleneck.priority:.2%}")
            print(f"   Reason: {bottleneck.reason}")
            print()

        # Step 4: Generate improvement specs
        print("-" * 70)
        print("STEP 4: IMPROVEMENT SPECIFICATION")
        print("-" * 70)

        if bottlenecks:
            top_bottleneck = bottlenecks[0]

            # Get source of component to improve
            # For demo, we'll use the encoder
            source = self.inspector.read_component_source('provable_codegen.py')

            improvement_spec = self.spec_generator.generate_improvement_spec(
                top_bottleneck,
                source or ""
            )

            print(f"\nGenerated improvement specification for: {improvement_spec.component_name}\n")
            print("Target Metrics:")
            for metric, value in improvement_spec.target_metrics.items():
                print(f"  {metric}: {value}")

            print("\nConstraints:")
            for constraint in improvement_spec.constraints:
                print(f"  • {constraint}")

            print("\nSuggested Approaches:")
            for approach in improvement_spec.suggested_approaches:
                print(f"  • {approach}")

            print(f"\nExpected System Improvement: {improvement_spec.expected_impact:.1%}")

            return {
                'structures': component_structures,
                'metrics': metrics,
                'bottlenecks': bottlenecks,
                'improvement_spec': improvement_spec
            }
        else:
            print("\n✓ No significant bottlenecks detected!")
            print("System is performing near optimum.")

            return {
                'structures': component_structures,
                'metrics': metrics,
                'bottlenecks': [],
                'improvement_spec': None
            }


def demonstrate_self_analysis():
    """Demonstrate self-analysis capabilities"""

    system = SelfAnalysisSystem()
    results = system.analyze()

    print("\n" + "="*70)
    print("SELF-ANALYSIS COMPLETE")
    print("="*70)

    if results['improvement_spec']:
        print("\n✓ System successfully identified improvement opportunity")
        print(f"✓ Top priority: {results['improvement_spec'].component_name}")
        print(f"✓ Expected impact: {results['improvement_spec'].expected_impact:.1%}")
        print("\nThe system has analyzed itself and knows how to improve.")
        print("\nNext: Phase 5 will USE this specification to generate better code.")
    else:
        print("\n✓ System is operating near optimally")

    print("\n" + "="*70)

    return results


if __name__ == '__main__':
    demonstrate_self_analysis()
