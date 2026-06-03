"""
AgentOps – Production Features
Mirrors the structure shown in 02_production_features.ipynb

Adds:
  - Output guardrails (validate_log_analysis)
  - Pydantic-enforced structured output
  - Verbose retry on rejection
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from crewai import Crew, Process, Task
from crewai.tasks.task_output import TaskOutput
from typing import Tuple, Any

from agents import log_analyzer
from tasks import LogAnalysisReport, validate_log_analysis
from tools import log_reader_tool

# ─────────────────────────────────────────────
# "Tricky" log that has only INFO entries – agent must retry
# ─────────────────────────────────────────────
TRICKY_LOG_INPUT = """
[2024-01-16 10:00:00.001] INFO: System health check started
[2024-01-16 10:00:01.002] INFO: All services operational
[2024-01-16 10:00:02.003] INFO: Memory usage: 45%
[2024-01-16 10:00:03.004] INFO: CPU usage: 12%
[2024-01-16 10:00:04.005] INFO: Disk usage: 67%
[2024-01-16 10:00:05.006] WARNING: Disk usage approaching threshold (67% of 80%)
[2024-01-16 10:00:06.007] INFO: Health check complete
"""

_tmp_tricky_path = os.path.join(os.path.dirname(__file__), "task_outputs", "_tmp_tricky.log")
os.makedirs(os.path.dirname(_tmp_tricky_path), exist_ok=True)
with open(_tmp_tricky_path, "w") as f:
    f.write(TRICKY_LOG_INPUT)


def run_production_pipeline(log_content: str = None, log_file_path: str = None, verbose: bool = True) -> dict:
    """
    Production pipeline with guardrail validation.

    The guardrail rejects outputs that contain zero errors, forcing the agent
    to dig deeper into INFO/WARNING messages to find real issues.
    """
    if log_content:
        tmp = os.path.join(os.path.dirname(__file__), "task_outputs", "_tmp_prod.log")
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        with open(tmp, "w") as f:
            f.write(log_content)
        path = tmp
    else:
        path = log_file_path or _tmp_tricky_path

    # ─────────────────────────────────────────────
    # Task with guardrail attached
    # ─────────────────────────────────────────────
    guarded_task = Task(
        description=f"Analyze the following log data to identify issues:\n{path}",
        expected_output="A structured log analysis report",
        output_pydantic=LogAnalysisReport,
        guardrail=validate_log_analysis,
        agent=log_analyzer,
    )

    guarded_crew = Crew(
        agents=[log_analyzer],
        tasks=[guarded_task],
        process=Process.sequential,
        verbose=verbose,
    )

    guarded_result = guarded_crew.kickoff(inputs={"log_data": TRICKY_LOG_INPUT})

    output = guarded_crew.tasks[0].output
    return {
        "analysis": output.pydantic if output else None,
        "raw_result": guarded_result,
    }


if __name__ == "__main__":
    print("\n[Production Pipeline] Running with guardrail...\n")
    result = run_production_pipeline(verbose=True)
    if result["analysis"]:
        a = result["analysis"]
        print(f"\nSeverity  : {a.severity}")
        print(f"Root Cause: {a.root_cause}")
        print(f"Errors    : {len(a.errors)}")
