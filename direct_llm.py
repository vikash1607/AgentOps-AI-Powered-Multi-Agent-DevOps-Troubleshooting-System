"""
Direct LLM Analysis – baseline comparison against the multi-agent pipeline.
Uses raw OpenAI API with a single prompt, no agent orchestration.

NOTE: The OpenAI client is created inside analyze_with_direct_llm() so it
always picks up the OPENAI_API_KEY that was set (e.g. from the Streamlit
sidebar) rather than the value present at import time.
"""

import os
import time


SYSTEM_PROMPT = """You are a DevOps engineer. Analyze the provided log data and return a structured report.

Your report must include:
1. Summary of the primary issue
2. List of all errors with timestamps and severity
3. Root cause analysis
4. Affected components
5. Timeline of events
6. Overall severity (LOW / MEDIUM / HIGH / CRITICAL)
7. Recommended fix steps

Be concise but thorough."""


def analyze_with_direct_llm(log_content: str, model: str = "gpt-4o-mini") -> dict:
    """
    Analyze log content using a single direct LLM call (no agents).

    The OpenAI client is instantiated here so it always reads the current
    value of OPENAI_API_KEY from the environment, even if the key was set
    after this module was first imported.

    Returns:
        dict with keys: response_text, model, tokens_used,
                        prompt_tokens, completion_tokens, elapsed_seconds
    """
    # Late import + late client creation = always uses current env key
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Please enter your API key in the Streamlit sidebar."
        )

    client = OpenAI(api_key=api_key)

    start = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Please analyze the following log data:\n\n{log_content}",
            },
        ],
        temperature=0.1,
        max_tokens=1500,
    )

    elapsed = time.time() - start

    return {
        "response_text":       response.choices[0].message.content,
        "model":               response.model,
        "tokens_used":         response.usage.total_tokens,
        "prompt_tokens":       response.usage.prompt_tokens,
        "completion_tokens":   response.usage.completion_tokens,
        "elapsed_seconds":     round(elapsed, 2),
    }


if __name__ == "__main__":
    sample_log = """
[2024-01-15 14:32:15.123] INFO: Starting deployment of myapp-deployment
[2024-01-15 14:32:17.890] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 failed to start
[2024-01-15 14:32:18.123] ERROR: Failed to pull image "myapp:v1.2.3": pull access denied
[2024-01-15 14:32:18.456] ERROR: Pod status: ImagePullBackOff
[2024-01-15 14:32:29.456] CRITICAL: Production deployment failed - rollback initiated
"""
    result = analyze_with_direct_llm(sample_log)
    print(f"Model     : {result['model']}")
    print(f"Tokens    : {result['tokens_used']}")
    print(f"Time (s)  : {result['elapsed_seconds']}")
    print(f"\nResponse:\n{result['response_text']}")
