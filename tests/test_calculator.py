"""Unit tests for safe calculator."""

from aura.tools.calculator import evaluate_expression


def test_basic_arithmetic():
    assert evaluate_expression("2 + 2") == "Result: 4"
    assert evaluate_expression("10 - 4") == "Result: 6"
    assert evaluate_expression("7 * 8") == "Result: 56"
    assert evaluate_expression("100 / 4") == "Result: 25"
    assert evaluate_expression("7 // 2") == "Result: 3"
    assert evaluate_expression("10 % 3") == "Result: 1"
    assert evaluate_expression("2 ** 3") == "Result: 8"


def test_operator_precedence_and_parentheses():
    assert evaluate_expression("2 + 3 * 4") == "Result: 14"
    assert evaluate_expression("(2 + 3) * 4") == "Result: 20"
    assert evaluate_expression("((10 - 2) * 3) / 4") == "Result: 6"


def test_math_functions_and_constants():
    assert evaluate_expression("sqrt(16)") == "Result: 4"
    assert evaluate_expression("abs(-42)") == "Result: 42"
    assert evaluate_expression("round(3.14159, 2)") == "Result: 3.14"
    assert "3.14" in evaluate_expression("pi")
    assert "2.71" in evaluate_expression("e")


def test_division_by_zero():
    res = evaluate_expression("10 / 0")
    assert "Division by zero" in res

    res_mod = evaluate_expression("10 % 0")
    assert "Division by zero" in res_mod


def test_large_exponent_blocked():
    res = evaluate_expression("2 ** 10000")
    assert "Exponent too large" in res


def test_security_arbitrary_code_injection_blocked():
    # Attempt to call builtins / imports
    assert "disallowed" in evaluate_expression("__import__('os').system('dir')").lower() or "error" in evaluate_expression("__import__('os').system('dir')").lower()
    assert "disallowed" in evaluate_expression("open('secret.txt')").lower() or "unknown" in evaluate_expression("open('secret.txt')").lower() or "error" in evaluate_expression("open('secret.txt')").lower()
    assert "syntax" in evaluate_expression("import os").lower() or "disallowed" in evaluate_expression("import os").lower()
    assert "disallowed" in evaluate_expression("(1).__class__").lower() or "syntax" in evaluate_expression("(1).__class__").lower()


def test_empty_and_syntax_error():
    assert "Error:" in evaluate_expression("")
    assert "Syntax Error:" in evaluate_expression("2 +* 5")


def test_verbal_math_expressions():
    assert evaluate_expression("5 times 5") == "Result: 25"
    assert evaluate_expression("5 into 5") == "Result: 25"
    assert evaluate_expression("5 x 5") == "Result: 25"
    assert evaluate_expression("10 plus 15") == "Result: 25"
    assert evaluate_expression("30 minus 5") == "Result: 25"
    assert evaluate_expression("100 divided by 4") == "Result: 25"
    assert evaluate_expression("5 squared") == "Result: 25"
    assert evaluate_expression("2 to the power of 5") == "Result: 32"

