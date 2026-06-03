# AgentOps – AI-Powered Multi-Agent DevOps Troubleshooting System

> **Jan 2026 – Feb 2026**  
> Multi-agent CrewAI pipeline for production log analysis, root-cause detection, and automated remediation planning.

---

## Architecture

```
Log Input
    │
    ▼
┌─────────────────────┐
│  Agent 1            │  tools: log_reader_tool
│  DevOps Log Analyzer│  max_iter=3, max_rpm=10, max_execution_time=300s
└────────┬────────────┘
         │ context
         ▼
┌─────────────────────┐
│  Agent 2            │  tools: (LLM knowledge)
│  Issue Investigator │  max_iter=5, max_rpm=15, max_execution_time=600s
└────────┬────────────┘
         │ context
         ▼
┌─────────────────────┐
│  Agent 3            │  tools: save_report_tool
│  Solution Specialist│  max_iter=3, max_rpm=10, max_execution_time=300s
└────────┬────────────┘
         │
         ▼
  Pydantic-validated
  SolutionPlan output
```

---

## Project Structure

```
agentops/
├── streamlit_app.py              ← Comparison UI (Direct LLM vs Multi-Agent)
├── requirements.txt
└── agents/
    ├── dummy_logs/
    │   ├── kubernetes_deployment_error.log
    │   └── database_connection_error.log
    └── intermediate/
        └── v1/
            ├── agents.py         ← 3 CrewAI agents
            ├── tasks.py          ← Tasks + Pydantic models + guardrail
            ├── tools.py          ← log_reader_tool, save_report_tool
            ├── main.py           ← Full pipeline runner (CLI)
            ├── production_pipeline.py  ← Guardrail demo
            └── direct_llm.py     ← Single-call baseline
```

---

## Setup

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Set your API key
export OPENAI_API_KEY=sk-...

# 3. Run the Streamlit comparison UI
streamlit run streamlit_app.py

# OR run the CLI pipeline directly
cd agents/intermediate/v1
python main.py --log-file ../../dummy_logs/kubernetes_deployment_error.log
```

---

## Agent Parameters Explained

| Parameter | Description |
|---|---|
| `max_execution_time` | Hard timeout in seconds (e.g. 300s = 5 mins) |
| `max_iter` | Max number of LLM iterations per agent |
| `max_rpm` | Max LLM API requests per minute (rate limiting) |
| `respect_context_window` | Auto-summarize if conversation exceeds model context |

---

## Key Features

- **3-Agent Sequential Pipeline** – Analyze → Investigate → Solve
- **Pydantic Structured Output** – Every output is type-validated
- **Guardrail Validation** – Rejects outputs with zero errors, forces retry
- **File Tool Integration** – Agents read actual log files from disk
- **Streamlit Comparison UI** – Side-by-side direct LLM vs multi-agent
- **Rate Limiting & Timeouts** – Production-safe agent configuration
