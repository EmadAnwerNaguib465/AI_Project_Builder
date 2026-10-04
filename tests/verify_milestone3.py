"""
Milestone 3 verification: test LLM service imports and prompt loading.
Does NOT make real API calls (no key required for this test).
"""
import sys
sys.path.insert(0, '.')

print("--- Milestone 3: LLM Service + Prompts Verification ---\n")

# 1. Test LLM service imports cleanly
try:
    from app.services.llm_service import LLMService, llm_service
    print("PASS  LLMService imported")
    print(f"      llm_service singleton: {type(llm_service).__name__}")
except Exception as e:
    print(f"FAIL  LLMService import: {e}")
    sys.exit(1)

# 2. Test that prompt loading works for all 6 prompts
prompts = ["supervisor", "researcher", "rag", "architect", "critic", "report"]
all_pass = True
for name in prompts:
    try:
        content = LLMService.load_prompt(name)
        word_count = len(content.split())
        print(f"PASS  Prompt '{name}': {word_count} words, {len(content)} chars")
    except Exception as e:
        print(f"FAIL  Prompt '{name}': {e}")
        all_pass = False

print()

# 3. Test format_prompt works
try:
    template = "Hello {name}, your project is {project}."
    formatted = LLMService.format_prompt(template, name="User", project="AI Builder")
    assert formatted == "Hello User, your project is AI Builder."
    print("PASS  format_prompt: substitution works correctly")
except Exception as e:
    print(f"FAIL  format_prompt: {e}")
    all_pass = False

# 4. Test missing placeholder raises ValueError
try:
    LLMService.format_prompt("Hello {name}", missing_key="oops")
    print("FAIL  format_prompt: should have raised ValueError for missing placeholder")
    all_pass = False
except ValueError:
    print("PASS  format_prompt: raises ValueError for missing placeholder")

# 5. Test LLM lazy init (no API key set) raises clear error
try:
    service = LLMService()
    # Temporarily clear key
    import os
    original_key = os.environ.get("GOOGLE_API_KEY", "")
    os.environ.pop("GOOGLE_API_KEY", None)

    # Patch settings to simulate missing key
    from app.config.settings import settings
    original_setting = settings.google_api_key
    object.__setattr__(settings, 'google_api_key', '')

    try:
        service._get_llm()
        print("FAIL  LLMService: should raise ValueError for missing API key")
        all_pass = False
    except ValueError as e:
        print(f"PASS  LLMService: raises clear ValueError when GOOGLE_API_KEY missing")
    finally:
        object.__setattr__(settings, 'google_api_key', original_setting)
        if original_key:
            os.environ["GOOGLE_API_KEY"] = original_key
except Exception as e:
    print(f"WARN  Could not test missing key scenario: {e}")

print()

# 6. Verify prompt placeholders exist in each prompt
print("--- Checking prompt placeholders ---")
placeholder_checks = {
    "supervisor": ["{user_idea}"],
    "researcher": ["{project_title}", "{web_search_results}", "{dataset_search_results}"],
    "rag": ["{project_title}", "{retrieved_passages}", "{top_k}"],
    "architect": ["{project_title}", "{research_summary}", "{retrieved_context}"],
    "critic": ["{project_title}", "{revision_count}", "{max_revisions}"],
    "report": ["{user_idea}", "{sources}", "{revision_count}"],
}
for name, placeholders in placeholder_checks.items():
    content = LLMService.load_prompt(name)
    for ph in placeholders:
        if ph in content:
            print(f"PASS  {name}: contains {ph}")
        else:
            print(f"FAIL  {name}: MISSING placeholder {ph}")
            all_pass = False

print()
if all_pass:
    print("ALL MILESTONE 3 CHECKS PASSED")
else:
    print("SOME MILESTONE 3 CHECKS FAILED - review output above")
    sys.exit(1)
