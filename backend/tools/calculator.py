"""
tools/calculator.py - Calculator Tool
=======================================
This tool lets the agent perform mathematical calculations safely.

The key design decision: we use Python's ast.literal_eval() and a
restricted evaluator instead of Python's built-in eval().

WHY NOT USE eval()?
  eval("2 + 2")  → works fine ✓
  eval("__import__('os').system('rm -rf /')")  → DANGEROUS! ✗
  
  eval() can execute ANY Python code, making it a security risk.
  Our safe evaluator only allows math operations.

HOW IT WORKS:
  1. Parse the expression into an Abstract Syntax Tree (AST)
  2. Walk the tree and only allow safe math nodes
  3. Evaluate the result
"""

import ast
import math
import operator
from typing import Union


# ============================================================
# SAFE MATH EVALUATOR
# ============================================================

# Allowed binary operations (two-number operations)
# e.g. 2 + 3, 10 / 4, 2 ** 8
SAFE_OPERATORS = {
    ast.Add: operator.add,        # Addition: +
    ast.Sub: operator.sub,        # Subtraction: -
    ast.Mult: operator.mul,       # Multiplication: *
    ast.Div: operator.truediv,    # Division: /
    ast.FloorDiv: operator.floordiv,  # Floor division: //
    ast.Mod: operator.mod,        # Modulo (remainder): %
    ast.Pow: operator.pow,        # Power/exponent: **
}

# Allowed unary operations (single-number operations)
# e.g. -5, +3
SAFE_UNARY_OPERATORS = {
    ast.USub: operator.neg,  # Negative: -5
    ast.UAdd: operator.pos,  # Positive: +5
}

# Allowed math functions from Python's math library
# e.g. sqrt(16), sin(0), log(100)
SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node: ast.AST) -> Union[int, float]:
    """
    Recursively evaluate an AST node using only safe math operations.
    Raises ValueError if any unsafe operation is detected.
    """
    # A plain number: 42, 3.14
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsafe value type: {type(node.value)}")

    # A named constant or function: pi, e, sqrt(...)
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable or function: '{node.id}'")

    # A function call: sqrt(16), round(3.7)
    elif isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function not allowed: '{func_name}'")
        func = SAFE_FUNCTIONS[func_name]
        args = [_safe_eval(arg) for arg in node.args]
        return func(*args)

    # A binary operation: 2 + 3, 10 * 4
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Operator not allowed: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        # Prevent division by zero
        if op_type == ast.Div and right == 0:
            raise ValueError("Division by zero is not allowed")
        return SAFE_OPERATORS[op_type](left, right)

    # A unary operation: -5, +3
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_UNARY_OPERATORS:
            raise ValueError(f"Unary operator not allowed: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return SAFE_UNARY_OPERATORS[op_type](operand)

    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


# ============================================================
# CALCULATOR TOOL CLASS
# ============================================================

class CalculatorTool:
    """
    A safe math calculator tool for the AI agent.
    
    The agent calls this tool when the user asks math questions like:
    - "What is 15% of 240?"
    - "Calculate the compound interest on 10000 at 5% for 3 years"
    - "What is sqrt(144) + 2^8?"
    
    Usage:
        calc = CalculatorTool()
        result = calc.run("2 + 2 * 10")
        # Returns: "Result: 22"
    """

    # Tool metadata — the agent uses this to decide when to use this tool
    name: str = "Calculator"
    description: str = (
        "Performs safe mathematical calculations. "
        "Supports: +, -, *, /, **, %, sqrt(), sin(), cos(), log(), "
        "round(), ceil(), floor(), and constants pi, e. "
        "Use this for any arithmetic or math problem."
    )

    def run(self, expression: str) -> str:
        """
        Evaluate a mathematical expression and return the result.
        
        Args:
            expression: A math expression string like "2 + 2" or "sqrt(144)"
            
        Returns:
            A formatted string with the result, or an error message
        """
        # Clean up the input — remove extra spaces and normalize
        expression = expression.strip()

        # Guard against empty input
        if not expression:
            return "Error: No expression provided. Please give me a math problem to solve."

        # Limit expression length to prevent abuse
        if len(expression) > 500:
            return "Error: Expression is too long. Please simplify it."

        try:
            # Step 1: Parse the expression into an Abstract Syntax Tree
            tree = ast.parse(expression, mode="eval")

            # Step 2: Safely evaluate the AST
            result = _safe_eval(tree.body)

            # Step 3: Format the result nicely
            # If it's a whole number, show without decimals: 4 not 4.0
            if isinstance(result, float) and result.is_integer():
                formatted_result = str(int(result))
            elif isinstance(result, float):
                # Round to 6 decimal places for readability
                formatted_result = f"{result:.6g}"
            else:
                formatted_result = str(result)

            return f"Result: {expression} = {formatted_result}"

        except ValueError as e:
            # Our safe evaluator rejected something
            return f"Calculation Error: {str(e)}"
        except SyntaxError:
            return (
                f"Syntax Error: '{expression}' is not a valid math expression. "
                "Example valid expressions: '2 + 3', 'sqrt(16)', '10 * (3 + 4)'"
            )
        except Exception as e:
            return f"Unexpected error calculating '{expression}': {str(e)}"

    def get_tool_info(self) -> dict:
        """Return tool metadata as a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "example_inputs": [
                "2 + 2",
                "15 * 240 / 100",
                "sqrt(144)",
                "2 ** 10",
                "round(3.14159, 2)"
            ]
        }
