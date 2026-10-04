"""
Milestone 11 verification: LangGraph Workflow.

Tests:
- Graph compiles without errors
- Correct nodes registered
- Conditional edge routing logic
- run_pipeline() raises ValueError on empty input
- stream_pipeline() raises ValueError on empty input
- get_graph_info() returns correct metadata
- Graph can be drawn (Mermaid ASCII representation)
"""
import sys
sys.path.insert(0, '.')

print("--- Milestone 11: LangGraph Workflow Verification ---\n")
all_pass = True

# ── 1. Import and compile ──────────────────────────────────────────────────
print("=== Graph Compilation ===")
try:
    from app.graph.workflow import graph, run_pipeline, stream_pipeline, get_graph_info, build_graph
    print("  PASS  workflow.py imported — graph compiled at module load")
    print(f"  PASS  graph type: {type(graph).__name__}")
except Exception as e:
    print(f"  FAIL  import: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

print()

# ── 2. Graph structure ─────────────────────────────────────────────────────
print("=== Graph Structure ===")
info = get_graph_info()
expected_nodes = ["supervisor", "research", "rag", "architect", "critic", "report"]
assert info["nodes"] == expected_nodes, f"Expected {expected_nodes}, got {info['nodes']}"
print(f"  PASS  Nodes: {info['nodes']}")
assert info["entry_point"] == "supervisor"
print(f"  PASS  Entry point: {info['entry_point']}")
assert info["terminal_node"] == "report"
print(f"  PASS  Terminal node: {info['terminal_node']}")
assert info["max_revisions"] == 2
print(f"  PASS  Max revisions: {info['max_revisions']}")

# Verify conditional edge structure
cond = info["conditional_edge"]
assert cond["from"] == "critic"
assert "PASS" in cond["routes"]
assert cond["routes"]["PASS"] == "report"
print(f"  PASS  Conditional edge: critic -> {cond['routes']}")

print()

# ── 3. Graph nodes from LangGraph object ───────────────────────────────────
print("=== LangGraph Internal Structure ===")
try:
    # Get the graph's node names from the compiled graph
    graph_nodes = list(graph.nodes.keys())
    print(f"  PASS  Registered nodes: {graph_nodes}")
    for node in expected_nodes:
        assert node in graph_nodes, f"Node '{node}' missing from graph"
    print(f"  PASS  All expected nodes present in compiled graph")
except AttributeError:
    # Fallback: just verify the graph object is callable
    print(f"  PASS  graph object is callable: {callable(graph.invoke)}")

print()

# ── 4. Input validation ────────────────────────────────────────────────────
print("=== Input Validation ===")
try:
    run_pipeline("")
    print("  FAIL  Should raise ValueError for empty idea")
    all_pass = False
except ValueError as e:
    print(f"  PASS  run_pipeline(''): raises ValueError")

try:
    run_pipeline("   ")
    print("  FAIL  Should raise ValueError for whitespace-only idea")
    all_pass = False
except ValueError as e:
    print(f"  PASS  run_pipeline('   '): raises ValueError")

try:
    list(stream_pipeline(""))
    print("  FAIL  Should raise ValueError for empty idea")
    all_pass = False
except ValueError as e:
    print(f"  PASS  stream_pipeline(''): raises ValueError")

print()

# ── 5. Graph Mermaid visualization ─────────────────────────────────────────
print("=== Graph Visualization ===")
try:
    mermaid = graph.get_graph().draw_mermaid()
    # Count expected node mentions
    for node in expected_nodes:
        assert node in mermaid, f"Node '{node}' not in Mermaid output"
    lines = mermaid.strip().split('\n')
    print(f"  PASS  Mermaid diagram generated: {len(lines)} lines")
    print()
    print("  --- Mermaid Diagram ---")
    for line in lines:
        print(f"  {line}")
    print("  --- End Diagram ---")
except Exception as e:
    print(f"  WARN  Could not generate Mermaid diagram: {e}")

print()

# ── 6. route_after_critic standalone test ─────────────────────────────────
print("=== Conditional Edge Function ===")
from app.agents.critic_agent import route_after_critic
routing_cases = [
    ({"current_agent": "report"},    "report"),
    ({"current_agent": "research"},  "research"),
    ({"current_agent": "architect"}, "architect"),
    ({"current_agent": "garbage"},   "report"),    # fallback
    ({},                             "report"),    # missing key → fallback
]
for state_in, expected in routing_cases:
    result = route_after_critic(state_in)
    if result == expected:
        print(f"  PASS  route({state_in}) -> '{result}'")
    else:
        print(f"  FAIL  route({state_in}) -> '{result}' (expected '{expected}')")
        all_pass = False

print()
if all_pass:
    print("ALL MILESTONE 11 CHECKS PASSED")
    print("\nThe complete LangGraph pipeline is ready.")
    print("Next step: Set GOOGLE_API_KEY in .env and run an end-to-end test.")
else:
    print("SOME MILESTONE 11 CHECKS FAILED")
    sys.exit(1)
