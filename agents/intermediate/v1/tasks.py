import os
from crewai import Task
from pydantic import BaseModel, Field
from typing import List, Optional


# ─────────────────────────────────────────────
# Pydantic Output Models
# ─────────────────────────────────────────────

class LogError(BaseModel):
    timestamp: str = Field(description="Timestamp of the error")
    level: str = Field(description="Log level: ERROR, CRITICAL, WARNING, INFO")
    message: str = Field(description="Full error message")
    component: Optional[str] = Field(default=None, description="Affected component or service")


class LogAnalysisReport(BaseModel):
    summary: str = Field(description="Brief summary of the primary issue")
    errors: List[LogError] = Field(description="List of identified errors")
    root_cause: str = Field(description="Root cause analysis")
    affected_components: List[str] = Field(description="List of affected system components")
    timeline: str = Field(description="Timeline of failure events")
    severity: str = Field(description="Overall severity: LOW, MEDIUM, HIGH, CRITICAL")


class InvestigationReport(BaseModel):
    issue_summary: str = Field(description="Summary of investigated issue")
    similar_issues: List[str] = Field(description="Similar known issues found")
    common_causes: List[str] = Field(description="Common causes ranked by likelihood")
    community_solutions: List[str] = Field(description="Community-verified solutions")
    documentation_links: List[str] = Field(description="Links to official documentation")
    best_practices: List[str] = Field(description="Best practices to prevent similar issues")


class RemediationStep(BaseModel):
    step_number: int
    command: Optional[str] = Field(default=None, description="Shell command to run")
    description: str = Field(description="What this step does")
    expected_output: Optional[str] = Field(default=None, description="Expected result")


class SolutionPlan(BaseModel):
    title: str = Field(description="Title of the remediation plan")
    primary_solution: List[RemediationStep] = Field(description="Step-by-step fix commands")
    verification_steps: List[str] = Field(description="Steps to verify the fix worked")
    prevention_strategies: List[str] = Field(description="Monitoring and prevention measures")
    rollback_procedure: List[str] = Field(description="Rollback steps if fix fails")
    estimated_resolution_time: str = Field(description="Estimated time to resolve")


# ─────────────────────────────────────────────
# Task Factories
# ─────────────────────────────────────────────

def create_analyze_task(log_analyzer_agent, log_file_path: str) -> Task:
    return Task(
        description=f"""Analyze the following log file to identify issues:\n{log_file_path}

        Read the log file using the Log File Reader tool, then:
        1. Identify all ERROR and CRITICAL level entries
        2. Extract key error messages and codes
        3. Build a timeline of failure events
        4. Determine the root cause of the primary failure
        5. List all affected components""",
        expected_output="""A detailed analysis report containing:
        - Primary issue description
        - Key error messages and codes
        - Timeline of failure events
        - Root cause analysis
        - Affected components""",
        output_pydantic=LogAnalysisReport,
        agent=log_analyzer_agent,
        output_file="task_outputs/analysis_report.md",
    )


def create_investigate_task(issue_investigator_agent, analyze_task: Task) -> Task:
    return Task(
        description="""Based on the log analysis findings, investigate the identified issues.

        Your investigation should:
        1. Research the specific error messages and codes found
        2. Find similar issues in the DevOps community
        3. Identify the most common causes ranked by likelihood
        4. Gather community-verified solutions
        5. Reference official documentation""",
        expected_output="""A comprehensive investigation report including:
        - Similar issues found online with references
        - Official documentation links
        - Common causes ranked by likelihood
        - Community-verified solutions
        - Best practices to prevent similar issues""",
        output_pydantic=InvestigationReport,
        agent=issue_investigator_agent,
        context=[analyze_task],
        output_file="task_outputs/investigation_report.md",
    )


def create_solution_task(solution_specialist_agent, analyze_task: Task, investigate_task: Task) -> Task:
    return Task(
        description="""Based on the log analysis and investigation findings, provide a complete solution.

        Your solution should:
        1. Create a step-by-step remediation plan with specific commands
        2. Provide verification steps to confirm the fix
        3. Suggest monitoring and prevention measures
        4. Include rollback procedures if needed
        5. Reference official documentation""",
        expected_output="""A detailed remediation plan with:
        - Primary solution with step-by-step commands
        - Verification and testing procedures
        - Prevention strategies and monitoring recommendations
        - Rollback plan in case of issues
        - Links to official documentation""",
        output_pydantic=SolutionPlan,
        agent=solution_specialist_agent,
        context=[analyze_task, investigate_task],
        output_file="task_outputs/solution_plan.md",
    )


# ─────────────────────────────────────────────
# Guardrail for production notebook (02_production_features)
# ─────────────────────────────────────────────

from crewai.tasks.task_output import TaskOutput
from typing import Tuple, Any


def validate_log_analysis(result: TaskOutput) -> Tuple[bool, Any]:
    """
    Guardrail function that validates task output before it's accepted.
    Returns:
        (True, data)  — output is good, pass it through
        (False, reason) — output is rejected, agent retries automatically
    """
    report = result.pydantic
    if not report or not report.errors:
        return (False, "Must identify at least one error")
    return (True, report)
