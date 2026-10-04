"""
Milestones 8-10 verification: Architect, Critic, Report agents.
Import checks + state contract validation. No live API calls.
"""
import sys
sys.path.insert(0, '.')

print("--- Milestones 8-10: Agent Import & Contract Verification ---\n")
all_pass = True

# ── Import checks ─────────────────────────────────────────────────────────────
print("=== Import Checks ===")
imports = [
    ("app.agents.architect_agent", "run_architect_agent"),
    ("app.agents.critic_agent",    "run_critic_agent, route_after_critic"),
    ("app.agents.report_agent",    "run_report_agent"),
    ("app.rag.embeddings",         "get_embedding_function"),  # updated import
    ("app.rag.vectorstore",        "build_vectorstore"),        # updated import
]
for mod, names in imports:
    try:
        __import__(mod, fromlist=[names])
        print(f"  PASS  {mod}")
    except Exception as e:
        print(f"  FAIL  {mod}: {e}")
        all_pass = False

print()

# ── Architect Agent state contract ────────────────────────────────────────────
print("=== Architect Agent Contract ===")
from app.agents.architect_agent import run_architect_agent

# Empty requirements -> graceful error
result = run_architect_agent({"requirements": {}})
assert result.get("error") is not None
assert result.get("architecture") == {}
assert result.get("dataset_strategy") == {}
assert result.get("model_strategy") == {}
expected_keys = {"architecture", "dataset_strategy", "model_strategy", "current_agent", "error"}
assert set(result.keys()) == expected_keys, f"Keys: {set(result.keys())}"
print(f"  PASS  Empty state: graceful error, correct keys")
print(f"  PASS  State keys: {expected_keys}")

print()

# ── Critic Agent state contract ───────────────────────────────────────────────
print("=== Critic Agent Contract ===")
from app.agents.critic_agent import run_critic_agent, route_after_critic

# Missing prerequisites -> graceful error
result = run_critic_agent({"requirements": {}, "architecture": {}})
assert result.get("error") is not None
expected_keys = {"critic_feedback", "revision_count", "revision_target", "current_agent", "error"}
assert set(result.keys()) == expected_keys
print(f"  PASS  Empty state: graceful error, correct keys")

# route_after_critic returns correct node names
for agent, expected in [("report", "report"), ("research", "research"), ("architect", "architect"), ("unknown", "report")]:
    route = route_after_critic({"current_agent": agent})
    assert route == expected, f"Expected {expected}, got {route}"
    print(f"  PASS  route_after_critic(current_agent='{agent}') -> '{route}'")

print()

# ── Report Agent state contract ───────────────────────────────────────────────
print("=== Report Agent Contract ===")
from app.agents.report_agent import run_report_agent

# Missing fields -> graceful error
result = run_report_agent({"requirements": {}, "architecture": {}})
assert result.get("error") is not None
expected_keys = {"final_report", "current_agent", "error"}
assert set(result.keys()) == expected_keys
print(f"  PASS  Empty state: graceful error, correct keys")
assert result["current_agent"] == "report"
print(f"  PASS  current_agent='report' on error (will be 'done' on success)")

print()

# ── Embedding/Vectorstore updated imports ─────────────────────────────────────
print("=== Updated Package Imports ===")
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    print("  PASS  langchain_huggingface.HuggingFaceEmbeddings available")
except ImportError as e:
    print(f"  FAIL  langchain_huggingface: {e}")
    all_pass = False

try:
    from langchain_chroma import Chroma
    print("  PASS  langchain_chroma.Chroma available")
except ImportError as e:
    print(f"  FAIL  langchain_chroma: {e}")
    all_pass = False

print()
if all_pass:
    print("ALL MILESTONES 8-10 CHECKS PASSED")
else:
    print("SOME CHECKS FAILED - review output above")
    sys.exit(1)
