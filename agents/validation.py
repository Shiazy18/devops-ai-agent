import re
import subprocess
import json
from services.llm import get_llm

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def run(state):
    try:
        llm = get_llm()
        # deterministic validation
        test_code, test_output = run_command("pytest")
        lint_code, lint_output = run_command("flake8 .")
        