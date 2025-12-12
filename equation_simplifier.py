"""
Equation Simplification and Mathematical Improvement Tool

This module provides symbolic manipulation and mathematical improvement
capabilities for equations, particularly functionals and Lagrangians of the form:

    L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)

Features:
- Symbolic expression parsing and representation
- Algebraic simplification (combining like terms, factoring)
- Functional analysis (identifying separable terms, dependencies)
- Mathematical improvements (canonical forms, symmetry exploitation)
- Variational analysis for Lagrangians

Author: Recursive Dialogue Engine Project
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union, Callable
from enum import Enum, auto
from abc import ABC, abstractmethod
import re
from collections import defaultdict
import copy


class ExpressionType(Enum):
    """Types of mathematical expressions."""
    CONSTANT = auto()
    VARIABLE = auto()
    FUNCTION = auto()
    OPERATOR = auto()
    FUNCTIONAL = auto()
    DERIVATIVE = auto()
    INTEGRAL = auto()


class OperatorType(Enum):
    """Supported mathematical operators."""
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    POW = "^"
    COMPOSE = "∘"
    PARTIAL = "∂"
    NABLA = "∇"
    LAPLACIAN = "∇²"
    DELTA = "δ"  # Functional derivative


@dataclass
class SimplificationConfig:
    """Configuration for equation simplification."""
    combine_like_terms: bool = True
    factor_common: bool = True
    expand_products: bool = False
    simplify_fractions: bool = True
    use_symmetry: bool = True
    canonical_ordering: bool = True
    identify_separability: bool = True
    max_iterations: int = 100
    verbose: bool = False


@dataclass
class Expression:
    """
    Represents a mathematical expression in a tree structure.

    Examples:
        - Constant: Expression(ExpressionType.CONSTANT, value=2.0)
        - Variable: Expression(ExpressionType.VARIABLE, name="ψ")
        - Function: Expression(ExpressionType.FUNCTION, name="F", args=[ψ])
        - Sum: Expression(ExpressionType.OPERATOR, operator=ADD, args=[a, b])
    """
    expr_type: ExpressionType
    name: Optional[str] = None
    value: Optional[float] = None
    operator: Optional[OperatorType] = None
    args: List['Expression'] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Compute dependencies after initialization."""
        if not self.dependencies:
            self.dependencies = self._compute_dependencies()

    def _compute_dependencies(self) -> Set[str]:
        """Recursively compute variable dependencies."""
        deps = set()
        if self.expr_type == ExpressionType.VARIABLE:
            deps.add(self.name)
        for arg in self.args:
            deps.update(arg._compute_dependencies())
        return deps

    def __repr__(self) -> str:
        return self.to_string()

    def to_string(self, parent_precedence: int = 0) -> str:
        """Convert expression to human-readable string."""
        if self.expr_type == ExpressionType.CONSTANT:
            return str(self.value)
        elif self.expr_type == ExpressionType.VARIABLE:
            return self.name
        elif self.expr_type == ExpressionType.FUNCTION:
            args_str = ", ".join(arg.to_string() for arg in self.args)
            return f"{self.name}({args_str})"
        elif self.expr_type == ExpressionType.FUNCTIONAL:
            args_str = ", ".join(arg.to_string() for arg in self.args)
            params = self.metadata.get('parameters', [])
            if params:
                params_str = "; ".join(params)
                return f"{self.name}({args_str}; {params_str})"
            return f"{self.name}[{args_str}]"
        elif self.expr_type == ExpressionType.OPERATOR:
            return self._operator_to_string(parent_precedence)
        elif self.expr_type == ExpressionType.DERIVATIVE:
            var = self.metadata.get('with_respect_to', '?')
            return f"∂{self.args[0].to_string()}/∂{var}"
        return f"<?{self.expr_type}?>"

    def _operator_to_string(self, parent_prec: int) -> str:
        """Format operator expression with appropriate parentheses."""
        precedence = {
            OperatorType.ADD: 1, OperatorType.SUB: 1,
            OperatorType.MUL: 2, OperatorType.DIV: 2,
            OperatorType.POW: 3, OperatorType.COMPOSE: 4
        }
        prec = precedence.get(self.operator, 0)

        if self.operator in (OperatorType.ADD, OperatorType.SUB):
            parts = []
            for i, arg in enumerate(self.args):
                s = arg.to_string(prec)
                if i == 0:
                    parts.append(s)
                elif self.operator == OperatorType.SUB and i == 1:
                    parts.append(f" - {s}")
                else:
                    parts.append(f" + {s}")
            result = "".join(parts)
        elif self.operator == OperatorType.MUL:
            parts = [arg.to_string(prec) for arg in self.args]
            result = " · ".join(parts)
        elif self.operator == OperatorType.DIV:
            result = f"{self.args[0].to_string(prec)} / {self.args[1].to_string(prec)}"
        elif self.operator == OperatorType.POW:
            result = f"{self.args[0].to_string(prec)}^{self.args[1].to_string(prec)}"
        else:
            result = f"{self.operator.value}({', '.join(a.to_string() for a in self.args)})"

        if prec < parent_prec:
            result = f"({result})"
        return result

    def copy(self) -> 'Expression':
        """Create a deep copy of the expression."""
        return copy.deepcopy(self)

    def substitute(self, var_name: str, replacement: 'Expression') -> 'Expression':
        """Substitute a variable with another expression."""
        if self.expr_type == ExpressionType.VARIABLE and self.name == var_name:
            return replacement.copy()

        new_expr = self.copy()
        new_expr.args = [arg.substitute(var_name, replacement) for arg in self.args]
        new_expr.dependencies = new_expr._compute_dependencies()
        return new_expr


class ExpressionBuilder:
    """Factory for creating common expression types."""

    @staticmethod
    def constant(value: float) -> Expression:
        return Expression(ExpressionType.CONSTANT, value=value)

    @staticmethod
    def variable(name: str) -> Expression:
        return Expression(ExpressionType.VARIABLE, name=name)

    @staticmethod
    def function(name: str, *args: Expression) -> Expression:
        return Expression(ExpressionType.FUNCTION, name=name, args=list(args))

    @staticmethod
    def functional(name: str, *args: Expression, parameters: List[str] = None) -> Expression:
        return Expression(
            ExpressionType.FUNCTIONAL,
            name=name,
            args=list(args),
            metadata={'parameters': parameters or []}
        )

    @staticmethod
    def add(*terms: Expression) -> Expression:
        if len(terms) == 1:
            return terms[0]
        return Expression(ExpressionType.OPERATOR, operator=OperatorType.ADD, args=list(terms))

    @staticmethod
    def subtract(a: Expression, b: Expression) -> Expression:
        return Expression(ExpressionType.OPERATOR, operator=OperatorType.SUB, args=[a, b])

    @staticmethod
    def multiply(*factors: Expression) -> Expression:
        if len(factors) == 1:
            return factors[0]
        return Expression(ExpressionType.OPERATOR, operator=OperatorType.MUL, args=list(factors))

    @staticmethod
    def divide(a: Expression, b: Expression) -> Expression:
        return Expression(ExpressionType.OPERATOR, operator=OperatorType.DIV, args=[a, b])

    @staticmethod
    def power(base: Expression, exp: Expression) -> Expression:
        return Expression(ExpressionType.OPERATOR, operator=OperatorType.POW, args=[base, exp])

    @staticmethod
    def derivative(expr: Expression, with_respect_to: str) -> Expression:
        return Expression(
            ExpressionType.DERIVATIVE,
            args=[expr],
            metadata={'with_respect_to': with_respect_to}
        )


class SimplificationRule(ABC):
    """Abstract base class for simplification rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the simplification rule."""
        pass

    @abstractmethod
    def applies(self, expr: Expression) -> bool:
        """Check if this rule applies to the expression."""
        pass

    @abstractmethod
    def apply(self, expr: Expression) -> Expression:
        """Apply the simplification rule."""
        pass


class CombineLikeTermsRule(SimplificationRule):
    """Combine like terms in addition: F(ψ) + F(ψ) → 2·F(ψ)"""

    @property
    def name(self) -> str:
        return "Combine Like Terms"

    def applies(self, expr: Expression) -> bool:
        if expr.expr_type != ExpressionType.OPERATOR:
            return False
        if expr.operator != OperatorType.ADD:
            return False
        # Check for duplicate terms
        term_strs = [arg.to_string() for arg in expr.args]
        return len(term_strs) != len(set(term_strs))

    def apply(self, expr: Expression) -> Expression:
        term_counts: Dict[str, Tuple[Expression, int]] = {}
        for arg in expr.args:
            key = arg.to_string()
            if key in term_counts:
                term_counts[key] = (arg, term_counts[key][1] + 1)
            else:
                term_counts[key] = (arg, 1)

        new_args = []
        for key, (term, count) in term_counts.items():
            if count == 1:
                new_args.append(term)
            else:
                coef = ExpressionBuilder.constant(float(count))
                new_args.append(ExpressionBuilder.multiply(coef, term))

        if len(new_args) == 1:
            return new_args[0]
        return ExpressionBuilder.add(*new_args)


class IdentityRule(SimplificationRule):
    """Remove identity elements: x + 0 → x, x · 1 → x"""

    @property
    def name(self) -> str:
        return "Identity Elements"

    def applies(self, expr: Expression) -> bool:
        if expr.expr_type != ExpressionType.OPERATOR:
            return False
        for arg in expr.args:
            if arg.expr_type == ExpressionType.CONSTANT:
                if expr.operator in (OperatorType.ADD, OperatorType.SUB) and arg.value == 0:
                    return True
                if expr.operator == OperatorType.MUL and arg.value == 1:
                    return True
        return False

    def apply(self, expr: Expression) -> Expression:
        if expr.operator in (OperatorType.ADD, OperatorType.SUB):
            new_args = [a for a in expr.args
                       if not (a.expr_type == ExpressionType.CONSTANT and a.value == 0)]
            if not new_args:
                return ExpressionBuilder.constant(0.0)
            if len(new_args) == 1:
                return new_args[0]
            return Expression(ExpressionType.OPERATOR, operator=expr.operator, args=new_args)

        if expr.operator == OperatorType.MUL:
            new_args = [a for a in expr.args
                       if not (a.expr_type == ExpressionType.CONSTANT and a.value == 1)]
            if not new_args:
                return ExpressionBuilder.constant(1.0)
            if len(new_args) == 1:
                return new_args[0]
            return Expression(ExpressionType.OPERATOR, operator=expr.operator, args=new_args)

        return expr


class ZeroProductRule(SimplificationRule):
    """x · 0 → 0"""

    @property
    def name(self) -> str:
        return "Zero Product"

    def applies(self, expr: Expression) -> bool:
        if expr.expr_type != ExpressionType.OPERATOR or expr.operator != OperatorType.MUL:
            return False
        return any(a.expr_type == ExpressionType.CONSTANT and a.value == 0 for a in expr.args)

    def apply(self, expr: Expression) -> Expression:
        return ExpressionBuilder.constant(0.0)


class ConstantFoldingRule(SimplificationRule):
    """Evaluate constant expressions: 2 + 3 → 5"""

    @property
    def name(self) -> str:
        return "Constant Folding"

    def applies(self, expr: Expression) -> bool:
        if expr.expr_type != ExpressionType.OPERATOR:
            return False
        return all(a.expr_type == ExpressionType.CONSTANT for a in expr.args)

    def apply(self, expr: Expression) -> Expression:
        values = [a.value for a in expr.args]

        if expr.operator == OperatorType.ADD:
            return ExpressionBuilder.constant(sum(values))
        elif expr.operator == OperatorType.SUB:
            return ExpressionBuilder.constant(values[0] - values[1])
        elif expr.operator == OperatorType.MUL:
            result = 1.0
            for v in values:
                result *= v
            return ExpressionBuilder.constant(result)
        elif expr.operator == OperatorType.DIV:
            if values[1] != 0:
                return ExpressionBuilder.constant(values[0] / values[1])
        elif expr.operator == OperatorType.POW:
            return ExpressionBuilder.constant(values[0] ** values[1])

        return expr


class FactorCommonRule(SimplificationRule):
    """Factor out common terms: A·F(ψ) + A·G(ψ) → A·(F(ψ) + G(ψ))"""

    @property
    def name(self) -> str:
        return "Factor Common Terms"

    def applies(self, expr: Expression) -> bool:
        if expr.expr_type != ExpressionType.OPERATOR or expr.operator != OperatorType.ADD:
            return False
        # Check if terms share common factors
        common = self._find_common_factor(expr.args)
        return common is not None

    def _find_common_factor(self, terms: List[Expression]) -> Optional[Expression]:
        """Find a factor common to all terms."""
        if len(terms) < 2:
            return None

        # Get factors from first term
        first_factors = self._get_factors(terms[0])

        for factor in first_factors:
            factor_str = factor.to_string()
            if all(self._contains_factor(term, factor_str) for term in terms[1:]):
                return factor
        return None

    def _get_factors(self, expr: Expression) -> List[Expression]:
        """Get all multiplicative factors of an expression."""
        if expr.expr_type == ExpressionType.OPERATOR and expr.operator == OperatorType.MUL:
            return expr.args
        return [expr]

    def _contains_factor(self, expr: Expression, factor_str: str) -> bool:
        """Check if expression contains the given factor."""
        for f in self._get_factors(expr):
            if f.to_string() == factor_str:
                return True
        return False

    def apply(self, expr: Expression) -> Expression:
        common = self._find_common_factor(expr.args)
        if common is None:
            return expr

        common_str = common.to_string()
        new_terms = []
        for term in expr.args:
            factors = self._get_factors(term)
            remaining = [f for f in factors if f.to_string() != common_str]
            if not remaining:
                new_terms.append(ExpressionBuilder.constant(1.0))
            elif len(remaining) == 1:
                new_terms.append(remaining[0])
            else:
                new_terms.append(ExpressionBuilder.multiply(*remaining))

        inner_sum = ExpressionBuilder.add(*new_terms)
        return ExpressionBuilder.multiply(common, inner_sum)


class EquationSimplifier:
    """
    Main equation simplification engine.

    Applies a series of simplification rules to transform
    equations into improved/canonical forms.
    """

    def __init__(self, config: SimplificationConfig = None):
        self.config = config or SimplificationConfig()
        self.rules: List[SimplificationRule] = []
        self._init_rules()
        self.transformation_log: List[Tuple[str, str, str]] = []

    def _init_rules(self):
        """Initialize simplification rules based on config."""
        self.rules.append(ZeroProductRule())
        self.rules.append(IdentityRule())
        self.rules.append(ConstantFoldingRule())

        if self.config.combine_like_terms:
            self.rules.append(CombineLikeTermsRule())
        if self.config.factor_common:
            self.rules.append(FactorCommonRule())

    def add_rule(self, rule: SimplificationRule):
        """Add a custom simplification rule."""
        self.rules.append(rule)

    def simplify(self, expr: Expression) -> Expression:
        """
        Apply simplification rules until no more changes occur.

        Returns the simplified expression.
        """
        self.transformation_log = []
        current = expr.copy()

        for iteration in range(self.config.max_iterations):
            before = current.to_string()

            # Apply rules to subexpressions first (bottom-up)
            current = self._simplify_recursive(current)

            after = current.to_string()
            if before == after:
                break

            if self.config.verbose:
                print(f"Iteration {iteration + 1}: {before} → {after}")

        return current

    def _simplify_recursive(self, expr: Expression) -> Expression:
        """Recursively simplify expression and subexpressions."""
        # First simplify all subexpressions
        if expr.args:
            new_args = [self._simplify_recursive(arg) for arg in expr.args]
            expr = Expression(
                expr.expr_type,
                name=expr.name,
                value=expr.value,
                operator=expr.operator,
                args=new_args,
                metadata=expr.metadata.copy()
            )

        # Then apply rules to this expression
        for rule in self.rules:
            if rule.applies(expr):
                before = expr.to_string()
                expr = rule.apply(expr)
                after = expr.to_string()
                self.transformation_log.append((rule.name, before, after))

        return expr

    def get_transformation_history(self) -> List[str]:
        """Get human-readable transformation history."""
        return [f"[{rule}] {before} → {after}"
                for rule, before, after in self.transformation_log]


@dataclass
class FunctionalAnalysis:
    """Results of analyzing a functional/Lagrangian."""
    is_separable: bool
    independent_terms: List[Tuple[str, Expression]]
    coupled_terms: List[Tuple[Set[str], Expression]]
    variable_dependencies: Dict[str, Set[str]]
    symmetries: List[str]
    suggested_improvements: List[str]
    canonical_form: Optional[Expression] = None


class FunctionalAnalyzer:
    """
    Analyzes functional expressions like Lagrangians.

    Specializes in expressions of the form:
        L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)
    """

    def __init__(self, config: SimplificationConfig = None):
        self.config = config or SimplificationConfig()
        self.simplifier = EquationSimplifier(config)

    def analyze(self, expr: Expression) -> FunctionalAnalysis:
        """Perform comprehensive analysis of a functional expression."""
        # Simplify first
        simplified = self.simplifier.simplify(expr)

        # Analyze structure
        is_separable, indep, coupled = self._analyze_separability(simplified)
        var_deps = self._compute_variable_dependencies(simplified)
        symmetries = self._detect_symmetries(simplified)
        improvements = self._suggest_improvements(simplified, is_separable, var_deps)
        canonical = self._compute_canonical_form(simplified)

        return FunctionalAnalysis(
            is_separable=is_separable,
            independent_terms=indep,
            coupled_terms=coupled,
            variable_dependencies=var_deps,
            symmetries=symmetries,
            suggested_improvements=improvements,
            canonical_form=canonical
        )

    def _analyze_separability(self, expr: Expression) -> Tuple[bool, List, List]:
        """
        Analyze if the functional is separable.

        A functional L[ψ, σ, U] is separable if it can be written as
        a sum of terms each depending on disjoint subsets of variables.
        """
        independent_terms = []
        coupled_terms = []

        if expr.expr_type == ExpressionType.OPERATOR and expr.operator == OperatorType.ADD:
            terms = expr.args
        else:
            terms = [expr]

        all_vars = expr.dependencies

        for term in terms:
            deps = term.dependencies
            if len(deps) <= 1:
                var_name = list(deps)[0] if deps else "constant"
                independent_terms.append((var_name, term))
            else:
                coupled_terms.append((deps, term))

        # Check true separability: no variable appears in multiple terms
        var_appearances: Dict[str, int] = defaultdict(int)
        for _, term in independent_terms:
            for v in term.dependencies:
                var_appearances[v] += 1
        for deps, term in coupled_terms:
            for v in deps:
                var_appearances[v] += 1

        is_fully_separable = all(count == 1 for count in var_appearances.values())

        return is_fully_separable, independent_terms, coupled_terms

    def _compute_variable_dependencies(self, expr: Expression) -> Dict[str, Set[str]]:
        """Map each variable to all variables it's coupled with."""
        deps: Dict[str, Set[str]] = defaultdict(set)

        def analyze_term(term: Expression):
            term_vars = term.dependencies
            for v in term_vars:
                deps[v].update(term_vars)

        if expr.expr_type == ExpressionType.OPERATOR and expr.operator == OperatorType.ADD:
            for term in expr.args:
                analyze_term(term)
        else:
            analyze_term(expr)

        return dict(deps)

    def _detect_symmetries(self, expr: Expression) -> List[str]:
        """Detect mathematical symmetries in the expression."""
        symmetries = []
        expr_str = expr.to_string()

        # Check for additive symmetry patterns
        if expr.expr_type == ExpressionType.OPERATOR and expr.operator == OperatorType.ADD:
            term_patterns = [arg.to_string() for arg in expr.args]

            # Look for similar functional forms
            func_names = []
            for arg in expr.args:
                if arg.expr_type in (ExpressionType.FUNCTION, ExpressionType.FUNCTIONAL):
                    func_names.append(arg.name)

            if len(set(func_names)) < len(func_names):
                symmetries.append("Repeated functional form detected - possible exchange symmetry")

        # Check for derivative-like structure (suggests variational principle)
        if "∂" in expr_str or "∇" in expr_str or "δ" in expr_str:
            symmetries.append("Contains differential operators - likely variational structure")

        return symmetries

    def _suggest_improvements(self, expr: Expression, is_separable: bool,
                             var_deps: Dict) -> List[str]:
        """Suggest mathematical improvements for the expression."""
        suggestions = []

        # Separability suggestions
        if is_separable:
            suggestions.append(
                "✓ Functional is fully separable - optimization can be parallelized over independent variables"
            )
        else:
            coupled_vars = [v for v, deps in var_deps.items() if len(deps) > 1]
            if coupled_vars:
                suggestions.append(
                    f"Consider variable transformation to decouple: {', '.join(coupled_vars)}"
                )

        # Structure-based suggestions
        if expr.expr_type == ExpressionType.OPERATOR and expr.operator == OperatorType.ADD:
            n_terms = len(expr.args)
            if n_terms > 5:
                suggestions.append(
                    f"Expression has {n_terms} additive terms - consider grouping by physical meaning"
                )

        # Computational suggestions
        suggestions.append(
            "For numerical optimization: exploit separability using block coordinate descent"
        )
        suggestions.append(
            "For variational analysis: compute Euler-Lagrange equations for each field"
        )

        return suggestions

    def _compute_canonical_form(self, expr: Expression) -> Expression:
        """Reorder expression into canonical form."""
        if expr.expr_type != ExpressionType.OPERATOR or expr.operator != OperatorType.ADD:
            return expr

        # Sort terms: independent terms first, then coupled by number of dependencies
        def sort_key(term: Expression) -> Tuple[int, str]:
            n_deps = len(term.dependencies)
            # Secondary sort by string representation for consistency
            return (n_deps, term.to_string())

        sorted_terms = sorted(expr.args, key=sort_key)
        return ExpressionBuilder.add(*sorted_terms)


def parse_lagrangian(notation: str) -> Expression:
    """
    Parse a Lagrangian-style functional notation.

    Supports notation like:
        "L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)"

    Returns the right-hand side as an Expression tree.
    """
    # Remove the left side (L[...] =)
    if "=" in notation:
        notation = notation.split("=", 1)[1].strip()

    # Split on top-level + and -
    terms = []
    current_term = ""
    paren_depth = 0
    bracket_depth = 0

    for i, char in enumerate(notation):
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
        elif char in ('+', '-') and paren_depth == 0 and bracket_depth == 0:
            if current_term.strip():
                terms.append(current_term.strip())
            current_term = "" if char == '+' else "-"
            continue
        current_term += char

    if current_term.strip():
        terms.append(current_term.strip())

    # Parse each term
    parsed_terms = []
    for term in terms:
        parsed_terms.append(_parse_term(term.strip()))

    if len(parsed_terms) == 1:
        return parsed_terms[0]
    return ExpressionBuilder.add(*parsed_terms)


def _parse_term(term: str) -> Expression:
    """Parse a single term like 'F(ψ)' or 'Γ(U; ψ)'."""
    # Handle negative terms
    negative = False
    if term.startswith('-'):
        negative = True
        term = term[1:].strip()

    # Match function/functional pattern
    match = re.match(r'(\w+)\s*[\(\[]\s*([^)\]]+)\s*[\)\]]', term)
    if match:
        name = match.group(1)
        args_str = match.group(2)

        # Check for parameter notation (semicolon-separated)
        if ';' in args_str:
            parts = args_str.split(';')
            args_part = parts[0]
            params_part = parts[1] if len(parts) > 1 else ""

            args = [ExpressionBuilder.variable(a.strip())
                   for a in args_part.split(',')]
            params = [p.strip() for p in params_part.split(',') if p.strip()]

            result = ExpressionBuilder.functional(name, *args, parameters=params)
        else:
            args = [ExpressionBuilder.variable(a.strip())
                   for a in args_str.split(',')]

            if '[' in term:  # Functional notation
                result = ExpressionBuilder.functional(name, *args)
            else:  # Regular function
                result = ExpressionBuilder.function(name, *args)
    else:
        # Simple variable or constant
        try:
            result = ExpressionBuilder.constant(float(term))
        except ValueError:
            result = ExpressionBuilder.variable(term)

    if negative:
        result = ExpressionBuilder.multiply(
            ExpressionBuilder.constant(-1.0),
            result
        )

    return result


class EquationImprover:
    """
    High-level interface for equation improvement.

    Combines parsing, simplification, and analysis to provide
    comprehensive equation improvement suggestions.
    """

    def __init__(self, config: SimplificationConfig = None):
        self.config = config or SimplificationConfig()
        self.simplifier = EquationSimplifier(self.config)
        self.analyzer = FunctionalAnalyzer(self.config)

    def improve(self, equation: str) -> Dict:
        """
        Analyze and improve an equation.

        Args:
            equation: String representation of the equation

        Returns:
            Dictionary with analysis results and improvements
        """
        # Parse the equation
        expr = parse_lagrangian(equation)

        # Simplify
        simplified = self.simplifier.simplify(expr)

        # Analyze
        analysis = self.analyzer.analyze(expr)

        # Generate report
        return {
            'original': equation,
            'parsed': expr.to_string(),
            'simplified': simplified.to_string(),
            'canonical_form': analysis.canonical_form.to_string() if analysis.canonical_form else None,
            'is_separable': analysis.is_separable,
            'independent_terms': [(v, t.to_string()) for v, t in analysis.independent_terms],
            'coupled_terms': [(list(deps), t.to_string()) for deps, t in analysis.coupled_terms],
            'variable_dependencies': {k: list(v) for k, v in analysis.variable_dependencies.items()},
            'symmetries': analysis.symmetries,
            'improvements': analysis.suggested_improvements,
            'transformations': self.simplifier.get_transformation_history()
        }

    def print_report(self, equation: str):
        """Print a formatted improvement report."""
        result = self.improve(equation)

        print("=" * 60)
        print("EQUATION IMPROVEMENT REPORT")
        print("=" * 60)
        print(f"\nOriginal:   {result['original']}")
        print(f"Parsed:     {result['parsed']}")
        print(f"Simplified: {result['simplified']}")

        if result['canonical_form']:
            print(f"Canonical:  {result['canonical_form']}")

        print(f"\n{'─' * 40}")
        print("STRUCTURE ANALYSIS")
        print(f"{'─' * 40}")
        print(f"Separable: {'Yes' if result['is_separable'] else 'No'}")

        if result['independent_terms']:
            print("\nIndependent terms:")
            for var, term in result['independent_terms']:
                print(f"  • {var}: {term}")

        if result['coupled_terms']:
            print("\nCoupled terms:")
            for deps, term in result['coupled_terms']:
                print(f"  • [{', '.join(deps)}]: {term}")

        print(f"\n{'─' * 40}")
        print("VARIABLE DEPENDENCIES")
        print(f"{'─' * 40}")
        for var, deps in result['variable_dependencies'].items():
            if len(deps) > 1:
                other_deps = [d for d in deps if d != var]
                print(f"  {var} ↔ {', '.join(other_deps)}")
            else:
                print(f"  {var}: independent")

        if result['symmetries']:
            print(f"\n{'─' * 40}")
            print("DETECTED SYMMETRIES")
            print(f"{'─' * 40}")
            for sym in result['symmetries']:
                print(f"  • {sym}")

        print(f"\n{'─' * 40}")
        print("IMPROVEMENT SUGGESTIONS")
        print(f"{'─' * 40}")
        for imp in result['improvements']:
            print(f"  • {imp}")

        if result['transformations']:
            print(f"\n{'─' * 40}")
            print("TRANSFORMATION STEPS")
            print(f"{'─' * 40}")
            for t in result['transformations']:
                print(f"  {t}")

        print("\n" + "=" * 60)


# Convenience functions
def simplify_equation(equation: str, verbose: bool = False) -> str:
    """Quick simplification of an equation string."""
    config = SimplificationConfig(verbose=verbose)
    improver = EquationImprover(config)
    result = improver.improve(equation)
    return result['simplified']


def analyze_functional(equation: str) -> FunctionalAnalysis:
    """Analyze a functional/Lagrangian expression."""
    expr = parse_lagrangian(equation)
    analyzer = FunctionalAnalyzer()
    return analyzer.analyze(expr)


# Example usage and demonstration
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("EQUATION SIMPLIFICATION TOOL - DEMONSTRATION")
    print("=" * 60)

    # The user's equation
    test_equation = "L[ψ, σ, U] = F(ψ) + H(σ) + Γ(U; ψ)"

    print(f"\nAnalyzing: {test_equation}")

    improver = EquationImprover()
    improver.print_report(test_equation)

    # Additional examples
    print("\n\n" + "=" * 60)
    print("ADDITIONAL EXAMPLES")
    print("=" * 60)

    examples = [
        "L = F(x) + F(x) + G(y)",  # Should combine like terms
        "E = T(v) + V(x) + W(x, v)",  # Classical mechanics style
        "S[φ] = K(φ) + U(φ) + J(φ; θ)",  # Action functional
    ]

    for eq in examples:
        print(f"\n{'─' * 40}")
        result = improver.improve(eq)
        print(f"Original:   {eq}")
        print(f"Simplified: {result['simplified']}")
        print(f"Separable:  {result['is_separable']}")
        if result['improvements']:
            print(f"Key improvement: {result['improvements'][0]}")
