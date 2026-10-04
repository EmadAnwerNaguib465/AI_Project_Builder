"""
Milestone 6 verification: Research Agent.

Part A: Import + structure verification (no API call).
Part B: Live LLM test (requires GOOGLE_API_KEY in .env).
"""
import sys
sys.path.insert(0, '.')

print("--- Milestone 6: Research Agent Verification ---\n")

all_pass = True

# ── PART A: Import & structure checks ────────────────────────────────────────

# 1. Import
try:
    from app.agents.research_agent import run_research_agent
    print("PASS  run_research_agent imported successfully")
except Exception as e:
    print(f"FAIL  import: {e}")
    sys.exit(1)

# 2. Empty requirements -> graceful error
try:
    result = run_research_agent({"requirements": {}})
    assert result.get("error") is not None
    assert result.get("research_results") == {}
    assert result.get("sources") == []
    print("PASS  Empty requirements: handled gracefully")
except Exception as e:
    print(f"FAIL  Empty requirements: {e}")
    all_pass = False

# 3. Verify returned keys
try:
    result = run_research_agent({"requirements": {}})
    expected = {"research_results", "sources", "current_agent", "error"}
    assert set(result.keys()) == expected, f"Got: {set(result.keys())}"
    print(f"PASS  State keys correct: {set(result.keys())}")
except Exception as e:
    print(f"FAIL  State keys: {e}")
    all_pass = False

# 4. current_agent must be 'research' on error, 'rag' on success
result = run_research_agent({"requirements": {}})
assert result["current_agent"] == "research", f"Expected 'research' on error, got '{result['current_agent']}'"
print(f"PASS  current_agent='research' on error (will be 'rag' on success)")

print()

# ── PART B: Live API test ────────────────────────────────────────────────────
from app.config.settings import settings

if not settings.google_api_key:
    print("SKIP  Live API test: GOOGLE_API_KEY not set in .env")
    print("      Set your key and re-run to test the live LLM call.")
    if all_pass:
        print("\nIMPORT AND STRUCTURE CHECKS PASSED")
    sys.exit(0 if all_pass else 1)

print("--- Part B: Live API Test (GOOGLE_API_KEY found) ---\n")

# Simulate state after Supervisor ran
MOCK_REQUIREMENTS = {
    "project_title": "Manufacturing Defect Detection System",
    "project_type": "computer_vision",
    "target_domain": "manufacturing",
    "objectives": [
        "Detect surface defects in manufactured parts with >95% accuracy",
        "Process images in real-time at 30 FPS",
        "Alert operators within 500ms of defect detection",
    ],
    "constraints": ["Limited GPU budget", "Small labeled dataset (< 2000 images)"],
    "key_challenges": [
        "Limited labeled training data",
        "Real-time inference requirement",
        "High class imbalance (few defects vs many good parts)",
    ],
    "complexity": "medium",
    "requires_rag": False,
    "requires_real_time": True,
}

try:
    print("Calling Research Agent with mock requirements...")
    result = run_research_agent({"requirements": MOCK_REQUIREMENTS})

    if result.get("error"):
        print(f"FAIL  Live test returned error: {result['error']}")
        sys.exit(1)

    rr = result["research_results"]
    sources = result["sources"]

    print(f"\nPASS  Research Agent completed")
    print(f"      summary          : {rr.get('summary', '')[:100]}...")
    print(f"      key_findings     : {len(rr.get('key_findings', []))} findings")
    print(f"      dataset_hints    : {rr.get('dataset_hints', [])}")
    print(f"      model_hints      : {rr.get('model_hints', [])}")
    print(f"      recommended_approaches: {len(rr.get('recommended_approaches', []))}")
    print(f"      sources          : {len(sources)} total")
    print(f"      current_agent    : {result['current_agent']}")

    # Validate with Pydantic
    from app.models.research_models import ResearchResult
    validated = ResearchResult(**rr)
    print(f"\nPASS  ResearchResult Pydantic validation: OK")
    assert result["current_agent"] == "rag", f"Expected 'rag', got '{result['current_agent']}'"
    print(f"PASS  Routing: current_agent correctly set to 'rag'")

except Exception as e:
    print(f"FAIL  Live test exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nALL MILESTONE 6 CHECKS PASSED")
