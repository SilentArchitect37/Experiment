"""
Phase 9: Semantic-Aware Architectural Harmony

LESSON LEARNED from Phase 8:
- Purely structural metrics miss semantic value
- Test files are valuable even with no incoming dependencies
- Entry points, documentation, and utilities have purpose

SOLUTION:
- Add semantic weighting to harmony metric
- Distinguish "valuable dead ends" from truly unused code
- Multi-objective optimization: Structure + Semantics

Mathematical Foundation:
=======================

ENHANCED HARMONY METRIC:
  H_semantic = α·Coherence - β·Coupling + γ·Coverage - δ·Redundancy + ε·Value

Where Value considers:
  • Test coverage (test files provide QA value)
  • Documentation (docs provide understanding)
  • Entry points (main/scripts provide accessibility)
  • Utility modules (tools/helpers provide leverage)

SEMANTIC WEIGHTING:
  weight(module) = base_weight × semantic_multiplier

  semantic_multiplier = {
    2.0  if module is test suite
    1.5  if module is documentation
    1.3  if module is entry point (__main__)
    1.2  if module is utility/helper
    1.0  otherwise (default)
  }

This prevents the system from deleting valuable code
that happens to have no incoming dependencies.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

from phase7_architectural_harmony import (
    ArchitectureMapper,
    HarmonyAnalyzer,
    DependencyGraph,
    HarmonyMetrics,
    Module
)


# ============================================================================
# SEMANTIC MODULE CLASSIFIER
# ============================================================================

@dataclass
class SemanticClassification:
    """Semantic classification of a module"""
    module_name: str
    is_test: bool = False
    is_documentation: bool = False
    is_entry_point: bool = False
    is_utility: bool = False
    is_config: bool = False
    semantic_value: float = 1.0  # Multiplier for importance


class SemanticClassifier:
    """
    Classifies modules by their semantic purpose

    This goes beyond structural analysis to understand WHAT a module does
    """

    def __init__(self):
        self.test_patterns = [
            r'.*test.*',
            r'.*_test$',
            r'^test_.*'
        ]

        self.doc_patterns = [
            r'.*\.md$',
            r'.*readme.*',
            r'.*doc.*',
            r'.*guide.*'
        ]

        self.entry_patterns = [
            r'.*__main__.*',
            r'.*main\.py$',
            r'.*run\.py$',
            r'.*start\.py$'
        ]

        self.utility_patterns = [
            r'.*util.*',
            r'.*helper.*',
            r'.*tool.*',
            r'.*common.*'
        ]

        self.config_patterns = [
            r'.*config.*',
            r'.*settings.*',
            r'.*__init__.*',
            r'.*setup.*'
        ]

    def classify(self, module: Module) -> SemanticClassification:
        """Classify a module by semantic purpose"""
        classification = SemanticClassification(module_name=module.name)

        name_lower = module.name.lower()

        # Check test
        if any(re.match(p, name_lower) for p in self.test_patterns):
            classification.is_test = True
            classification.semantic_value = 2.0  # Tests are very valuable!

        # Check documentation
        elif any(re.match(p, name_lower) for p in self.doc_patterns):
            classification.is_documentation = True
            classification.semantic_value = 1.5

        # Check entry point
        elif any(re.match(p, name_lower) for p in self.entry_patterns):
            classification.is_entry_point = True
            classification.semantic_value = 1.3

        # Check utility
        elif any(re.match(p, name_lower) for p in self.utility_patterns):
            classification.is_utility = True
            classification.semantic_value = 1.2

        # Check config
        elif any(re.match(p, name_lower) for p in self.config_patterns):
            classification.is_config = True
            classification.semantic_value = 1.2

        return classification


# ============================================================================
# SEMANTIC-AWARE HARMONY ANALYZER
# ============================================================================

@dataclass
class SemanticHarmonyMetrics(HarmonyMetrics):
    """Extended harmony metrics with semantic awareness"""
    semantic_value: float = 0.0  # Average semantic value of modules
    valuable_dead_ends: int = 0   # Dead ends that are semantically valuable
    true_dead_ends: int = 0       # Dead ends with no semantic value


class SemanticHarmonyAnalyzer(HarmonyAnalyzer):
    """
    Enhanced harmony analyzer that considers semantic value

    Prevents deletion of valuable modules (tests, docs, entry points)
    even if they have no incoming dependencies
    """

    def __init__(self, alpha=0.3, beta=0.2, gamma=0.2, delta=0.1, epsilon=0.2):
        """
        Weights for enhanced harmony metric:
        H = α·Coherence - β·Coupling + γ·Coverage - δ·Redundancy + ε·Value

        Note: epsilon is new - semantic value weight
        """
        super().__init__(alpha, beta, gamma, delta)
        self.epsilon = epsilon
        self.classifier = SemanticClassifier()

    def analyze(self, graph: DependencyGraph) -> SemanticHarmonyMetrics:
        """Compute harmony metrics with semantic awareness"""
        # Get base metrics
        base_metrics = super().analyze(graph)

        # Classify all modules
        classifications = {
            name: self.classifier.classify(module)
            for name, module in graph.modules.items()
        }

        # Compute semantic value
        semantic_value = self._compute_semantic_value(graph, classifications)

        # Identify valuable vs. true dead ends
        dead_ends = graph.get_dead_ends()
        valuable_dead_ends = []
        true_dead_ends = []

        for dead_end in dead_ends:
            classification = classifications.get(dead_end)
            if classification and classification.semantic_value > 1.0:
                valuable_dead_ends.append(dead_end)
            else:
                true_dead_ends.append(dead_end)

        # Enhanced overall harmony
        overall_harmony = (
            self.alpha * base_metrics.coherence -
            self.beta * base_metrics.coupling +
            self.gamma * base_metrics.coverage -
            self.delta * base_metrics.redundancy +
            self.epsilon * semantic_value  # NEW: Semantic value term
        )

        return SemanticHarmonyMetrics(
            coherence=base_metrics.coherence,
            coupling=base_metrics.coupling,
            coverage=base_metrics.coverage,
            redundancy=base_metrics.redundancy,
            overall_harmony=overall_harmony,
            semantic_value=semantic_value,
            num_islands=base_metrics.num_islands,
            num_dead_ends=len(dead_ends),
            valuable_dead_ends=len(valuable_dead_ends),
            true_dead_ends=len(true_dead_ends),
            num_hubs=base_metrics.num_hubs,
            avg_module_size=base_metrics.avg_module_size,
            avg_complexity=base_metrics.avg_complexity
        )

    def _compute_semantic_value(
        self,
        graph: DependencyGraph,
        classifications: Dict[str, SemanticClassification]
    ) -> float:
        """
        Compute overall semantic value of architecture

        Higher value = more tests, docs, utilities, entry points
        """
        if not graph.modules:
            return 0.0

        # Weighted average of semantic values
        total_value = sum(
            classifications[name].semantic_value
            for name in graph.modules.keys()
            if name in classifications
        )

        avg_value = total_value / len(graph.modules)

        # Normalize to [0, 1] range
        # semantic_value ranges from 1.0 (default) to 2.0 (tests)
        # So normalize: (avg - 1.0) / (2.0 - 1.0)
        normalized = (avg_value - 1.0) / 1.0

        return normalized


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_semantic_harmony():
    """
    Demonstrate semantic-aware harmony analysis

    Shows how the improved metric distinguishes valuable dead ends
    from true dead ends
    """
    print("=" * 70)
    print("PHASE 9: SEMANTIC-AWARE ARCHITECTURAL HARMONY")
    print("=" * 70)
    print()
    print("Lesson learned from Phase 8:")
    print("  Structural metrics alone miss semantic value")
    print()
    print("Solution:")
    print("  Add semantic weighting for tests, docs, entry points, utilities")
    print()
    print("=" * 70)
    print()

    # Map architecture
    print("─" * 70)
    print("STEP 1: ARCHITECTURE MAPPING")
    print("─" * 70)
    print()

    mapper = ArchitectureMapper(root_dir='.')
    graph = mapper.scan()

    print(f"Found {len(graph.modules)} modules")
    print()

    # Classify modules
    print("─" * 70)
    print("STEP 2: SEMANTIC CLASSIFICATION")
    print("─" * 70)
    print()

    classifier = SemanticClassifier()
    classifications = {}

    for name, module in graph.modules.items():
        classification = classifier.classify(module)
        classifications[name] = classification

        if classification.semantic_value > 1.0:
            category = []
            if classification.is_test:
                category.append("TEST")
            if classification.is_documentation:
                category.append("DOC")
            if classification.is_entry_point:
                category.append("ENTRY")
            if classification.is_utility:
                category.append("UTIL")
            if classification.is_config:
                category.append("CONFIG")

            print(f"{name}")
            print(f"  Category: {', '.join(category)}")
            print(f"  Value: {classification.semantic_value}x")
            print()

    # Compare metrics
    print("─" * 70)
    print("STEP 3: HARMONY COMPARISON")
    print("─" * 70)
    print()

    # Old metric (structural only)
    old_analyzer = HarmonyAnalyzer()
    old_metrics = old_analyzer.analyze(graph)

    # New metric (semantic-aware)
    new_analyzer = SemanticHarmonyAnalyzer()
    new_metrics = new_analyzer.analyze(graph)

    print("OLD METRIC (Structural Only):")
    print(f"  Harmony: {old_metrics.overall_harmony:.3f}")
    print(f"  Dead ends: {old_metrics.num_dead_ends} (all treated equally)")
    print()

    print("NEW METRIC (Semantic-Aware):")
    print(f"  Harmony: {new_metrics.overall_harmony:.3f}")
    print(f"  Semantic value: {new_metrics.semantic_value:.3f}")
    print(f"  Valuable dead ends: {new_metrics.valuable_dead_ends}")
    print(f"  True dead ends: {new_metrics.true_dead_ends}")
    print()

    print(f"Harmony change: {new_metrics.overall_harmony - old_metrics.overall_harmony:+.3f}")
    print()

    # Identify valuable dead ends
    print("─" * 70)
    print("STEP 4: VALUABLE VS. TRUE DEAD ENDS")
    print("─" * 70)
    print()

    dead_ends = graph.get_dead_ends()

    if dead_ends:
        print("VALUABLE DEAD ENDS (should NOT be deleted):")
        for dead_end in dead_ends:
            classification = classifications.get(dead_end)
            if classification and classification.semantic_value > 1.0:
                print(f"  • {dead_end} (value: {classification.semantic_value}x)")
                if classification.is_test:
                    print(f"    → Provides test coverage")
                if classification.is_documentation:
                    print(f"    → Provides documentation")
                if classification.is_entry_point:
                    print(f"    → Entry point for users")
        print()

        print("TRUE DEAD ENDS (candidates for removal):")
        found_true_dead_ends = False
        for dead_end in dead_ends:
            classification = classifications.get(dead_end)
            if not classification or classification.semantic_value <= 1.0:
                print(f"  • {dead_end}")
                found_true_dead_ends = True

        if not found_true_dead_ends:
            print(f"  (none found)")
        print()

    # Summary
    print("=" * 70)
    print("SEMANTIC HARMONY ANALYSIS COMPLETE")
    print("=" * 70)
    print()
    print("KEY INSIGHT:")
    print("  The system now distinguishes:")
    print("    • Valuable dead ends (tests, docs) → KEEP")
    print("    • True dead ends (unused code) → SAFE TO REMOVE")
    print()
    print("This prevents Phase 8's mistake of deleting test_suite.py")
    print()
    print("Enhanced Harmony Formula:")
    print("  H = α·Coherence - β·Coupling + γ·Coverage - δ·Redundancy + ε·Value")
    print()
    print("Where Value rewards:")
    print("  • Test files (2.0x value)")
    print("  • Documentation (1.5x value)")
    print("  • Entry points (1.3x value)")
    print("  • Utilities (1.2x value)")
    print()


if __name__ == '__main__':
    demonstrate_semantic_harmony()
