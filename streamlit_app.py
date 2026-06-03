"""
AgentOps – Streamlit Comparison UI
Side-by-side: Direct LLM  vs  Multi-Agent Pipeline
"""

import os
import sys
import time
import traceback
import importlib

import streamlit as st

# ── path setup ──────────────────────────────────────────────────────────────
# streamlit_app.py lives at:  <project_root>/streamlit_app.py
# v1 modules live at:         <project_root>/agents/intermediate/v1/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V1_DIR   = os.path.join(BASE_DIR, "agents", "intermediate", "v1")

# Insert at position 0 so our local modules always win over any installed pkg
if V1_DIR not in sys.path:
    sys.path.insert(0, V1_DIR)
# Also make sure the project root is on the path (safety net)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentOps – Log Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title  { font-size:2.2rem; font-weight:700; color:#1E88E5; }
    .sub-title   { font-size:1rem; color:#666; margin-bottom:1.5rem; }
    .metric-card { background:#1e1e2e; border-radius:10px; padding:1rem;
                   border-left:4px solid #1E88E5; margin-bottom:1rem; }
    .agent-card  { background:#1e2e1e; border-radius:10px; padding:1rem;
                   border-left:4px solid #43A047; margin-bottom:1rem; }
    .badge-crit  { background:#c62828; color:#fff; padding:2px 8px;
                   border-radius:4px; font-size:.8rem; }
    .badge-high  { background:#e65100; color:#fff; padding:2px 8px;
                   border-radius:4px; font-size:.8rem; }
    .badge-med   { background:#f9a825; color:#000; padding:2px 8px;
                   border-radius:4px; font-size:.8rem; }
    .badge-low   { background:#2e7d32; color:#fff; padding:2px 8px;
                   border-radius:4px; font-size:.8rem; }
    .stButton>button { width:100%; }
    .key-warn { background:#fff3cd; border:1px solid #ffc107; border-radius:6px;
                padding:0.5rem 1rem; color:#856404; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

# ── helpers ───────────────────────────────────────────────────────────────────
def severity_badge(sev: str) -> str:
    sev = (sev or "UNKNOWN").upper()
    cls = {"CRITICAL": "badge-crit", "HIGH": "badge-high",
           "MEDIUM": "badge-med", "LOW": "badge-low"}.get(sev, "badge-low")
    return f'<span class="{cls}">{sev}</span>'


def validate_api_key(key: str) -> tuple[bool, str]:
    """Return (is_valid, reason). Does a lightweight format check only."""
    key = key.strip()
    if not key:
        return False, "API key is empty."
    if not key.startswith("sk-"):
        return False, "Key must start with `sk-`."
    if len(key) < 40:
        return False, "Key looks too short – please paste the full key."
    if " " in key or "\n" in key:
        return False, "Key contains spaces/newlines – please paste it without extra whitespace."
    return True, ""


# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    raw_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Paste your key from https://platform.openai.com/api-keys  — starts with sk-",
    )

    key_ok, key_msg = validate_api_key(raw_key)
    if raw_key:
        if key_ok:
            # Always overwrite env so both OpenAI client and CrewAI pick it up
            os.environ["OPENAI_API_KEY"] = raw_key.strip()
            st.success("✅ API key looks valid")
        else:
            st.markdown(f'<div class="key-warn">⚠️ {key_msg}</div>', unsafe_allow_html=True)
    else:
        st.info("Enter your OpenAI API key to run analysis.")

    st.divider()

    model_choice = st.selectbox(
        "LLM Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
    )

    st.divider()
    st.markdown("### 📋 Sample Logs")
    sample_choice = st.selectbox(
        "Load a sample",
        [
            "-- paste your own --",
            "Kubernetes ImagePullBackOff",
            "Database Connection Failure",
            "Nginx Upstream Failure",
            "Redis Memory Exhaustion",
            "Kafka Consumer Lag",
            "CI/CD Pipeline Failure",
            "JWT Cascade Failure",
        ],
    )

    st.divider()
    st.markdown("""
**About**  
Compares two approaches on the same log:

- 🔵 **Direct LLM** — one prompt to GPT  
- 🟢 **Multi-Agent** — 3-agent CrewAI pipeline  
  1. Log Analyzer  
  2. Issue Investigator  
  3. Solution Specialist
""")

# ── sample logs dict ─────────────────────────────────────────────────────────
SAMPLES = {
    "Kubernetes ImagePullBackOff": """\
[2024-01-15 14:32:15.123] INFO: Starting deployment of myapp-deployment
[2024-01-15 14:32:16.567] WARNING: Pod myapp-deployment-7b8c9d5f4-abc12 in Pending state
[2024-01-15 14:32:17.890] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 failed to start
[2024-01-15 14:32:18.123] ERROR: Failed to pull image "myapp:v1.2.3": pull access denied, repository does not exist or may require 'docker login'
[2024-01-15 14:32:18.456] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 status: ImagePullBackOff
[2024-01-15 14:32:25.901] ERROR: Deployment rollout failed: deployment "myapp-deployment" exceeded its progress deadline
[2024-01-15 14:32:26.789] WARNING: Service myapp-service has no available endpoints
[2024-01-15 14:32:29.456] CRITICAL: Production deployment failed - rollback initiated""",

    "Database Connection Failure": """\
[2024-01-15 09:15:22.001] INFO: Application startup initiated
[2024-01-15 09:15:22.445] INFO: Connecting to database at db.internal:5432
[2024-01-15 09:15:23.112] ERROR: Connection refused: could not connect to server: Connection refused
[2024-01-15 09:15:23.113] ERROR: Is the server running on host "db.internal" (10.0.1.45) accepting TCP/IP connections on port 5432?
[2024-01-15 09:15:24.001] WARNING: Retrying database connection (attempt 1/3)
[2024-01-15 09:15:25.002] WARNING: Retrying database connection (attempt 2/3)
[2024-01-15 09:15:26.003] ERROR: Retrying database connection (attempt 3/3)
[2024-01-15 09:15:26.450] CRITICAL: Database connection pool exhausted - all retries failed
[2024-01-15 09:15:26.451] ERROR: FATAL: password authentication failed for user "appuser"
[2024-01-15 09:15:26.789] CRITICAL: Application cannot start - database unavailable""",

    "Nginx Upstream Failure": """\
[2024-02-10 02:15:33.001] INFO: Nginx reverse proxy started on port 443
[2024-02-10 02:16:03.889] ERROR: Upstream backend-02 (10.0.2.12:8080) timed out after 5000ms
[2024-02-10 02:16:45.112] ERROR: Upstream backend-01 (10.0.2.11:8080) timed out after 5000ms
[2024-02-10 02:17:00.001] CRITICAL: Only 1 upstream node remaining - load balancer degraded
[2024-02-10 02:17:15.334] ERROR: Upstream backend-03 (10.0.2.13:8080) connection refused: ECONNREFUSED
[2024-02-10 02:17:15.335] CRITICAL: All upstream nodes unavailable - returning 502 Bad Gateway to all clients
[2024-02-10 02:17:15.336] ERROR: Circuit breaker OPEN - blocking requests to backend pool
[2024-02-10 02:17:15.500] CRITICAL: 502 Bad Gateway served to 1,204 active connections""",

    "Redis Memory Exhaustion": """\
[2024-02-12 11:00:00.001] INFO: Redis cache server v7.0.11 running on port 6379
[2024-02-12 14:22:10.445] WARNING: Memory usage at 75% (1.5 GB / 2 GB) - approaching limit
[2024-02-12 14:48:02.334] ERROR: Memory usage at 98% (1.96 GB / 2 GB) - eviction cannot keep up with write rate
[2024-02-12 14:48:03.001] ERROR: MISCONF Redis is configured to save RDB snapshots but cannot persist on disk
[2024-02-12 14:48:03.002] ERROR: OOM command not allowed when used memory > 'maxmemory'. command=SET key=session:user:8821
[2024-02-12 14:48:03.200] CRITICAL: Redis rejecting all write commands - cache fully saturated
[2024-02-12 14:48:04.001] CRITICAL: User sessions cannot be persisted - authentication service degraded
[2024-02-12 14:48:04.500] ERROR: 3,412 requests/sec failing with cache write error""",

    "Kafka Consumer Lag": """\
[2024-02-14 08:00:00.001] INFO: Kafka consumer group order-processing-group started
[2024-02-14 09:15:22.445] WARNING: Consumer lag increasing: 12,450 messages behind on partition 2
[2024-02-14 09:16:00.334] ERROR: Consumer order-processor-03 failed to commit offset: coordinator not available
[2024-02-14 09:16:01.001] ERROR: Rebalance timed out after 30000ms - consumer order-processor-01 unresponsive
[2024-02-14 09:16:01.500] CRITICAL: Messages accumulating on partition 2: 128,445 unprocessed orders
[2024-02-14 09:16:02.001] ERROR: order-processor-03 threw unhandled exception: java.lang.OutOfMemoryError: Java heap space
[2024-02-14 09:16:02.500] CRITICAL: Consumer node kafka-consumer-03 crashed - partition 2 and 4 now unassigned
[2024-02-14 09:16:03.001] CRITICAL: 256,890 unprocessed order messages - revenue impact potential""",

    "CI/CD Pipeline Failure": """\
[2024-02-16 15:30:00.001] INFO: GitHub Actions pipeline triggered for PR #487 (branch: feature/payment-refactor)
[2024-02-16 15:30:52.334] WARNING: ESLint: 3 warnings found in src/payments/processor.js (non-blocking)
[2024-02-16 15:31:10.001] ERROR: FAIL src/payments/processor.test.js
[2024-02-16 15:31:10.003] ERROR: TypeError: Cannot read properties of undefined (reading 'amount')
[2024-02-16 15:31:10.004] ERROR:   at Object.processRefund (src/payments/processor.js:142:28)
[2024-02-16 15:31:10.100] ERROR: FAIL src/payments/webhook.test.js
[2024-02-16 15:31:10.102] ERROR: Expected status 200 but received 500
[2024-02-16 15:31:12.001] ERROR: Test Suites: 2 failed, 14 passed | Tests: 4 failed, 187 passed
[2024-02-16 15:31:12.500] CRITICAL: Pipeline FAILED - PR #487 blocked from merging to main
[2024-02-16 15:31:12.502] ERROR: Deployment to staging environment cancelled""",

    "JWT Cascade Failure": """\
[2024-02-18 20:01:14.445] WARNING: JWT secret rotation initiated by admin user admin@myapp.com
[2024-02-18 20:01:14.501] ERROR: Old JWT secret NOT propagated to user-service (service unreachable during rotation)
[2024-02-18 20:01:14.502] ERROR: Old JWT secret NOT propagated to order-service (rolling deploy in progress)
[2024-02-18 20:01:30.334] ERROR: user-service returning 401 Unauthorized for all requests: JWT signature verification failed
[2024-02-18 20:01:30.335] ERROR: order-service returning 401 Unauthorized for all requests: JWT signature verification failed
[2024-02-18 20:01:31.001] WARNING: Clients retrying failed requests - traffic spike: 8,540 req/min (8.5x normal)
[2024-02-18 20:01:31.500] ERROR: Rate limiter triggered for 1,240 client IPs - returning 429 Too Many Requests
[2024-02-18 20:01:32.001] CRITICAL: Cascade failure - auth errors causing retry storm overwhelming API gateway
[2024-02-18 20:01:33.500] CRITICAL: Full platform degradation - 0% of authenticated requests succeeding
[2024-02-18 20:01:34.001] ERROR: SLA breach detected - downtime exceeding 60 seconds""",
}

# ── header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🤖 AgentOps – DevOps Log Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Compare Direct LLM vs Multi-Agent Pipeline for production log analysis</div>', unsafe_allow_html=True)

# ── log input ─────────────────────────────────────────────────────────────────
default_log = SAMPLES.get(sample_choice, "")
log_input = st.text_area(
    "📄 Paste your log data",
    value=default_log,
    height=200,
    placeholder="Paste log lines here or select a sample from the sidebar...",
)

uploaded = st.file_uploader("Or upload a .log / .txt file", type=["log", "txt"])
if uploaded:
    log_input = uploaded.read().decode("utf-8")
    st.success(f"Loaded {uploaded.name} ({len(log_input)} chars)")

# ── run button ────────────────────────────────────────────────────────────────
_, col_btn, _ = st.columns([1, 2, 1])
with col_btn:
    run_btn = st.button("🚀 Run Comparison Analysis", type="primary", use_container_width=True)

st.divider()

# ── render helpers ────────────────────────────────────────────────────────────
def render_direct_result(result: dict):
    st.markdown("### 🔵 Direct LLM Analysis")
    c1, c2, c3 = st.columns(3)
    c1.metric("⏱ Time",   f"{result['elapsed_seconds']}s")
    c2.metric("🔢 Tokens", result["tokens_used"])
    c3.metric("💬 Model",  result["model"])
    with st.expander("📝 Full Response", expanded=True):
        st.markdown(result["response_text"])


def render_agent_result(result: dict, elapsed: float, agent_log: list):
    st.markdown("### 🟢 Multi-Agent Pipeline")
    c1, c2, c3 = st.columns(3)
    c1.metric("⏱ Time",   f"{round(elapsed, 1)}s")
    c2.metric("🤖 Agents", "3")
    c3.metric("📋 Tasks",  "3")

    analysis     = result.get("analysis")
    investigation = result.get("investigation")
    solution     = result.get("solution")

    if analysis:
        with st.expander("🔍 Agent 1 – Log Analysis", expanded=True):
            st.markdown(
                f"**Severity:** {severity_badge(analysis.severity)}  \n"
                f"**Root Cause:** {analysis.root_cause}  \n"
                f"**Affected:** {', '.join(analysis.affected_components)}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Summary:** {analysis.summary}")
            st.markdown("**Errors found:**")
            for err in analysis.errors:
                st.markdown(f"- `{err.timestamp}` **[{err.level}]** {err.message}")
            st.markdown(f"**Timeline:** {analysis.timeline}")

    if investigation:
        with st.expander("🔎 Agent 2 – Investigation", expanded=False):
            st.markdown(f"**Issue:** {investigation.issue_summary}")
            if investigation.common_causes:
                st.markdown("**Common Causes:**")
                for c in investigation.common_causes:
                    st.markdown(f"- {c}")
            if investigation.community_solutions:
                st.markdown("**Solutions:**")
                for s in investigation.community_solutions:
                    st.markdown(f"- {s}")
            if investigation.best_practices:
                st.markdown("**Best Practices:**")
                for bp in investigation.best_practices:
                    st.markdown(f"- {bp}")

    if solution:
        with st.expander("🛠 Agent 3 – Remediation Plan", expanded=True):
            st.markdown(f"### {solution.title}")
            st.info(f"⏰ Estimated resolution: **{solution.estimated_resolution_time}**")
            st.markdown("**Step-by-step fix:**")
            for step in solution.primary_solution:
                st.markdown(f"**Step {step.step_number}:** {step.description}")
                if step.command:
                    st.code(step.command, language="bash")
                if step.expected_output:
                    st.caption(f"Expected: {step.expected_output}")
            if solution.verification_steps:
                st.markdown("**Verification:**")
                for v in solution.verification_steps:
                    st.markdown(f"- {v}")
            if solution.rollback_procedure:
                with st.expander("⏪ Rollback Procedure"):
                    for r in solution.rollback_procedure:
                        st.markdown(f"- {r}")

    if agent_log:
        with st.expander("📋 Agent Execution Log", expanded=False):
            st.text("\n".join(agent_log))


def render_comparison(direct: dict, agent_elapsed: float):
    st.divider()
    st.markdown("## 📊 Side-by-Side Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔵 Direct LLM")
        st.metric("Response Time",        f"{direct['elapsed_seconds']}s")
        st.metric("Total Tokens",         direct["tokens_used"])
        st.metric("Agents Used",          "0")
        st.metric("Structured Output",    "❌")
        st.metric("Step-by-step Commands","❌")
        st.metric("Verification Steps",   "❌")
        st.metric("Rollback Procedure",   "❌")
    with col2:
        st.markdown("### 🟢 Multi-Agent Pipeline")
        st.metric("Response Time",        f"{round(agent_elapsed, 1)}s")
        st.metric("Total Tokens",         "~3x (3 agents)")
        st.metric("Agents Used",          "3")
        st.metric("Structured Output",    "✅")
        st.metric("Step-by-step Commands","✅")
        st.metric("Verification Steps",   "✅")
        st.metric("Rollback Procedure",   "✅")

    st.divider()
    st.markdown("### 🔑 Key Differences")
    import pandas as pd
    diff_data = {
        "Aspect": ["Speed","Depth of Analysis","Structured Output",
                   "Actionable Commands","Multi-step Reasoning",
                   "Tool Use (file reading)","Verification & Rollback","Retry / Guardrails"],
        "Direct LLM": ["⚡ Fastest","Single perspective","Freeform text",
                       "Sometimes, no guarantee","Single pass","No","No","No"],
        "Multi-Agent Pipeline": ["🐢 Slower (worth it)","3 specialist perspectives",
                                 "Pydantic-validated JSON","Always – with bash commands",
                                 "Analyze → Investigate → Solve","Yes – reads actual log files",
                                 "Always included","Yes – guardrail validation"],
    }
    st.dataframe(pd.DataFrame(diff_data), use_container_width=True, hide_index=True)


# ── main run logic ─────────────────────────────────────────────────────────────
if run_btn:
    # ── guard: log content
    if not log_input.strip():
        st.error("Please paste some log data or select a sample from the sidebar.")
        st.stop()

    # ── guard: API key
    api_key_env = os.getenv("OPENAI_API_KEY", "").strip()
    ok, reason = validate_api_key(api_key_env)
    if not ok:
        st.error(f"⛔ Invalid API key: {reason}  \nPlease fix the key in the sidebar and try again.")
        st.stop()

    st.markdown("## 🔄 Running Analysis…")
    prog = st.progress(0, text="Step 1/2 – Calling Direct LLM…")

    # ── Direct LLM ─────────────────────────────────────────────────────────
    direct_result = None
    direct_error  = None
    try:
        # Force-reload so a fresh OpenAI client picks up the env key set above
        import direct_llm as _dll
        importlib.reload(_dll)
        direct_result = _dll.analyze_with_direct_llm(log_input, model=model_choice)
    except Exception:
        direct_error = traceback.format_exc()

    prog.progress(50, text="Step 2/2 – Running Multi-Agent Pipeline (30–90 s)…")

    # ── Multi-Agent ────────────────────────────────────────────────────────
    agent_result  = None
    agent_error   = None
    agent_elapsed = 0.0
    agent_log: list = []
    t0 = time.time()

    import io
    from contextlib import redirect_stdout

    try:
        # Write the pasted log to a temp file so log_reader_tool can open it
        tmp_path = os.path.join(V1_DIR, "task_outputs", "_tmp_streamlit.log")
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        with open(tmp_path, "w") as f:
            f.write(log_input)

        # Reload main so agent/LLM objects pick up the freshly set env key
        import main as _main
        importlib.reload(_main)

        buf = io.StringIO()
        with redirect_stdout(buf):
            agent_result = _main.run_pipeline(log_file_path=tmp_path, verbose=True)
        agent_elapsed = time.time() - t0
        agent_log = buf.getvalue().splitlines()

    except Exception:
        agent_error   = traceback.format_exc()
        agent_elapsed = time.time() - t0

    prog.progress(100, text="✅ Done!")
    time.sleep(0.3)
    prog.empty()

    # ── render ──────────────────────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        if direct_error:
            st.error("Direct LLM failed")
            with st.expander("Show traceback"):
                st.code(direct_error)
        elif direct_result:
            render_direct_result(direct_result)

    with right:
        if agent_error:
            st.error("Multi-Agent Pipeline failed")
            with st.expander("Show traceback"):
                st.code(agent_error)
        elif agent_result:
            render_agent_result(agent_result, agent_elapsed, agent_log)

    if direct_result and agent_result:
        render_comparison(direct_result, agent_elapsed)

else:
    # ── placeholder ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
<div class="metric-card">
<h3>🔵 Direct LLM</h3>
<p>A single OpenAI API call with a well-crafted system prompt.
Fast and simple, but no structured output, no tool use, no verification steps.</p>
<ul>
  <li>Single-pass analysis</li>
  <li>Free-form text output</li>
  <li>No file reading</li>
  <li>No retry logic</li>
</ul>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
<div class="agent-card">
<h3>🟢 Multi-Agent Pipeline</h3>
<p>Three specialized CrewAI agents working in sequence — each with a distinct role,
tool access, and Pydantic-validated output with guardrails.</p>
<ul>
  <li>Agent 1 – Log Analyzer (reads files)</li>
  <li>Agent 2 – Issue Investigator (deep research)</li>
  <li>Agent 3 – Solution Specialist (bash commands)</li>
  <li>Guardrail validation on every output</li>
</ul>
</div>
""", unsafe_allow_html=True)

    st.info("👆 Enter your OpenAI API key in the sidebar, paste a log, and click **Run Comparison Analysis**.")
