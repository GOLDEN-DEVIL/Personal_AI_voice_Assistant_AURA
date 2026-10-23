"""Safe AST-based arithmetic calculator.

Evaluates mathematical expressions without using `eval` or `exec`.
Supports basic arithmetic and standard math functions while strictly
blocking arbitrary code, attribute lookups, loops, and statement execution.
"""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any, Callable

# Allowed binary operators
_BIN_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Allowed unary operators
_UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Allowed math functions and constants
_ALLOWED_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "ceil": math.ceil,
    "floor": math.floor,
}

_ALLOWED_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}


class CalculatorError(ValueError):
    """Raised for invalid or disallowed calculator input."""


def _eval_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise CalculatorError(f"Unsupported constant type: {type(node.value).__name__}")

    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_CONSTANTS:
            return _ALLOWED_CONSTANTS[node.id]
        raise CalculatorError(f"Unknown or unsupported identifier: '{node.id}'")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _UNARY_OPS:
            operand = _eval_node(node.operand)
            return _UNARY_OPS[op_type](operand)
        raise CalculatorError(f"Unsupported unary operator: {op_type.__name__}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _BIN_OPS:
            left = _eval_node(node.left)
            right = _eval_node(node.right)

            # Guard against dangerous or unbounded exponentiation
            if op_type is ast.Pow:
                if isinstance(right, (int, float)) and abs(right) > 1000:
                    raise CalculatorError("Exponent too large (maximum exponent magnitude is 1000).")

            # Guard against division by zero
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise CalculatorError("Division by zero is not allowed.")

            try:
                return _BIN_OPS[op_type](left, right)
            except OverflowError:
                raise CalculatorError("Calculation result exceeded numerical bounds (overflow).")

        raise CalculatorError(f"Unsupported operator: {op_type.__name__}")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculatorError("Complex function calls are not permitted.")
        func_name = node.func.id
        if func_name not in _ALLOWED_FUNCTIONS:
            raise CalculatorError(f"Function '{func_name}' is not in the safe math allowlist.")

        func = _ALLOWED_FUNCTIONS[func_name]
        args = [_eval_node(arg) for arg in node.args]
        try:
            return func(*args)
        except Exception as err:
            raise CalculatorError(f"Error evaluating {func_name}(): {err}") from err

    raise CalculatorError(f"Disallowed expression syntax: {type(node).__name__}")


def normalize_verbal_expression(expr: str) -> str:
    """Normalize spoken English arithmetic phrases into standard math symbols.

    Converts phrases like '5 times 5', '10 divided by 2', '5 x 5', '4 into 6',
    '3 squared' into valid Python syntax before AST parsing.
    """
    cleaned = expr.strip()
    replacements: list[tuple[str, str]] = [
        (r"\bmultiplied\s+by\b", "*"),
        (r"\btimes\b", "*"),
        (r"\binto\b", "*"),
        (r"\bdivided\s+by\b", "/"),
        (r"\bover\b", "/"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\bto\s+the\s+power\s+of\b", "**"),
        (r"\bsquared\b", "** 2"),
        (r"\bcubed\b", "** 3"),
        (r"(?<=\d)\s*[xX]\s*(?=\d)", " * "),
        (r"\b[xX]\b", "*"),
    ]
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned


def evaluate_expression(expression: str) -> str:
    """Safely parse and calculate a mathematical expression string.

    Returns a friendly string representation of the result or error.
    """
    expr_clean = normalize_verbal_expression(expression)
    if not expr_clean:
        return "Error: Please provide a mathematical expression (e.g., 'calc 42 * 2' or 'calc sqrt(16)')."

    try:
        parsed_ast = ast.parse(expr_clean, mode="eval")
        result = _eval_node(parsed_ast)

        # Clean integer display if float has no fractional part
        if isinstance(result, float) and result.is_integer():
            return f"Result: {int(result)}"
        return f"Result: {result}"
    except SyntaxError:
        return f"Syntax Error: Could not parse expression '{expression}'. Please check brackets and operators."
    except CalculatorError as err:
        return f"Calculator Error: {err}"
    except Exception as err:
        return f"Calculation Error: {err}"
