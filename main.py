"""
AgentOps – Multi-Agent DevOps Troubleshooting System
Mirrors the structure shown in 01_multi_agent_pipeline.ipynb
"""

import os
import sys

# Make sure local modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from crewai import Crew, Process
from agents import log_analyzer, issue_investigator, solution_specialist
from tasks import create_analyze_task, create_investigate_task, create_solution_task

# ─────────────────────────────────────────────
# Sample log input (mirrors Step 2 in the notebook)
# ─────────────────────────────────────────────
LOG_INPUT = """
[2024-01-15 14:32:15.123] INFO: Starting deployment of myapp-deployment
[2024-01-15 14:32:16.567] WARNING: Pod myapp-deployment-7b8c9d5f4-abc12 in Pending state
[2024-01-15 14:32:17.890] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 failed to start
[2024-01-15 14:32:18.123] ERROR: Failed to pull image "myapp:v1.2.3": pull access denied, repository does not exist or may require 'docker login': denied: requested access to the resource is denied
[2024-01-15 14:32:18.456] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 status: ImagePullBackOff
[2024-01-15 14:32:25.901] ERROR: Deployment rollout failed: deployment "myapp-deployment" exceeded its progress deadline
[2024-01-15 14:32:26.789] WARNING: Service myapp-service has no available endpoints
[2024-01-15 14:32:29.456] CRITICAL: Production deployment failed - rollback initiated
"""

# ─────────────────────────────────────────────
# Write inline log to a temp file so the log_reader_tool can read it
# ─────────────────────────────────────────────
_tmp_log_path = os.path.join(os.path.dirname(__file__), "task_outputs", "_tmp_inline.log")
os.makedirs(os.path.dirname(_tmp_log_path), exist_ok=True)
with open(_tmp_log_path, "w") as f:
    f.write(LOG_INPUT)


def run_pipeline(log_file_path: str = None, verbose: bool = True) -> dict:
    """
    Run the full 3-agent DevOps pipeline.

    Args:
        log_file_path: Path to a log file. Defaults to the inline sample log.
        verbose: Whether to print crew execution details.

    Returns:
        dict with keys: analysis, investigation, solution, raw_result
    """
    path = log_file_path or _tmp_log_path

    # Build tasks
    analyze_task = create_analyze_task(log_analyzer, path)
    investigate_task = create_investigate_task(issue_investigator, analyze_task)
    solution_task = create_solution_task(solution_specialist, analyze_task, investigate_task)

    # ─────────────────────────────────────────────
    # Full Pipeline Crew  (Step 8 in the notebook)
    # ─────────────────────────────────────────────
    devops_crew = Crew(
        agents=[log_analyzer, issue_investigator, solution_specialist],
        tasks=[analyze_task, investigate_task, solution_task],
        process=Process.sequential,
        verbose=verbose,
        cache=True,
        max_rpm=30,
    )

    result = devops_crew.kickoff(inputs={"log_file_path": path})

    # Parse pydantic outputs safely
    outputs = devops_crew.tasks
    analysis = outputs[0].output.pydantic if outputs[0].output else None
    investigation = outputs[1].output.pydantic if outputs[1].output else None
    solution = outputs[2].output.pydantic if outputs[2].output else None

    return {
        "analysis": analysis,
        "investigation": investigation,
        "solution": solution,
        "raw_result": result,
    }


# ─────────────────────────────────────────────
# CLI entrypoint
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AgentOps – DevOps Log Analyzer")
    parser.add_argument(
        "--log-file",
        default=None,
        help="Path to a log file (defaults to the built-in sample log)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress verbose crew output"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  AgentOps – Multi-Agent DevOps Troubleshooting System")
    print("=" * 60 + "\n")

    results = run_pipeline(log_file_path=args.log_file, verbose=not args.quiet)

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)

    if results["analysis"]:
        print(f"\n[Analysis] Severity  : {results['analysis'].severity}")
        print(f"[Analysis] Root Cause: {results['analysis'].root_cause}")
        print(f"[Analysis] Errors    : {len(results['analysis'].errors)} found")

    if results["solution"]:
        print(f"\n[Solution] {results['solution'].title}")
        print(f"[Solution] Est. resolution time: {results['solution'].estimated_resolution_time}")
        print(f"[Solution] Steps: {len(results['solution'].primary_solution)}")

    print("\nOutput files written to task_outputs/")
