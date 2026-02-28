import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class DevOpsAgent:
    def __init__(self):
        # Initialize the Azure AI Client
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def analyze_failure(self, logs):
        """
        Sends the logs to the AI and gets a structured JSON response.
        """
        prompt = f"""
        You are an expert DevOps AI. You have been given the raw logs of a failed Azure DevOps pipeline.
        
        LOGS:
        {logs}
        
        TASK:
        1. Identify the root cause of the error.
        2. Propose a specific fix.
        3. Provide a confidence score between 0.0 and 1.0.
        
        Return ONLY valid JSON in this format:
        {{"root_cause": "...", "fix": "...", "confidence": 0.0}}
        """

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content