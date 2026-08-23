"""
Structural guarantee: the compliance and risk engines cannot depend on the
LLM client, even indirectly. This is checked by static import inspection,
not just code review — if someone adds `from app.services.llm_client import ...`
inside evaluator.py or scoring.py, this test fails the build.
"""
import ast
from pathlib import Path

ENGINE_FILES = [
    "app/services/rules/evaluator.py",
    "app/services/rules/schema.py",
    "app/services/risk/scoring.py",
]

FORBIDDEN_SUBSTRING = "llm_client"


def _imports_forbidden_module(path: Path) -> bool:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and FORBIDDEN_SUBSTRING in node.module:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if FORBIDDEN_SUBSTRING in alias.name:
                    return True
    return False


def test_rule_and_risk_engines_have_zero_llm_dependency():
    backend_root = Path(__file__).resolve().parents[1]
    for rel_path in ENGINE_FILES:
        full_path = backend_root / rel_path
        assert full_path.exists(), f"expected engine file missing: {rel_path}"
        assert not _imports_forbidden_module(full_path), (
            f"{rel_path} must never import the LLM client — compliance/risk "
            "verdicts must remain deterministic and LLM-independent"
        )
