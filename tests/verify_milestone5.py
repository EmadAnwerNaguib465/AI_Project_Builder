"""
Milestone 5 verification: Tools + Search Service.

Tests:
- calculator: math evaluation, safe failure cases
- web_search: graceful no-key handling
- dataset_search: HF API or curated fallback
- search_service: combined orchestration
"""
import sys
sys.path.insert(0, '.')

print("--- Milestone 5: Tools + Search Service Verification ---\n")

all_pass = True

# ── 1. Calculator ─────────────────────────────────────────────────────────────
print("=== Calculator ===")
from app.tools.calculator import calculate

calc_cases = [
    ("224 * 224 * 3",          150528.0, True),
    ("1000000 / 32",           31250.0,   True),
    ("2 ** 10",                1024.0,    True),
    ("sqrt(256)",              16.0,      True),
    ("round(3.14159, 2)",      3.14,      True),
    ("100 * 0.8",              80.0,      True),
    ("",                       None,      False),   # empty → error
    ("import os",              None,      False),   # code injection → error
    ("1 / 0",                  None,      False),   # div by zero → error
]

for expr, expected, should_succeed in calc_cases:
    r = calculate(expr)
    if should_succeed:
        if r["success"] and abs(r["result"] - expected) < 0.001:
            print(f"  PASS  calculate('{expr}') = {r['result']}")
        else:
            print(f"  FAIL  calculate('{expr}'): success={r['success']}, result={r['result']}, expected={expected}, error={r['error']}")
            all_pass = False
    else:
        if not r["success"]:
            print(f"  PASS  calculate('{expr}') -> correctly failed: {r['error'][:60]}")
        else:
            print(f"  FAIL  calculate('{expr}') -> should have failed but returned {r['result']}")
            all_pass = False

print()

# ── 2. Web Search (no Tavily key) ─────────────────────────────────────────────
print("=== Web Search ===")
from app.tools.web_search import web_search

resp = web_search("computer vision defect detection")
if not resp.success:
    print(f"  PASS  web_search without API key: graceful failure")
    print(f"        Error: {resp.error[:80]}")
    formatted = resp.to_formatted_string()
    assert "no results" in formatted.lower() or "not configured" in formatted.lower()
    print(f"  PASS  to_formatted_string(): returns safe message")
    sources = resp.get_sources()
    assert sources == []
    print(f"  PASS  get_sources(): returns empty list")
elif resp.success:
    # Has Tavily key configured
    print(f"  PASS  web_search with API key: {len(resp.results)} results returned")
    print(f"        First result: {resp.results[0].title[:60]}")

print()

# ── 3. Dataset Search ─────────────────────────────────────────────────────────
print("=== Dataset Search ===")
from app.tools.dataset_search import dataset_search

for ptype in ["computer_vision", "nlp", "rag", "recommendation"]:
    ds_resp = dataset_search(project_type=ptype, domain="", max_results=3)
    if len(ds_resp.datasets) >= 1:
        names = [d.name for d in ds_resp.datasets[:3]]
        print(f"  PASS  dataset_search('{ptype}'): {len(ds_resp.datasets)} datasets [{ds_resp.source}]")
        print(f"        -> {', '.join(names)}")
    else:
        print(f"  FAIL  dataset_search('{ptype}'): returned 0 datasets")
        all_pass = False

# Test formatted string
ds_resp = dataset_search(project_type="nlp", domain="healthcare")
fmt = ds_resp.to_formatted_string()
assert len(fmt) > 50
print(f"  PASS  to_formatted_string(): {len(fmt)} chars")

print()

# ── 4. Search Service ─────────────────────────────────────────────────────────
print("=== Search Service ===")
from app.services.search_service import SearchService, search_service

# Test with mock requirements
mock_requirements = {
    "project_title": "Defect Detection CV System",
    "project_type": "computer_vision",
    "target_domain": "manufacturing",
    "objectives": ["Detect defects with >95% accuracy"],
    "key_challenges": ["Limited labeled data", "Real-time inference"],
}

try:
    web_str, dataset_str, sources = search_service.run_research_search(
        requirements=mock_requirements,
        max_web_results=3,
        max_dataset_results=3,
    )
    print(f"  PASS  run_research_search(): completed")
    print(f"        web_str length    : {len(web_str)} chars")
    print(f"        dataset_str length: {len(dataset_str)} chars")
    print(f"        sources collected : {len(sources)}")
    assert isinstance(web_str, str) and len(web_str) > 10
    assert isinstance(dataset_str, str) and len(dataset_str) > 10
    assert isinstance(sources, list)
    print(f"  PASS  Return types all correct")
except Exception as e:
    print(f"  FAIL  run_research_search(): {e}")
    import traceback
    traceback.print_exc()
    all_pass = False

# Test query builder
query = SearchService._build_web_query(
    project_title="Sentiment Analysis",
    project_type="nlp",
    domain="customer reviews",
    objectives=["Classify sentiment"],
    challenges=["Sarcasm detection"],
)
assert "nlp" in query.lower() or "natural language" in query.lower() or "best practices" in query.lower()
print(f"  PASS  _build_web_query(): '{query}'")

print()

# ── Summary ───────────────────────────────────────────────────────────────────
if all_pass:
    print("ALL MILESTONE 5 CHECKS PASSED")
else:
    print("SOME MILESTONE 5 CHECKS FAILED - review output above")
    sys.exit(1)
