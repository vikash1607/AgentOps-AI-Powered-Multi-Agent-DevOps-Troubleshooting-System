# 🤖 AgentOps – AI-Powered Multi-Agent DevOps Troubleshooting System

> Automated Production Log Analysis, Root Cause Detection, and Remediation Planning using Multi-Agent AI

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Overview

AgentOps is an AI-powered DevOps troubleshooting system that leverages multiple specialized AI agents to analyze production logs, investigate failures, identify root causes, and generate actionable remediation plans.

Unlike traditional single-prompt log analysis, AgentOps orchestrates multiple AI agents that collaborate to provide deeper insights, structured outputs, and production-ready troubleshooting workflows.

---

## 🚀 Key Features

### 🔍 Intelligent Log Analysis
- Production log ingestion via file upload or text input
- Detects errors, warnings, failures, and anomalies
- Extracts timestamps, affected services, and severity levels

### 🕵️ Root Cause Investigation
- Multi-agent investigation workflow
- Identifies underlying causes instead of surface-level errors
- Correlates events across multiple log entries

### 🛠 Automated Remediation Planning
- Generates step-by-step troubleshooting instructions
- Provides bash commands and deployment fixes
- Suggests verification and rollback procedures

### 📊 Structured Outputs
- Pydantic-validated responses
- Severity classification
- Incident timeline generation
- Root cause reports

### 🌐 Modern UI
- Streamlit-powered dashboard
- Compare Direct LLM vs Multi-Agent Analysis
- Upload log files or paste raw logs

---
# 🏗 Project Structure

```text


AgentOps/
│
├── streamlit_app.py
├── main.py
├── direct_llm.py
├── production_pipeline.py
├── tools.py
├── requirements.txt
│
├── agents/
│   ├── agents.py
│   ├── tasks.py
│   └── configs/
│
├── task_outputs/
│
└── README.md


```
# 🏗 Architecture

```text
                ┌────────────────────┐
                │    Production Log   │
                └──────────┬─────────┘
                           │
                           ▼
                ┌────────────────────┐
                │ Agent 1            │
                │ Log Analyzer       │
                └──────────┬─────────┘
                           │
                           ▼
                ┌────────────────────┐
                │ Agent 2            │
                │ Issue Investigator │
                └──────────┬─────────┘
                           │
                           ▼
                ┌────────────────────┐
                │ Agent 3            │
                │ Solution Specialist│
                └──────────┬─────────┘
                           │
                           ▼
                ┌────────────────────┐
                │ Remediation Report │
                └────────────────────┘
