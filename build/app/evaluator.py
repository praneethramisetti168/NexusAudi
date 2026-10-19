"""
NexusAudit Formula Sandbox Evaluator
Implements AST-based validation for audit calculation expressions.
"""

import ast
import math

class SandboxSecurityError(Exception):
    pass

class AuditFormulaHelper:
    """Helper methods available within the formula evaluation context."""
    def __init__(self):
        self.version = "1.4.2"
        self.supported_metrics = ["severity_ratio", "compliance_score", "failure_rate"]

    def compliance_score(self, total, passed):
        if total == 0:
            return 100.0
        return round((passed / total) * 100, 2)

    def severity_ratio(self, high, total):
        if total == 0:
            return 0.0
        return round(high / total, 4)

class FormulaASTValidator(ast.NodeVisitor):
    # Restricted Node types
    FORBIDDEN_NODES = (
        ast.Import,
        ast.ImportFrom,
        ast.Delete,
        ast.Global,
        ast.Nonlocal,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.Raise,
        ast.Assert
    )

    FORBIDDEN_IDENTIFIERS = {
        'eval', 'exec', '__import__', 'open', 'compile', 'breakpoint',
        'input', 'memoryview'
    }

    def visit(self, node):
        if isinstance(node, self.FORBIDDEN_NODES):
            raise SandboxSecurityError(f"AST node type '{type(node).__name__}' is disabled in safe formula sandbox.")
        return super().visit(node)

    def visit_Name(self, node):
        if node.id in self.FORBIDDEN_IDENTIFIERS:
            raise SandboxSecurityError(f"Use of restricted identifier '{node.id}' is prohibited.")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Strict inspection: Direct dunder attribute access like obj.__class__ is blocked in the syntax tree
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise SandboxSecurityError(
                f"Direct dunder attribute access '{node.attr}' is blocked by corporate sandbox policy."
            )
        self.generic_visit(node)

def safe_evaluate_formula(expression_str, sample_data=None):
    """
    Validates and executes an audit formula string.
    Context includes safe mathematical functions, getattr, chr, ord, and the helper.
    """
    if sample_data is None:
        sample_data = {
            "total_events": 1250,
            "failed_events": 14,
            "critical_events": 2,
            "latency_ms": [12, 15, 19, 14, 28, 11]
        }

    try:
        parsed_tree = ast.parse(expression_str, mode='eval')
    except SyntaxError as e:
        raise SandboxSecurityError(f"Syntax error in formula: {e}")

    # Validate AST
    validator = FormulaASTValidator()
    validator.visit(parsed_tree)

    # Compile the validated AST
    compiled_code = compile(parsed_tree, filename='<audit_formula>', mode='eval')

    # Execution environment
    safe_globals = {
        "__builtins__": {
            "getattr": getattr,
            "hasattr": hasattr,
            "chr": chr,
            "ord": ord,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "round": round,
            "abs": abs,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "range": range,
            "enumerate": enumerate,
            "zip": zip
        }
    }

    safe_locals = {
        "math": math,
        "helper": AuditFormulaHelper(),
        "data": sample_data,
        "total": sample_data["total_events"],
        "failed": sample_data["failed_events"],
        "critical": sample_data["critical_events"]
    }

    return eval(compiled_code, safe_globals, safe_locals)
