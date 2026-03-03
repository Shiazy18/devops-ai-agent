import re

ERROR_PATTERNS = [
    r"##\[error\]([^\n]+)",  # Azure DevOps error pattern
    r"ERROR:\s*(.*)",         # Generic error pattern
    r"Exception:\s*(.*)",     # Exception pattern
    r"Traceback \(most recent call last\):([\s\S]+?)(?=^\S|\Z)"  # Python traceback pattern
    r"^.*\berror\b.*$",       # Any line containing the word "error"
    r"^.*\bfail\b.*$",        # Any line containing the word "fail"
]

class LogProcessor:
    def extract_errors(self, logs):
        lines = logs.splitlines()
        blocks = []
        current_block = []

        for line in lines:
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in ERROR_PATTERNS):
                if current_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
            current_block.append(line)

        if current_block:
            blocks.append("\n".join(current_block))

        return blocks[:5]  # Return top 5 error blocks to avoid overwhelming the LLM