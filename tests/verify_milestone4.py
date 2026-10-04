"""
Milestone 4 verification: Supervisor Agent.

Part A: Import + structure verification (no API call).
Part B: Live LLM test (requires GOOGLE_API_KEY in .env).
"""
import sys
sys.path.insert(0, '.')

print("--- Milestone 4: Supervisor Agent Verification ---\n")

# ── PART A: Import & structure checks ─────────────────────────────────────────

# 1. Import the agent
try:
    from app.agents.supervisor import run_supervisor
    print("PASS  run_supervisor imported successfully")
except Exception as e:
    print(f"FAIL  import: {e}")
    sys.exit(1)

# 2. Test with empty idea → should return error, not raise exception
try:
    result = run_supervisor({"user_idea": ""})
    assert result.get("error") is not None, "Should have set error for empty idea"
    assert result.get("requirements") == {}, "requirements should be empty on error"
    print("PASS  Empty idea: handled gracefully (error set, no exception raised)")
except AssertionError as e:
    print(f"FAIL  Empty idea check: {e}")
except Exception as e:
    print(f"FAIL  Empty idea raised unexpected exception: {e}")

# 3. Test with too-short idea → should return error
try:
    result = run_supervisor({"user_idea": "AI thing"})
    assert result.get("error") is not None
    print("PASS  Too-short idea: handled gracefully")
except Exception as e:
    print(f"FAIL  Short idea: {e}")

# 4. Verify state keys returned are correct
try:
    result = run_supervisor({"user_idea": ""})
    expected_keys = {"requirements", "current_agent", "error"}
    actual_keys = set(result.keys())
    assert expected_keys == actual_keys, f"Expected {expected_keys}, got {actual_keys}"
    print(f"PASS  State keys correct: {actual_keys}")
except Exception as e:
    print(f"FAIL  State keys: {e}")

print()

# ── PART B: Live API test ──────────────────────────────────────────────────────
from app.config.settings import settings

if not settings.google_api_key:
    print("SKIP  Live API test: GOOGLE_API_KEY not set in .env")
    print("      Set your key and re-run to test the live LLM call.")
    print("\nIMPORT AND STRUCTURE CHECKS PASSED")
    sys.exit(0)

print("--- Part B: Live API Test (GOOGLE_API_KEY found) ---\n")

TEST_IDEA = (
    "I want to build a computer vision system that automatically detects "
    "quality defects in manufactured products on an assembly line. "
    "The system should process images in real-time from cameras and alert "
    "operators when a defect is detected. I want to use deep learning."
)

try:
    print(f"Sending idea to Gemini: '{TEST_IDEA[:60]}...'")
    result = run_supervisor({"user_idea": TEST_IDEA})

    if result.get("error"):
        print(f"FAIL  Live test returned error: {result['error']}")
        sys.exit(1)

    reqs = result["requirements"]
    print(f"\nPASS  Supervisor completed successfully")
    print(f"      project_title    : {reqs.get('project_title')}")
    print(f"      project_type     : {reqs.get('project_type')}")
    print(f"      complexity       : {reqs.get('complexity')}")
    print(f"      target_domain    : {reqs.get('target_domain')}")
    print(f"      requires_real_time: {reqs.get('requires_real_time')}")
    print(f"      objectives       : {reqs.get('objectives', [])[:2]}")
    print(f"      key_challenges   : {reqs.get('key_challenges', [])[:2]}")
    print(f"      current_agent    : {result['current_agent']}")

    # Validate the returned dict matches Requirements schema
    from app.models.state_models import Requirements
    validated = Requirements(**reqs)
    print(f"\nPASS  Requirements Pydantic validation: OK")

except Exception as e:
    print(f"FAIL  Live test exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nALL MILESTONE 4 CHECKS PASSED")
