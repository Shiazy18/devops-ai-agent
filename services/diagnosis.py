from services.llm import get_llm
import re

def diagnose_pipeline_failure(logs: str) -> dict:
        # --- Post-processing: Known failure patterns ---
        known_patterns = [
            {
                "pattern": r"Pool 'Default' was changed to 'Linux' unexpectedly",
                "expected_failure_types": ["pipeline"],
                "expected_root_cause": "Pipeline pool configuration changed unexpectedly.",
                "expected_files": ["/azure-pipelines.yml"]
            },
            {
                "pattern": r"ModuleNotFoundError: No module named 'requests'",
                "expected_failure_types": ["application"],
                "expected_root_cause": "Missing Python package 'requests'.",
                "expected_files": ["/requirements.txt"]
            },
            {
                "pattern": r"No space left on device",
                "expected_failure_types": ["infrastructure"],
                "expected_root_cause": "Build agent ran out of disk space.",
                "expected_files": []
            }
        ]

    llm = get_llm()
    # Example input data for testing and prompt enrichment
    example_failure_log = """
    ## Example Pipeline Failure Log
    Job: Build
    Status: Failed
    Error: Pool 'Default' was changed to 'Linux' unexpectedly. This should not happen.
    File: azure-pipelines.yml
    ---
    Job: Test
    Status: Succeeded
    """

    prompt = f"""
    You are a senior DevOps Architect.
    Analyze the complete pipeline logs and look for error messages. 
    Carefully look for error messages as there can be multiple parallel jobs some may have succeeded and some may have failed. 
    Focus on the failed ones.
    If there are no logs, just say no logs found.
    Respond STRICTLY in this format:

    ROOT_CAUSE: <short explanation>
    FAILURE_TYPE: <application | infrastructure | pipeline>
    FILES_TO_MODIFY
    Just give the exact file paths from the repo, no explanations:
    Also if fixable via pipeline, suggest the pipeline file. Only give file paths, no explanations. If no files need to be modified, just say none.
    - <file path 1>
    - <file path 2>
    and so on...
    CONFIDENCE: <0.0 to 1.0>
    No extra text outside this format.

    Logs:
    {logs}

    Example failure log for reference:
    {example_failure_log}
    """
    response = llm.invoke(prompt)
    diagnosis_text = response.content

    failure_type_match = re.search(r"FAILURE_TYPE:\s*(.*)", diagnosis_text)
    confidence = re.search(r"CONFIDENCE:\s*(.*)", diagnosis_text)
    root_cause = re.search(r"ROOT_CAUSE:\s*(.*)", diagnosis_text)
    files = []
    for line in diagnosis_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            file_name = stripped[1:].strip()
            if not file_name.startswith("/"):
                file_name = "/" + file_name
            files.append(file_name)

    # Parse multiple failure types (comma or pipe separated)
    failure_types = []
    if failure_type_match:
        raw_types = failure_type_match.group(1).strip().lower()
        # Accept comma, pipe, or space separated
        for t in re.split(r",|\||\s+", raw_types):
            t = t.strip()
            if t:
                failure_types.append(t)
    if not failure_types:
        failure_types = ["unknown"]

    # Confidence score validation
    conf_score = float(confidence.group(1)) if confidence else 0.0
    if conf_score < 0.6:
        print("[Diagnosis] Low confidence score detected. Human review recommended.")

    # Post-processing: override diagnosis if known pattern matches
    for kp in known_patterns:
        if re.search(kp["pattern"], logs, re.IGNORECASE):
            print(f"[Diagnosis] Known pattern matched: {kp['pattern']}")
            return {
                "raw_text": diagnosis_text + "\n[Post-processed: Known pattern applied]",
                "failure_type": kp["expected_failure_types"],
                "confidence": 1.0,
                "root_cause": kp["expected_root_cause"],
                "files_to_modify": kp["expected_files"]
            }

    return {
        "raw_text": diagnosis_text,
        "failure_type": failure_types,
        "confidence": conf_score,
        "root_cause": root_cause.group(1).strip() if root_cause else "No root cause identified",
        "files_to_modify": files
    }
