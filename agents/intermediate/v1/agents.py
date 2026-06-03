import os
from crewai import Agent, LLM
from tools import log_reader_tool, save_report_tool

# LLM is created as a function so it always reads the current env key.
# CrewAI agents accept a callable for llm= as well as an LLM instance.
def _make_llm():
    return LLM(
        model="gpt-4o-mini",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        temperature=0.1,
    )

# ─────────────────────────────────────────────
# Agent 1: Log Analyzer – Analyzes log files to identify issues
# ─────────────────────────────────────────────
log_analyzer = Agent(
    role="DevOps Log Analyzer",
    goal="Analyze log files to identify and extract specific issues, errors, and failure patterns",
    llm=_make_llm(),
    backstory="""You are a senior DevOps engineer with 10 years of experience in
analyzing production logs and identifying critical issues. You excel at parsing
through complex log files, identifying error patterns, extracting relevant error
messages, and determining the root cause of failures from log data.""",
    tools=[log_reader_tool],
    verbose=True,
    max_iter=3,
    max_rpm=10,
    max_execution_time=300,
    respect_context_window=True,
)

# ─────────────────────────────────────────────
# Agent 2: Issue Investigator – Researches solutions
# ─────────────────────────────────────────────
issue_investigator = Agent(
    role="DevOps Issue Investigator",
    goal="Investigate identified issues by searching documentation, forums, and known solutions online",
    llm=_make_llm(),
    backstory="""You are a DevOps troubleshooting specialist who excels at quickly
finding solutions to technical problems. You know how to search effectively for
similar issues, identify reliable sources, and gather comprehensive information
about error patterns and their solutions.""",
    tools=[],
    verbose=True,
    max_iter=5,
    max_rpm=15,
    max_execution_time=600,
    respect_context_window=True,
)

# ─────────────────────────────────────────────
# Agent 3: Solution Specialist – Provides actionable solutions
# ─────────────────────────────────────────────
solution_specialist = Agent(
    role="DevOps Solution Specialist",
    goal="Create detailed, actionable remediation plans based on log analysis and investigation findings",
    llm=_make_llm(),
    backstory="""You are an expert DevOps architect who specializes in creating
comprehensive remediation plans. You translate technical findings into clear,
step-by-step solutions that junior engineers can follow. You always provide
verification steps, rollback procedures, and prevention strategies.""",
    tools=[save_report_tool],
    verbose=True,
    max_iter=3,
    max_rpm=10,
    max_execution_time=300,
    respect_context_window=True,
)
