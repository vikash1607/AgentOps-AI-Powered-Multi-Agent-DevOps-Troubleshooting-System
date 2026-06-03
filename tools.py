import os
from crewai.tools import tool


@tool("Log File Reader")
def log_reader_tool(file_path: str) -> str:
    """
    Reads a log file from the given file path and returns its contents.
    Use this tool to read log files for analysis.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at path: {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return "Warning: The log file is empty."

        return f"=== Log File Contents: {file_path} ===\n\n{content}"

    except PermissionError:
        return f"Error: Permission denied when reading file: {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool("Save Report to File")
def save_report_tool(content: str, file_path: str) -> str:
    """
    Saves a report or analysis result to the specified file path.
    Use this tool to persist analysis results.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Report successfully saved to: {file_path}"
    except Exception as e:
        return f"Error saving report: {str(e)}"
