"""
app.py — AI Project Builder: Streamlit User Interface

Multi-Agent AI Project Planning System
Built with LangGraph, Gemini 2.0 Flash, ChromaDB, and Tavily.

Run:
    streamlit run app.py
"""

import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# ── Page config — MUST be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="AI Project Builder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Dark glassmorphism theme ─────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Google Font ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  /* ── Root variables ── */
  :root {
    --bg-primary:    #0D1117;
    --bg-secondary:  #161B22;
    --bg-card:       rgba(255,255,255,0.04);
    --border:        rgba(255,255,255,0.08);
    --accent-blue:   #6366F1;
    --accent-purple: #8B5CF6;
    --accent-cyan:   #22D3EE;
    --accent-green:  #10B981;
    --accent-amber:  #F59E0B;
    --accent-red:    #EF4444;
    --text-primary:  #F1F5F9;
    --text-secondary:#94A3B8;
    --text-muted:    #64748B;
    --gradient-1:    linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #22D3EE 100%);
    --gradient-2:    linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
  }

  /* ── Global background ── */
  .stApp, .main, [data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
  }

  /* ── Hide default header decoration ── */
  header[data-testid="stHeader"] { background: transparent !important; }
  #MainMenu, footer { display: none !important; }

  /* ── Hero banner ── */
  .hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #0f0c29 40%, #141832 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 48px 40px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }
  .hero-banner::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.12) 0%, transparent 50%);
    pointer-events: none;
  }
  .hero-title {
    font-size: 3rem; font-weight: 800;
    background: linear-gradient(135deg, #A5B4FC, #C4B5FD, #67E8F9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0; line-height: 1.1;
  }
  .hero-subtitle {
    font-size: 1.1rem; color: var(--text-secondary); margin: 0;
    font-weight: 400; letter-spacing: 0.01em;
  }
  .badge {
    display: inline-block; padding: 4px 12px; border-radius: 99px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em;
    border: 1px solid; margin-right: 8px; margin-top: 16px;
  }
  .badge-blue   { color: #818CF8; border-color: rgba(129,140,248,0.4); background: rgba(99,102,241,0.1); }
  .badge-purple { color: #C4B5FD; border-color: rgba(196,181,253,0.4); background: rgba(139,92,246,0.1); }
  .badge-cyan   { color: #67E8F9; border-color: rgba(103,232,249,0.4); background: rgba(34,211,238,0.1); }
  .badge-green  { color: #6EE7B7; border-color: rgba(110,231,183,0.4); background: rgba(16,185,129,0.1); }

  /* ── Glass cards ── */
  .glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(12px);
    transition: border-color 0.2s ease, transform 0.2s ease;
    margin-bottom: 16px;
  }
  .glass-card:hover { border-color: rgba(99,102,241,0.4); }

  /* ── Section headers ── */
  .section-header {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--accent-blue);
    margin: 0 0 8px 0;
  }
  .section-title {
    font-size: 1.4rem; font-weight: 700; color: var(--text-primary);
    margin: 0 0 16px 0;
  }

  /* ── Metric cards ── */
  .metric-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }
  .metric-value {
    font-size: 2rem; font-weight: 800;
    background: var(--gradient-1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .metric-label { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }

  /* ── Progress steps ── */
  .step-item {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 12px 16px; border-radius: 10px; margin-bottom: 8px;
    border: 1px solid var(--border);
    transition: all 0.3s ease;
  }
  .step-pending  { background: rgba(255,255,255,0.02); opacity: 0.5; }
  .step-running  { background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.4); animation: pulse 1.5s infinite; }
  .step-done     { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.3); }
  .step-error    { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.3); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.7} }
  .step-icon { font-size: 1.2rem; margin-top: 2px; min-width: 24px; }
  .step-name { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
  .step-desc { font-size: 0.8rem; color: var(--text-secondary); }

  /* ── Report sections ── */
  .report-section {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
  }
  .report-label {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;
  }

  /* ── Tags / chips ── */
  .chip {
    display: inline-block; padding: 4px 12px; border-radius: 99px;
    background: rgba(99,102,241,0.12); color: #A5B4FC;
    border: 1px solid rgba(99,102,241,0.25); font-size: 0.78rem;
    margin: 3px; font-weight: 500;
  }
  .chip-green { background: rgba(16,185,129,0.1); color:#6EE7B7; border-color:rgba(16,185,129,0.25); }
  .chip-amber { background: rgba(245,158,11,0.1); color:#FCD34D; border-color:rgba(245,158,11,0.25); }
  .chip-red   { background: rgba(239,68,68,0.1);  color:#FCA5A5; border-color:rgba(239,68,68,0.25);  }

  /* ── Roadmap steps ── */
  .roadmap-item {
    display: flex; gap: 16px; align-items: flex-start;
    padding: 12px 0; border-bottom: 1px solid var(--border);
  }
  .roadmap-item:last-child { border-bottom: none; }
  .roadmap-num {
    min-width: 28px; height: 28px; border-radius: 50%;
    background: var(--gradient-1); display: flex;
    align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 700; color: white;
    flex-shrink: 0; margin-top: 2px;
  }
  .roadmap-text { color: var(--text-primary); font-size: 0.9rem; line-height: 1.5; }

  /* ── Risk items ── */
  .risk-item {
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.2);
    color: var(--text-primary); font-size: 0.87rem; line-height: 1.5;
  }

  /* ── Source links ── */
  .source-item {
    padding: 8px 14px; border-radius: 8px; margin-bottom: 6px;
    background: rgba(255,255,255,0.03); border: 1px solid var(--border);
    font-size: 0.82rem; word-break: break-all;
  }
  .source-item a { color: var(--accent-cyan); text-decoration: none; }
  .source-item a:hover { text-decoration: underline; }

  /* ── Streamlit widget overrides ── */
  .stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important; color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important;
  }
  .stTextArea textarea:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
  }
  .stButton > button {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 0.95rem !important; padding: 0.6rem 2rem !important;
    transition: all 0.2s ease !important; font-family: 'Inter', sans-serif !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.4) !important;
  }
  .stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important; border-radius: 12px !important;
    gap: 4px !important; padding: 4px !important;
    border: 1px solid var(--border) !important;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; color: var(--text-secondary) !important;
    font-weight: 500 !important; font-family: 'Inter', sans-serif !important;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(99,102,241,0.2) !important;
    color: var(--text-primary) !important;
  }
  div[data-testid="stMarkdownContainer"] p { color: var(--text-primary); }
  .stDownloadButton > button {
    background: rgba(16,185,129,0.15) !important;
    border: 1px solid rgba(16,185,129,0.4) !important;
    color: #6EE7B7 !important;
  }
  .stDownloadButton > button:hover {
    background: rgba(16,185,129,0.25) !important;
    box-shadow: 0 4px 16px rgba(16,185,129,0.2) !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state initialization ───────────────────────────────────────────────
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = "idle"   # idle | running | complete | error
if "final_state" not in st.session_state:
    st.session_state.final_state = None
if "agent_log" not in st.session_state:
    st.session_state.agent_log = []
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None

# ── Agent metadata ─────────────────────────────────────────────────────────────
AGENTS = [
    ("supervisor", "🧠", "Requirements Analysis",  "Parsing your project idea into structured requirements"),
    ("research",   "🔍", "Research",               "Searching web and discovering relevant datasets"),
    ("rag",        "📚", "Knowledge Retrieval",    "Querying curated AI/ML knowledge base"),
    ("architect",  "🏗️", "Architecture Design",    "Designing system architecture, dataset & model strategy"),
    ("critic",     "⚖️", "Quality Validation",     "Validating plan completeness and feasibility"),
    ("report",     "📋", "Report Generation",      "Compiling comprehensive final project plan"),
]
AGENT_NAMES = {a[0] for a in AGENTS}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 24px 0;'>
      <div style='font-size:2.5rem;'>🤖</div>
      <div style='font-weight:700; font-size:1.05rem; color:#F1F5F9; margin-top:8px;'>AI Project Builder</div>
      <div style='font-size:0.78rem; color:#64748B;'>Multi-Agent Planning System</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**⚙️ System**", unsafe_allow_html=False)

    # Check API keys
    from app.config.settings import settings
    from app.rag.vectorstore import get_vector_count

    gemini_ok  = bool(settings.google_api_key)
    openai_ok  = bool(settings.openai_api_key)
    tavily_ok  = bool(settings.tavily_api_key)
    vector_ct  = get_vector_count()

    def status_row(label, ok, detail=""):
        icon = "🟢" if ok else "🔴"
        color = "#6EE7B7" if ok else "#FCA5A5"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<span>{icon}</span>'
            f'<span style="color:{color};font-size:0.85rem;font-weight:500;">{label}</span>'
            f'{"<span style=color:#64748B;font-size:0.75rem;margin-left:auto>" + detail + "</span>" if detail else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

    status_row("Gemini LLM",      gemini_ok, settings.llm_model if gemini_ok else "Key missing")
    status_row("Embeddings",      True,      "local (MiniLM)")
    status_row("Tavily Search",   tavily_ok, "Active" if tavily_ok else "Disabled")
    status_row("Knowledge Base",  vector_ct > 0, f"{vector_ct} vectors")

    st.markdown("---")
    st.markdown("**🔁 Pipeline**", unsafe_allow_html=False)
    st.markdown(
        f'<div style="font-size:0.8rem;color:#94A3B8;line-height:1.8;">'
        f'<div>Agents: <b style="color:#A5B4FC">6</b></div>'
        f'<div>Model: <b style="color:#A5B4FC">{settings.llm_model}</b></div>'
        f'<div>Max Revisions: <b style="color:#A5B4FC">{settings.max_revisions}</b></div>'
        f'<div>RAG Top-K: <b style="color:#A5B4FC">{settings.rag_top_k}</b></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not gemini_ok:
        st.markdown("---")
        st.error("**⚠️ GOOGLE_API_KEY missing**\n\nAdd it to your `.env` file to run the pipeline.")

    st.markdown("---")
    if st.button("🔄 New Project", use_container_width=True):
        st.session_state.pipeline_state = "idle"
        st.session_state.final_state = None
        st.session_state.agent_log = []
        st.session_state.error_msg = None
        st.rerun()

# ── Hero Banner ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <p class="hero-title">AI Project Builder</p>
  <p class="hero-subtitle">Describe your AI idea — six specialized agents will design<br>your complete project plan in minutes.</p>
  <div>
    <span class="badge badge-blue">LangGraph</span>
        <span class="badge badge-purple">Gemini</span>
    <span class="badge badge-cyan">RAG</span>
    <span class="badge badge-green">Multi-Agent</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STATE: IDLE — Show input form
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.pipeline_state == "idle":

    # Example ideas
    EXAMPLES = [
        "Build a real-time computer vision system to detect manufacturing defects on an assembly line using deep learning and YOLOv8.",
        "Create a RAG-powered document Q&A chatbot for legal contracts using Gemini and ChromaDB.",
        "Develop a music recommendation system that personalizes playlists based on listening history and mood detection.",
        "Build an NLP sentiment analysis pipeline for social media monitoring in the e-commerce domain.",
    ]

    col_main, col_sidebar_spacer = st.columns([3, 1])

    with col_main:
        st.markdown("""
        <div class="section-header">Describe Your Project</div>
        <div class="section-title">What AI system do you want to build?</div>
        """, unsafe_allow_html=True)

        user_idea = st.text_area(
            label="Project Idea",
            label_visibility="collapsed",
            placeholder="Example: Build a computer vision system that detects product defects in real-time on a manufacturing assembly line using deep learning...",
            height=140,
            key="user_idea_input",
        )

        col_btn, col_count = st.columns([2, 1])
        with col_btn:
            submit = st.button("🚀 Build My Project Plan", use_container_width=True, disabled=not gemini_ok)
        with col_count:
            char_count = len(user_idea)
            color = "#6EE7B7" if char_count >= 50 else "#F59E0B" if char_count > 0 else "#64748B"
            st.markdown(
                f'<p style="color:{color};font-size:0.85rem;margin-top:10px;text-align:right;">'
                f'{char_count} chars {"✓" if char_count >= 50 else "(min 50)"}</p>',
                unsafe_allow_html=True,
            )

        if submit and user_idea.strip():
            st.session_state.pipeline_state = "running"
            st.session_state.user_idea = user_idea.strip()
            st.session_state.agent_log = []
            st.rerun()
        elif submit and not user_idea.strip():
            st.warning("Please describe your project idea before submitting.")

    # Example ideas
    st.markdown("---")
    st.markdown('<div class="section-header" style="margin-bottom:12px;">Try an Example</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        with cols[i % 2]:
            if st.button(f"💡 {ex[:70]}...", key=f"ex_{i}", use_container_width=True):
                st.session_state.pipeline_state = "running"
                st.session_state.user_idea = ex
                st.session_state.agent_log = []
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: RUNNING — Stream pipeline with live progress
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pipeline_state == "running":

    user_idea = st.session_state.get("user_idea", "")

    st.markdown(f"""
    <div class="glass-card">
      <div class="section-header">Pipeline Executing</div>
      <div style="color:#F1F5F9;font-size:0.95rem;margin-top:4px;">
        <span style="color:#94A3B8;">Idea:</span> {user_idea[:120]}{'...' if len(user_idea) > 120 else ''}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Build step display
    completed_agents = set(st.session_state.agent_log)
    step_placeholder = st.empty()

    def render_steps(current_agent=None, done_agents=None):
        done_agents = done_agents or set()
        html = '<div style="margin-top:8px;">'
        for node, icon, name, desc in AGENTS:
            if node in done_agents:
                cls, status_icon = "step-done", "✅"
            elif node == current_agent:
                cls, status_icon = "step-running", "⏳"
            else:
                cls, status_icon = "step-pending", "⬜"
            html += f"""
            <div class="step-item {cls}">
              <span class="step-icon">{icon}</span>
              <div>
                <div class="step-name">{status_icon} {name}</div>
                <div class="step-desc">{desc}</div>
              </div>
            </div>"""
        html += "</div>"
        return html

    step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
    progress_bar = st.progress(0, text="Starting pipeline...")

    # ── Run the pipeline ─────────────────────────────────────────────────────
    try:
        from app.graph.workflow import stream_pipeline

        agent_order = [a[0] for a in AGENTS]
        done = set()
        final_state_parts = {}

        for node_name, state_update in stream_pipeline(user_idea):
            # Skip internal LangGraph nodes
            if node_name.startswith("__"):
                continue

            # Mark as done
            done.add(node_name)
            st.session_state.agent_log = list(done)

            # Merge state update
            final_state_parts.update(state_update)

            # Find next pending
            current_idx = agent_order.index(node_name) if node_name in agent_order else -1
            next_agent = agent_order[current_idx + 1] if current_idx + 1 < len(agent_order) else None

            # Update UI
            step_placeholder.markdown(render_steps(next_agent, done), unsafe_allow_html=True)
            progress = int((len(done) / len(AGENTS)) * 100)
            progress_bar.progress(progress, text=f"Completed: {node_name} ({progress}%)")

        # All done
        step_placeholder.markdown(render_steps(done_agents=done), unsafe_allow_html=True)
        progress_bar.progress(100, text="Pipeline complete!")
        time.sleep(0.5)

        st.session_state.final_state = final_state_parts
        st.session_state.pipeline_state = "complete"
        st.rerun()

    except Exception as e:
        st.session_state.pipeline_state = "error"
        st.session_state.error_msg = str(e)
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: ERROR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pipeline_state == "error":

    st.error(f"**Pipeline Error**\n\n{st.session_state.error_msg}")
    st.markdown("""
    **Common causes:**
    - `GOOGLE_API_KEY` not set or invalid → [Get a key](https://aistudio.google.com/app/apikey)
    - Gemini API rate limit hit → wait 60 seconds and retry
    - LangGraph version incompatibility → check `pip list`
    """)
    if st.button("🔄 Try Again"):
        st.session_state.pipeline_state = "idle"
        st.session_state.error_msg = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STATE: COMPLETE — Display full report
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pipeline_state == "complete":

    final_state = st.session_state.final_state or {}
    report: dict = final_state.get("final_report", {})

    if not report:
        st.error("Pipeline completed but no report was generated. Check agent error logs.")
        if st.button("Start Over"):
            st.session_state.pipeline_state = "idle"
            st.rerun()
        st.stop()

    # ── Report header ──────────────────────────────────────────────────────────
    project_title   = report.get("project_title", "AI Project")
    timeline_weeks  = report.get("estimated_timeline_weeks", "?")
    revision_count  = report.get("revision_count", 0)
    roadmap_len     = len(report.get("implementation_roadmap", []))
    sources_len     = len(report.get("sources", []))

    st.markdown(f"""
    <div class="hero-banner" style="padding:32px 36px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <span style="font-size:1.8rem;">📋</span>
        <span class="section-header" style="margin:0;">Project Plan Ready</span>
      </div>
      <div style="font-size:1.8rem;font-weight:800;color:#F1F5F9;margin-bottom:4px;">{project_title}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key metrics ────────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, f"{timeline_weeks}w",      "Estimated Timeline"),
        (m2, str(roadmap_len),           "Implementation Steps"),
        (m3, str(revision_count),        "Critic Revisions"),
        (m4, str(sources_len),           "Research Sources"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value">{val}</div>
              <div class="metric-label">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Download button ────────────────────────────────────────────────────────
    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    fname = f"{project_title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    st.download_button(
        label="⬇️  Download Full Report (JSON)",
        data=report_json,
        file_name=fname,
        mime="application/json",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabbed report ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Overview",
        "🏗️ Architecture",
        "📊 Dataset",
        "🤖 Model",
        "🗺️ Roadmap",
        "🔗 Sources",
    ])

    # ── Tab 1: Overview ────────────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="report-label">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="report-section">{report.get("executive_summary", "—")}</div>""", unsafe_allow_html=True)

        col_obj, col_met = st.columns(2)

        with col_obj:
            st.markdown('<div class="report-label" style="margin-top:16px;">Objectives</div>', unsafe_allow_html=True)
            objectives = report.get("objectives", [])
            obj_html = '<div class="report-section">' + "".join(
                f'<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="color:#6366F1;font-weight:700;">{i+1}.</span>'
                f'<span style="color:#F1F5F9;font-size:0.9rem;">{o}</span></div>'
                for i, o in enumerate(objectives)
            ) + "</div>"
            st.markdown(obj_html, unsafe_allow_html=True)

        with col_met:
            st.markdown('<div class="report-label" style="margin-top:16px;">Success Metrics</div>', unsafe_allow_html=True)
            metrics = report.get("success_metrics", [])
            met_html = '<div class="report-section">' + "".join(
                f'<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="color:#10B981;font-weight:700;">✓</span>'
                f'<span style="color:#F1F5F9;font-size:0.9rem;">{m}</span></div>'
                for m in metrics
            ) + "</div>"
            st.markdown(met_html, unsafe_allow_html=True)

        # Required skills + tools
        col_sk, col_tl = st.columns(2)
        with col_sk:
            st.markdown('<div class="report-label" style="margin-top:16px;">Required Skills</div>', unsafe_allow_html=True)
            skills = report.get("required_skills", [])
            st.markdown('<div style="margin-top:8px;">' + "".join(f'<span class="chip">{s}</span>' for s in skills) + "</div>", unsafe_allow_html=True)

        with col_tl:
            st.markdown('<div class="report-label" style="margin-top:16px;">Recommended Tools</div>', unsafe_allow_html=True)
            tools = report.get("recommended_tools", [])
            st.markdown('<div style="margin-top:8px;">' + "".join(f'<span class="chip chip-green">{t}</span>' for t in tools) + "</div>", unsafe_allow_html=True)

    # ── Tab 2: Architecture ────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="report-label">Technical Architecture</div>', unsafe_allow_html=True)
        arch_text = report.get("technical_architecture", "")
        st.markdown(arch_text)  # Rendered as markdown

    # ── Tab 3: Dataset ─────────────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="report-label">Dataset Strategy</div>', unsafe_allow_html=True)
        st.markdown(report.get("dataset_plan", ""))

    # ── Tab 4: Model ───────────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="report-label">Model Strategy</div>', unsafe_allow_html=True)
        st.markdown(report.get("model_plan", ""))

    # ── Tab 5: Roadmap ─────────────────────────────────────────────────────────
    with tab5:
        roadmap = report.get("implementation_roadmap", [])
        st.markdown('<div class="report-label">Implementation Roadmap</div>', unsafe_allow_html=True)
        road_html = '<div class="report-section">'
        for i, step in enumerate(roadmap):
            road_html += f"""
            <div class="roadmap-item">
              <div class="roadmap-num">{i+1}</div>
              <div class="roadmap-text">{step}</div>
            </div>"""
        road_html += "</div>"
        st.markdown(road_html, unsafe_allow_html=True)

        # Risks
        risks = report.get("risks_and_mitigations", [])
        if risks:
            st.markdown('<div class="report-label" style="margin-top:24px;">Risks & Mitigations</div>', unsafe_allow_html=True)
            risks_html = "".join(f'<div class="risk-item">⚠️ {r}</div>' for r in risks)
            st.markdown(risks_html, unsafe_allow_html=True)

    # ── Tab 6: Sources ─────────────────────────────────────────────────────────
    with tab6:
        sources = report.get("sources", [])
        st.markdown(f'<div class="report-label">Research Sources ({len(sources)})</div>', unsafe_allow_html=True)
        if sources:
            src_html = ""
            for s in sources:
                if s.startswith("http"):
                    src_html += f'<div class="source-item">🔗 <a href="{s}" target="_blank">{s}</a></div>'
                else:
                    src_html += f'<div class="source-item">📄 {s}</div>'
            st.markdown(src_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="source-item">No sources collected.</div>', unsafe_allow_html=True)

    # ── Pipeline metadata footer ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center;padding:16px;color:#64748B;font-size:0.78rem;
    border-top:1px solid rgba(255,255,255,0.06);margin-top:16px;">
      Generated by AI Project Builder &nbsp;·&nbsp; {settings.llm_model} &nbsp;·&nbsp;
      {revision_count} critic revision(s) &nbsp;·&nbsp;
      {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
    """, unsafe_allow_html=True)
