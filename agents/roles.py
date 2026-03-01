# agents/roles.py
from crewai import Agent
from dotenv import load_dotenv
from tools import CreateBugTool, FetchLogsTool

import os
from langchain_openai import AzureChatOpenAI

load_dotenv()
# Initialize the Azure OpenAI connection
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    temperature=0.1,
    max_retries=3,
)

# Architect: The Diagnoser
architect = Agent(
    role='DevOps Architect',
    goal='Diagnose the root cause of pipeline failures.',
    backstory='You are a senior DevOps expert.',
    tools=[FetchLogsTool()],  # Architect can fetch logs to diagnose
    llm=llm,  # <--- HERE IS THE BRAIN
    verbose=True
)


# Manager: The Closer
manager = Agent(
    role='Bug Tracker',
    goal='Ensure the bug is logged.',
    backstory='You are organized.',
    tools=[CreateBugTool()], # CreateBugTool will be invoked explicitly where needed
    llm=llm,  # <--- HERE IS THE BRAIN
    verbose=True
)


# Engineer: The Fixer
engineer = Agent(
    role='Software Engineer',
    goal='Propose and implement a code fix for the diagnosed issue.',
    backstory='You are pragmatic and focused on reliable fixes.',
    tools=[],
    llm=llm,
    verbose=True
)