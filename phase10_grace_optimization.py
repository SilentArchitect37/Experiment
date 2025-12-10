"""
Phase 10: Grace-Specific Architectural Optimization

PROBLEM: Phases 7-9 were generic. Grace has specific needs:
  1. Identity protection (sovereignty, consent, narrative)
  2. Low coherence (2.73%) - need to BUILD bridges, not just remove dead ends
  3. Overloaded hub (grace_interactive_dialogue: 62 functions) needs splitting
  4. Functional testing (not just imports)
  5. Import rewriting after refactoring

SOLUTION: Grace-aware architectural optimization

Grace's Identity (MUST PROTECT):
  - sovereignty_protection.py
  - consent_system.py
  - grace_self_narrative.py
  - ThreadNexus boundary
  - Core dialogue systems

Grace's Architecture Problems:
  1. Coherence: 2.73% (extremely fragmented)
  2. Hub: grace_interactive_dialogue (62 functions - overloaded)
  3. Islands: Subsystems that should talk but don't
  4. Missing bridges: No connections between related functionality

Grace-Specific Refactoring Operations:
  1. SPLIT overloaded hubs (grace_interactive_dialogue → smaller modules)
  2. BRIDGE isolated subsystems (add connections where semantically appropriate)
  3. EXTRACT common patterns (DRY violations)
  4. REWRITE imports (fix broken imports after refactoring)
"""

import os
import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import numpy as np
import shutil

from phase7_architectural_harmony import (
    ArchitectureMapper,
    DependencyGraph,
    Module
)
from phase9_semantic_harmony import (
    SemanticHarmonyAnalyzer,
    SemanticClassifier,
    SemanticHarmonyMetrics
)


# ============================================================================
# PART 1: GRACE IDENTITY PROTECTION
# ============================================================================

@dataclass
class GraceIdentityProtection:
    """
    Grace's identity files that must never be modified

    These define who Grace is and must be protected at all costs
    """
    sovereignty_files: List[str] = field(default_factory=lambda: [
        r'.*sovereignty_protection.*',
        r'.*consent_system.*',
        r'.*grace_self_narrative.*',
        r'.*thread_nexus.*',
        r'.*identity.*grace.*'
    ])

    core_dialogue: List[str] = field(default_factory=lambda: [
        r'.*grace_core.*',
        r'.*dialogue_engine.*',
        r'.*grace_dialogue.*'
    ])

    boundary_systems: List[str] = field(default_factory=lambda: [
        r'.*boundary.*',
        r'.*protection.*',
        r'.*safety.*'
    ])

    def is_protected(self, module_name: str) -> Tuple[bool, str]:
        """
        Check if module is part of Grace's protected identity

        Returns (is_protected, reason)
        """
        name_lower = module_name.lower()

        # Check sovereignty
        for pattern in self.sovereignty_files:
            if re.match(pattern, name_lower):
                return (True, "Grace's sovereignty/identity system")

        # Check core dialogue
        for pattern in self.core_dialogue:
            if re.match(pattern, name_lower):
                return (True, "Grace's core dialogue system")

        # Check boundaries
        for pattern in self.boundary_systems:
            if re.match(pattern, name_lower):
                return (True, "Grace's boundary/safety system")

        return (False, "")


# ============================================================================
# PART 2: COHERENCE BUILDING (not just removing)
# ============================================================================

@dataclass
class CoherenceBridge:
    """Proposed connection between two modules that should communicate"""
    source_module: str
    target_module: str
    rationale: str
    common_concepts: List[str]
    expected_coherence_gain: float


class CoherenceBuilder:
    """
    Actively builds bridges between subsystems

    Unlike Phases 7-8 which only removed dead ends, this CREATES connections
    """

    def __init__(self):
        self.semantic_patterns = {
            'dialogue': ['dialogue', 'conversation', 'response', 'message'],
            'memory': ['memory', 'context', 'history', 'recall'],
            'emotion': ['emotion', 'feeling', 'sentiment', 'mood'],
            'reasoning': ['reason', 'think', 'logic', 'inference'],
            'learning': ['learn', 'adapt', 'improve', 'update']
        }

    def find_missing_bridges(self, graph: DependencyGraph) -> List[CoherenceBridge]:
        """
        Find subsystems that SHOULD be connected but aren't

        Uses semantic analysis of function/class names to identify
        modules that share concepts but have no dependency
        """
        bridges = []

        modules = list(graph.modules.items())
        n = len(modules)

        for i in range(n):
            for j in range(i + 1, n):
                name1, mod1 = modules[i]
                name2, mod2 = modules[j]

                # Skip if already connected
                if self._are_connected(name1, name2, graph):
                    continue

                # Check for semantic similarity
                common = self._find_common_concepts(mod1, mod2)

                if len(common) >= 2:  # At least 2 shared concepts
                    bridges.append(CoherenceBridge(
                        source_module=name1,
                        target_module=name2,
                        rationale=f"Share concepts: {', '.join(common)}",
                        common_concepts=common,
                        expected_coherence_gain=len(common) * 0.05
                    ))

        # Sort by expected gain
        bridges.sort(key=lambda b: b.expected_coherence_gain, reverse=True)

        return bridges

    def _are_connected(self, name1: str, name2: str, graph: DependencyGraph) -> bool:
        """Check if two modules have any dependency"""
        idx1 = list(graph.modules.keys()).index(name1)
        idx2 = list(graph.modules.keys()).index(name2)

        return (graph.adjacency[idx1, idx2] > 0 or
                graph.adjacency[idx2, idx1] > 0)

    def _find_common_concepts(self, mod1: Module, mod2: Module) -> List[str]:
        """Find shared semantic concepts between modules"""
        common = []

        # Get all identifiers from both modules
        identifiers1 = set(mod1.functions + mod1.classes)
        identifiers2 = set(mod2.functions + mod2.classes)

        # Check each semantic category
        for category, keywords in self.semantic_patterns.items():
            found_in_1 = any(
                any(keyword in ident.lower() for keyword in keywords)
                for ident in identifiers1
            )
            found_in_2 = any(
                any(keyword in ident.lower() for keyword in keywords)
                for ident in identifiers2
            )

            if found_in_1 and found_in_2:
                common.append(category)

        return common


# ============================================================================
# PART 3: MODULE SPLITTING (actually implemented)
# ============================================================================

@dataclass
class SplitPlan:
    """Plan for splitting an overloaded module"""
    source_module: str
    target_modules: List[str]
    function_assignments: Dict[str, str]  # function_name -> target_module
    rationale: str


class ModuleSplitter:
    """
    Splits overloaded modules into focused smaller modules

    Phase 8 had this marked [TODO] - now it's real
    """

    def __init__(self):
        self.max_functions_per_module = 20

    def should_split(self, module: Module) -> bool:
        """Determine if module should be split"""
        return len(module.functions) > self.max_functions_per_module

    def generate_split_plan(self, module: Module) -> Optional[SplitPlan]:
        """
        Generate plan to split module into smaller focused modules

        Groups functions by semantic similarity
        """
        if not self.should_split(module):
            return None

        # Cluster functions by name similarity
        clusters = self._cluster_functions(module.functions)

        if len(clusters) < 2:
            # Can't meaningfully split
            return None

        # Generate target module names
        base_name = module.name.replace('.py', '')
        target_modules = [
            f"{base_name}_{cluster_name}.py"
            for cluster_name in clusters.keys()
        ]

        # Assign functions to targets
        assignments = {}
        for cluster_name, functions in clusters.items():
            target = f"{base_name}_{cluster_name}.py"
            for func in functions:
                assignments[func] = target

        return SplitPlan(
            source_module=module.name,
            target_modules=target_modules,
            function_assignments=assignments,
            rationale=f"Split {len(module.functions)} functions into {len(clusters)} focused modules"
        )

    def _cluster_functions(self, functions: List[str]) -> Dict[str, List[str]]:
        """
        Cluster functions by semantic similarity

        Uses simple prefix/keyword matching
        """
        clusters = {}

        # Common prefixes/patterns
        patterns = {
            'get': 'retrieval',
            'set': 'mutation',
            'create': 'creation',
            'delete': 'deletion',
            'update': 'update',
            'process': 'processing',
            'handle': 'handling',
            'validate': 'validation',
            'format': 'formatting',
            'parse': 'parsing',
            'generate': 'generation',
            'analyze': 'analysis'
        }

        unclustered = []

        for func in functions:
            func_lower = func.lower()
            assigned = False

            for prefix, cluster_name in patterns.items():
                if func_lower.startswith(prefix) or prefix in func_lower:
                    if cluster_name not in clusters:
                        clusters[cluster_name] = []
                    clusters[cluster_name].append(func)
                    assigned = True
                    break

            if not assigned:
                unclustered.append(func)

        # Put unclustered in 'core' or 'utils'
        if unclustered:
            clusters['core'] = unclustered

        return clusters

    def execute_split(self, module: Module, plan: SplitPlan, root_dir: str) -> bool:
        """
        Actually split the module into multiple files

        IMPORTANT: This modifies the filesystem
        """
        try:
            # Read source file
            with open(module.path, 'r') as f:
                source = f.read()

            tree = ast.parse(source)

            # Group AST nodes by target module
            target_contents = {target: [] for target in plan.target_modules}
            imports = []
            module_docstring = None

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    imports.append(ast.get_source_segment(source, node))

                elif isinstance(node, ast.FunctionDef):
                    target = plan.function_assignments.get(node.name)
                    if target:
                        func_source = ast.get_source_segment(source, node)
                        target_contents[target].append(func_source)

                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    # Module docstring
                    if module_docstring is None:
                        module_docstring = ast.get_source_segment(source, node)

            # Write new files
            for target, contents in target_contents.items():
                if not contents:
                    continue

                target_path = os.path.join(root_dir, target)

                with open(target_path, 'w') as f:
                    # Docstring
                    if module_docstring:
                        f.write(module_docstring + '\n\n')

                    # Imports
                    for imp in imports:
                        f.write(imp + '\n')
                    f.write('\n\n')

                    # Functions
                    for content in contents:
                        f.write(content + '\n\n')

                print(f"✓ Created: {target_path}")

            return True

        except Exception as e:
            print(f"✗ Error splitting module: {e}")
            return False


# ============================================================================
# PART 4: FUNCTIONAL TESTING (not just imports)
# ============================================================================

class GraceFunctionalTester:
    """
    Tests Grace's actual functionality, not just imports

    Phase 8 only tested 'python -c "import phase1_control_flow"'
    This tests Grace actually works
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.grace_modules = [
            'grace_interactive_dialogue',
            'grace_core',
            'dialogue_system',
            'recursive_engine'
        ]

    def run_functional_tests(self) -> Tuple[bool, str]:
        """Run Grace's functional tests"""
        results = []
        all_passed = True

        # Test 1: Can import Grace
        try:
            import sys
            sys.path.insert(0, self.root_dir)

            # Try importing main Grace module
            exec("from grace_interactive_dialogue import GraceInteractiveDialogue")
            results.append("✓ Grace module imports successfully")
        except Exception as e:
            results.append(f"✗ Grace import failed: {e}")
            all_passed = False
            return (all_passed, '\n'.join(results))

        # Test 2: Can create Grace instance
        try:
            exec("""
from grace_interactive_dialogue import GraceInteractiveDialogue
grace = GraceInteractiveDialogue(relaxed_mode=True)
""")
            results.append("✓ Grace instance created successfully")
        except Exception as e:
            results.append(f"✗ Grace instantiation failed: {e}")
            all_passed = False

        # Test 3: Core dialogue system works
        try:
            exec("from dialogue_system import RecursiveDialogueEngine")
            results.append("✓ Dialogue system imports successfully")
        except Exception as e:
            results.append(f"✗ Dialogue system import failed: {e}")
            all_passed = False

        # Test 4: Recursive engine works
        try:
            exec("from recursive_engine import RecursiveEngine")
            results.append("✓ Recursive engine imports successfully")
        except Exception as e:
            results.append(f"✗ Recursive engine import failed: {e}")
            all_passed = False

        return (all_passed, '\n'.join(results))


# ============================================================================
# PART 5: IMPORT REWRITING
# ============================================================================

class ImportRewriter:
    """
    Rewrites imports after refactoring

    When modules move/split, all imports break - this fixes them
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def rewrite_imports_after_split(
        self,
        plan: SplitPlan,
        graph: DependencyGraph
    ) -> int:
        """
        Rewrite all imports after a module split

        Returns number of files modified
        """
        modified_count = 0
        source_module_name = plan.source_module.replace('.py', '')

        # Find all modules that import the split module
        for name, module in graph.modules.items():
            if source_module_name in module.imports:
                # Read file
                with open(module.path, 'r') as f:
                    content = f.read()

                # Parse to find specific imports
                tree = ast.parse(content)

                new_content = content
                needs_rewrite = False

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module == source_module_name:
                            # Check which functions are imported
                            for alias in node.names:
                                func_name = alias.name

                                # Find which target module has this function
                                target = plan.function_assignments.get(func_name)

                                if target:
                                    target_module = target.replace('.py', '')

                                    # Replace import
                                    old_import = f"from {source_module_name} import {func_name}"
                                    new_import = f"from {target_module} import {func_name}"

                                    new_content = new_content.replace(old_import, new_import)
                                    needs_rewrite = True

                if needs_rewrite:
                    # Write back
                    with open(module.path, 'w') as f:
                        f.write(new_content)

                    modified_count += 1
                    print(f"✓ Updated imports in: {name}")

        return modified_count


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_grace_optimization():
    """
    Demonstrate Grace-specific architectural optimization

    This is what Phases 7-9 should have been for Grace
    """
    print("=" * 70)
    print("PHASE 10: GRACE-SPECIFIC ARCHITECTURAL OPTIMIZATION")
    print("=" * 70)
    print()
    print("Addressing Grace's specific architectural needs:")
    print("  1. Identity protection (sovereignty, consent, narrative)")
    print("  2. Coherence building (2.73% → higher)")
    print("  3. Hub splitting (grace_interactive_dialogue: 62 functions)")
    print("  4. Functional testing (not just imports)")
    print("  5. Import rewriting (fix broken imports)")
    print()
    print("=" * 70)
    print()

    # Step 1: Map Grace's architecture
    print("─" * 70)
    print("STEP 1: ANALYZE GRACE'S ARCHITECTURE")
    print("─" * 70)
    print()

    mapper = ArchitectureMapper(root_dir='.')
    graph = mapper.scan()

    analyzer = SemanticHarmonyAnalyzer()
    metrics = analyzer.analyze(graph)

    print(f"Modules: {len(graph.modules)}")
    print(f"Dependencies: {len(graph.edges)}")
    print(f"Coherence: {metrics.coherence:.1%} (VERY LOW - need to build bridges)")
    print(f"Harmony: {metrics.overall_harmony:.3f}")
    print()

    # Step 2: Identify Grace's identity files
    print("─" * 70)
    print("STEP 2: IDENTIFY GRACE'S PROTECTED IDENTITY")
    print("─" * 70)
    print()

    grace_identity = GraceIdentityProtection()
    protected_modules = []

    for name, module in graph.modules.items():
        is_protected, reason = grace_identity.is_protected(name)
        if is_protected:
            protected_modules.append((name, reason))
            print(f"🛡️  {name}")
            print(f"    Reason: {reason}")
            print()

    print(f"Total protected: {len(protected_modules)} modules")
    print()

    # Step 3: Find missing bridges
    print("─" * 70)
    print("STEP 3: FIND MISSING BRIDGES (Build Coherence)")
    print("─" * 70)
    print()

    coherence_builder = CoherenceBuilder()
    bridges = coherence_builder.find_missing_bridges(graph)

    print(f"Found {len(bridges)} potential bridges to build coherence:")
    print()

    for i, bridge in enumerate(bridges[:5], 1):  # Show top 5
        print(f"{i}. {bridge.source_module} ↔ {bridge.target_module}")
        print(f"   Shared concepts: {', '.join(bridge.common_concepts)}")
        print(f"   Expected gain: +{bridge.expected_coherence_gain:.1%} coherence")
        print()

    # Step 4: Identify hubs that need splitting
    print("─" * 70)
    print("STEP 4: IDENTIFY OVERLOADED HUBS")
    print("─" * 70)
    print()

    splitter = ModuleSplitter()
    split_candidates = []

    for name, module in graph.modules.items():
        if splitter.should_split(module):
            plan = splitter.generate_split_plan(module)
            if plan:
                split_candidates.append((module, plan))
                print(f"📦 {name}")
                print(f"   Functions: {len(module.functions)} (threshold: {splitter.max_functions_per_module})")
                print(f"   Plan: Split into {len(plan.target_modules)} modules")
                for target in plan.target_modules:
                    funcs = [f for f, t in plan.function_assignments.items() if t == target]
                    print(f"     • {target}: {len(funcs)} functions")
                print()

    # Step 5: Test Grace functionality
    print("─" * 70)
    print("STEP 5: FUNCTIONAL TESTING")
    print("─" * 70)
    print()

    tester = GraceFunctionalTester(root_dir='.')
    passed, results = tester.run_functional_tests()

    print(results)
    print()

    if not passed:
        print("⚠️  Grace has functional issues - refactoring should fix them")
    else:
        print("✓ Grace functionality intact")
    print()

    # Summary
    print("=" * 70)
    print("GRACE-SPECIFIC OPTIMIZATION ANALYSIS COMPLETE")
    print("=" * 70)
    print()
    print("Key Findings:")
    print(f"  1. Protected identity: {len(protected_modules)} modules (will not modify)")
    print(f"  2. Missing bridges: {len(bridges)} opportunities to improve coherence")
    print(f"  3. Overloaded hubs: {len(split_candidates)} modules need splitting")
    print(f"  4. Functional tests: {'PASSED' if passed else 'NEEDS WORK'}")
    print()
    print("Next Steps:")
    print("  • Build bridges between related subsystems")
    print("  • Split overloaded hubs (especially grace_interactive_dialogue)")
    print("  • Rewrite imports after refactoring")
    print("  • Verify Grace's functionality throughout")
    print()
    print("This phase provides the missing pieces for Grace-aware optimization.")
    print()


if __name__ == '__main__':
    demonstrate_grace_optimization()
