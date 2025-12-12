"""
Test Suite for Equation Simplification Tool

Tests the symbolic manipulation, simplification rules,
and functional analysis capabilities.
"""

import sys
from dataclasses import dataclass
from typing import List, Tuple

from equation_simplifier import (
    Expression, ExpressionType, OperatorType,
    ExpressionBuilder, SimplificationConfig,
    EquationSimplifier, FunctionalAnalyzer,
    parse_lagrangian, simplify_equation, analyze_functional,
    EquationImprover,
    CombineLikeTermsRule, IdentityRule, ZeroProductRule,
    ConstantFoldingRule, FactorCommonRule
)


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    message: str = ""


class EquationSimplifierTestSuite:
    """Comprehensive test suite for the equation simplifier."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.verbose = True

    def run_all_tests(self) -> Tuple[int, int]:
        """Run all tests and return (passed, total) counts."""
        self.results = []

        # Expression building tests
        self.test_constant_creation()
        self.test_variable_creation()
        self.test_function_creation()
        self.test_functional_creation()
        self.test_operator_creation()
        self.test_expression_to_string()

        # Simplification rule tests
        self.test_identity_rule_addition()
        self.test_identity_rule_multiplication()
        self.test_zero_product_rule()
        self.test_constant_folding_add()
        self.test_constant_folding_mul()
        self.test_combine_like_terms()
        self.test_factor_common()

        # Parsing tests
        self.test_parse_simple_sum()
        self.test_parse_lagrangian()
        self.test_parse_with_parameters()
        self.test_parse_negative_term()

        # Integration tests
        self.test_simplify_combined()
        self.test_functional_analysis()
        self.test_separability_detection()
        self.test_dependency_analysis()

        # The user's specific equation
        self.test_user_equation()

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        return passed, total

    def _record(self, name: str, passed: bool, message: str = ""):
        """Record a test result."""
        result = TestResult(name, passed, message)
        self.results.append(result)
        if self.verbose:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {name}")
            if message and not passed:
                print(f"         {message}")

    # === Expression Building Tests ===

    def test_constant_creation(self):
        """Test creating constant expressions."""
        c = ExpressionBuilder.constant(3.14)
        passed = (c.expr_type == ExpressionType.CONSTANT and
                 c.value == 3.14 and
                 c.to_string() == "3.14")
        self._record("Constant creation", passed)

    def test_variable_creation(self):
        """Test creating variable expressions."""
        v = ExpressionBuilder.variable("ψ")
        passed = (v.expr_type == ExpressionType.VARIABLE and
                 v.name == "ψ" and
                 "ψ" in v.dependencies)
        self._record("Variable creation", passed)

    def test_function_creation(self):
        """Test creating function expressions."""
        x = ExpressionBuilder.variable("x")
        f = ExpressionBuilder.function("F", x)
        passed = (f.expr_type == ExpressionType.FUNCTION and
                 f.name == "F" and
                 f.to_string() == "F(x)")
        self._record("Function creation", passed)

    def test_functional_creation(self):
        """Test creating functional expressions with parameters."""
        u = ExpressionBuilder.variable("U")
        gamma = ExpressionBuilder.functional("Γ", u, parameters=["ψ"])
        passed = (gamma.expr_type == ExpressionType.FUNCTIONAL and
                 "ψ" in gamma.metadata.get('parameters', []))
        self._record("Functional creation", passed)

    def test_operator_creation(self):
        """Test creating operator expressions."""
        a = ExpressionBuilder.variable("a")
        b = ExpressionBuilder.variable("b")
        sum_expr = ExpressionBuilder.add(a, b)
        passed = (sum_expr.expr_type == ExpressionType.OPERATOR and
                 sum_expr.operator == OperatorType.ADD and
                 len(sum_expr.args) == 2)
        self._record("Operator creation", passed)

    def test_expression_to_string(self):
        """Test string representation of complex expressions."""
        x = ExpressionBuilder.variable("x")
        y = ExpressionBuilder.variable("y")
        expr = ExpressionBuilder.add(
            ExpressionBuilder.function("F", x),
            ExpressionBuilder.function("G", y)
        )
        result = expr.to_string()
        passed = "F(x)" in result and "G(y)" in result and "+" in result
        self._record("Expression to_string", passed, f"Got: {result}")

    # === Simplification Rule Tests ===

    def test_identity_rule_addition(self):
        """Test x + 0 → x."""
        rule = IdentityRule()
        x = ExpressionBuilder.variable("x")
        zero = ExpressionBuilder.constant(0.0)
        expr = ExpressionBuilder.add(x, zero)

        passed = rule.applies(expr)
        if passed:
            result = rule.apply(expr)
            passed = result.to_string() == "x"
        self._record("Identity rule (addition)", passed)

    def test_identity_rule_multiplication(self):
        """Test x * 1 → x."""
        rule = IdentityRule()
        x = ExpressionBuilder.variable("x")
        one = ExpressionBuilder.constant(1.0)
        expr = ExpressionBuilder.multiply(x, one)

        passed = rule.applies(expr)
        if passed:
            result = rule.apply(expr)
            passed = result.to_string() == "x"
        self._record("Identity rule (multiplication)", passed)

    def test_zero_product_rule(self):
        """Test x * 0 → 0."""
        rule = ZeroProductRule()
        x = ExpressionBuilder.variable("x")
        zero = ExpressionBuilder.constant(0.0)
        expr = ExpressionBuilder.multiply(x, zero)

        passed = rule.applies(expr)
        if passed:
            result = rule.apply(expr)
            passed = (result.expr_type == ExpressionType.CONSTANT and
                     result.value == 0.0)
        self._record("Zero product rule", passed)

    def test_constant_folding_add(self):
        """Test 2 + 3 → 5."""
        rule = ConstantFoldingRule()
        two = ExpressionBuilder.constant(2.0)
        three = ExpressionBuilder.constant(3.0)
        expr = ExpressionBuilder.add(two, three)

        passed = rule.applies(expr)
        if passed:
            result = rule.apply(expr)
            passed = (result.expr_type == ExpressionType.CONSTANT and
                     result.value == 5.0)
        self._record("Constant folding (addition)", passed)

    def test_constant_folding_mul(self):
        """Test 2 * 3 → 6."""
        rule = ConstantFoldingRule()
        two = ExpressionBuilder.constant(2.0)
        three = ExpressionBuilder.constant(3.0)
        expr = ExpressionBuilder.multiply(two, three)

        passed = rule.applies(expr)
        if passed:
            result = rule.apply(expr)
            passed = (result.expr_type == ExpressionType.CONSTANT and
                     result.value == 6.0)
        self._record("Constant folding (multiplication)", passed)

    def test_combine_like_terms(self):
        """Test F(x) + F(x) → 2·F(x)."""
        rule = CombineLikeTermsRule()
        x = ExpressionBuilder.variable("x")
        f1 = ExpressionBuilder.function("F", x)
        f2 = ExpressionBuilder.function("F", x)
        expr = ExpressionBuilder.add(f1, f2)

        passed = rule.applies(expr)
        if passed:
            result = rule.apply(expr)
            result_str = result.to_string()
            passed = "2" in result_str and "F(x)" in result_str
        self._record("Combine like terms", passed)

    def test_factor_common(self):
        """Test A·F + A·G → A·(F + G)."""
        rule = FactorCommonRule()
        a = ExpressionBuilder.variable("A")
        f = ExpressionBuilder.variable("F")
        g = ExpressionBuilder.variable("G")

        term1 = ExpressionBuilder.multiply(a, f)
        term2 = ExpressionBuilder.multiply(a, g)
        expr = ExpressionBuilder.add(term1, term2)

        applies = rule.applies(expr)
        if applies:
            result = rule.apply(expr)
            # Should factor out A
            result_str = result.to_string()
            passed = "A" in result_str
        else:
            passed = False
        self._record("Factor common terms", passed)

    # === Parsing Tests ===

    def test_parse_simple_sum(self):
        """Test parsing a simple sum: F(x) + G(y)."""
        result = parse_lagrangian("F(x) + G(y)")
        passed = (result.expr_type == ExpressionType.OPERATOR and
                 result.operator == OperatorType.ADD and
                 len(result.args) == 2)
        self._record("Parse simple sum", passed)

    def test_parse_lagrangian(self):
        """Test parsing full Lagrangian notation."""
        result = parse_lagrangian("L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U)")
        passed = (result.expr_type == ExpressionType.OPERATOR and
                 len(result.args) == 3)
        self._record("Parse Lagrangian", passed)

    def test_parse_with_parameters(self):
        """Test parsing functional with parameters: Γ(U; ψ)."""
        result = parse_lagrangian("Γ(U; ψ)")
        passed = (result.expr_type == ExpressionType.FUNCTIONAL and
                 result.name == "Γ" and
                 "ψ" in result.metadata.get('parameters', []))
        self._record("Parse with parameters", passed)

    def test_parse_negative_term(self):
        """Test parsing expression with negative terms."""
        result = parse_lagrangian("F(x) - G(y)")
        # Should parse as subtraction or addition with negative
        result_str = result.to_string()
        passed = "F(x)" in result_str and "G(y)" in result_str
        self._record("Parse negative term", passed)

    # === Integration Tests ===

    def test_simplify_combined(self):
        """Test combined simplification of complex expression."""
        config = SimplificationConfig(verbose=False)
        simplifier = EquationSimplifier(config)

        # Create: F(x) + 0 + F(x)
        x = ExpressionBuilder.variable("x")
        f1 = ExpressionBuilder.function("F", x)
        zero = ExpressionBuilder.constant(0.0)
        f2 = ExpressionBuilder.function("F", x)
        expr = ExpressionBuilder.add(f1, zero, f2)

        result = simplifier.simplify(expr)
        result_str = result.to_string()

        # Should remove 0 and combine like terms (2 or 2.0 both acceptable)
        has_coefficient = "2" in result_str or "2.0" in result_str
        passed = has_coefficient and "F(x)" in result_str and result_str.count("0") <= 1  # allow 2.0
        self._record("Combined simplification", passed, f"Got: {result_str}")

    def test_functional_analysis(self):
        """Test functional analysis of Lagrangian."""
        analysis = analyze_functional("L = F(ψ) + H(σ) + K(U)")

        passed = (analysis.is_separable and
                 len(analysis.independent_terms) == 3 and
                 len(analysis.coupled_terms) == 0)
        self._record("Functional analysis (separable)", passed)

    def test_separability_detection(self):
        """Test detection of non-separable functionals."""
        # Γ(U; ψ) depends on both U and ψ (through the ; notation means parameterized)
        # But the actual dependencies come from the args
        analysis = analyze_functional("L = F(ψ) + Γ(U, ψ)")  # Both as args

        # With both U and ψ as args, Γ depends on both
        has_coupled = len(analysis.coupled_terms) > 0
        self._record("Separability detection (coupled)", has_coupled)

    def test_dependency_analysis(self):
        """Test variable dependency analysis."""
        analysis = analyze_functional("L = F(x) + G(x, y) + H(z)")

        deps = analysis.variable_dependencies
        # x should be coupled with y (through G)
        x_deps = deps.get('x', set())
        passed = 'y' in x_deps or 'x' in deps.get('y', set())
        self._record("Dependency analysis", passed)

    def test_user_equation(self):
        """Test the user's specific equation: L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)."""
        equation = "L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)"

        improver = EquationImprover()
        result = improver.improve(equation)

        # Check all expected components are present
        checks = [
            result['parsed'] is not None,
            result['simplified'] is not None,
            len(result['improvements']) > 0,
            'F(ψ)' in result['parsed'] or 'F' in result['parsed'],
        ]

        passed = all(checks)
        self._record("User equation analysis", passed,
                    f"Parsed: {result['parsed']}, Simplified: {result['simplified']}")

    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print("\n" + "=" * 50)
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 50)

        if passed < total:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")

        return passed == total


def run_demo():
    """Run a demonstration of the equation improvement tool."""
    print("\n" + "=" * 60)
    print("EQUATION IMPROVEMENT DEMONSTRATION")
    print("=" * 60)

    # The user's equation
    user_equation = "L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)"

    print(f"\nYour equation: {user_equation}")
    print("\nRunning analysis...")

    improver = EquationImprover(SimplificationConfig(verbose=False))
    improver.print_report(user_equation)

    # Show some mathematical insights
    print("\n" + "=" * 60)
    print("MATHEMATICAL INSIGHTS")
    print("=" * 60)

    insights = """
Based on the structure L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ):

1. PARTIAL SEPARABILITY:
   • F(ψ) and H(σ) are independent - can be optimized separately
   • Γ(U; ψ) couples U with ψ - requires joint optimization

2. EULER-LAGRANGE EQUATIONS:
   For variational problems δL = 0:
   • δL/δψ = F'(ψ) + ∂Γ/∂ψ = 0
   • δL/δσ = H'(σ) = 0          (independent!)
   • δL/δU = ∂Γ/∂U = 0

3. OPTIMIZATION STRATEGY:
   Block coordinate descent:
   • Step 1: Optimize σ independently via H'(σ) = 0
   • Step 2: Jointly optimize (ψ, U) via coupled equations

4. POSSIBLE IMPROVEMENTS:
   • If Γ(U; ψ) = Γ₁(U) · Γ₂(ψ), the system becomes fully separable
   • Consider change of variables: (ψ, U) → (ξ, η) to decouple
   • If F, H, Γ are convex, the problem has unique global minimum
"""
    print(insights)


if __name__ == "__main__":
    print("=" * 60)
    print("EQUATION SIMPLIFIER TEST SUITE")
    print("=" * 60)
    print()

    # Run tests
    suite = EquationSimplifierTestSuite()
    suite.run_all_tests()
    success = suite.print_summary()

    # Run demo
    run_demo()

    sys.exit(0 if success else 1)
