"""
app/tools/calculator.py

Safe math expression evaluator for the Architect Agent.

Used to compute:
- Dataset size estimates (e.g., "How many samples at 80/20 split?")
- Parameter counts (e.g., "How many params in a 12-layer transformer?")
- Training time estimates (e.g., "Hours per epoch at N samples, B batch size")
- Storage estimates (e.g., "Total GB for N images at 224x224 float32")

IMPORTANT: This uses Python's AST module — NOT eval() — so arbitrary code
cannot be injected. Only numeric literals and safe math operators are allowed.

Usage:
    from app.tools.calculator import calculate
    result = calculate("1000 * 0.8")          # → 800.0
    result = calculate("224 * 224 * 3 * 4")   # → 602112.0 (bytes per image)
"""

import ast
import math
import operator
from typing import Union

from app.utils.logger import get_logger, log_tool_call

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Allowed operators and functions
# ---------------------------------------------------------------------------
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,   # unary minus
    ast.UAdd: operator.pos,   # unary plus
}

_ALLOWED_FUNCTIONS = {
    "abs":   abs,
    "round": round,
    "min":   min,
    "max":   max,
    "sqrt":  math.sqrt,
    "log":   math.log,
    "log10": math.log10,
    "ceil":  math.ceil,
    "floor": math.floor,
}

_ALLOWED_CONSTANTS = {
    "pi":  math.pi,
    "e":   math.e,
    "inf": math.inf,
}


class CalculatorError(ValueError):
    """Raised when the expression is invalid or unsafe."""
    pass


def _evaluate_node(node: ast.AST) -> Union[int, float]:
    """
    Recursively evaluates an AST node.
    Raises CalculatorError for any unsupported node type.
    """
    # Numeric literal
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise CalculatorError(f"Unsupported literal type: {type(node.value).__name__}")

    # Named constant (pi, e, inf)
    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_CONSTANTS:
            return _ALLOWED_CONSTANTS[node.id]
        raise CalculatorError(
            f"Unknown name '{node.id}'. "
            f"Allowed: {list(_ALLOWED_CONSTANTS.keys())}"
        )

    # Binary operation (a + b, a * b, etc.)
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise CalculatorError(f"Unsupported operator: {op_type.__name__}")
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        try:
            return _ALLOWED_OPERATORS[op_type](left, right)
        except ZeroDivisionError:
            raise CalculatorError("Division by zero.")
        except OverflowError:
            raise CalculatorError("Result is too large (overflow).")

    # Unary operation (-x, +x)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise CalculatorError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _evaluate_node(node.operand)
        return _ALLOWED_OPERATORS[op_type](operand)

    # Function call (sqrt, round, etc.)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculatorError("Only simple function calls are allowed (e.g., sqrt(2)).")
        func_name = node.func.id
        if func_name not in _ALLOWED_FUNCTIONS:
            raise CalculatorError(
                f"Unknown function '{func_name}'. "
                f"Allowed: {list(_ALLOWED_FUNCTIONS.keys())}"
            )
        args = [_evaluate_node(arg) for arg in node.args]
        try:
            return _ALLOWED_FUNCTIONS[func_name](*args)
        except Exception as e:
            raise CalculatorError(f"Function error in {func_name}(): {e}")

    raise CalculatorError(
        f"Unsupported expression type: {type(node).__name__}. "
        "Only numeric arithmetic is allowed."
    )


def calculate(expression: str) -> dict:
    """
    Safely evaluates a math expression string.

    Args:
        expression: A string containing a math expression.
                    Examples: "224 * 224 * 3", "1000000 / 32", "sqrt(256)"

    Returns:
        A dict with keys:
            - "result" (float | None): The numeric result, or None on error.
            - "expression" (str): The original expression.
            - "success" (bool): Whether evaluation succeeded.
            - "error" (str | None): Error message if failed.
            - "formatted" (str): Human-readable result string.
    """
    log_tool_call(logger, "calculator", expression)

    expression = expression.strip()

    if not expression:
        return {
            "result": None,
            "expression": expression,
            "success": False,
            "error": "Empty expression.",
            "formatted": "Error: empty expression.",
        }

    try:
        # Parse the expression into an AST
        tree = ast.parse(expression, mode="eval")
        result = _evaluate_node(tree.body)

        # Format the result nicely
        if isinstance(result, float) and result.is_integer():
            formatted = f"{expression} = {int(result):,}"
            result = float(result)
        elif isinstance(result, float):
            formatted = f"{expression} = {result:,.4f}"
        else:
            formatted = f"{expression} = {result:,}"
            result = float(result)

        logger.info(f"[TOOL]  calculator: {formatted}")

        return {
            "result": result,
            "expression": expression,
            "success": True,
            "error": None,
            "formatted": formatted,
        }

    except SyntaxError:
        error_msg = f"Invalid syntax in expression: '{expression}'"
        logger.warning(f"[TOOL]  calculator error: {error_msg}")
        return {
            "result": None,
            "expression": expression,
            "success": False,
            "error": error_msg,
            "formatted": f"Error: {error_msg}",
        }
    except CalculatorError as e:
        logger.warning(f"[TOOL]  calculator error: {e}")
        return {
            "result": None,
            "expression": expression,
            "success": False,
            "error": str(e),
            "formatted": f"Error: {e}",
        }
    except Exception as e:
        logger.error(f"[ERR]   calculator unexpected error: {e}")
        return {
            "result": None,
            "expression": expression,
            "success": False,
            "error": f"Unexpected error: {e}",
            "formatted": f"Error: {e}",
        }
