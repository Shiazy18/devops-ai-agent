from crewai import Crew, Task, Process
from agents.roles import architect, engineer, manager

def run_remediation(build_id):
    # Tasks
    #t1 = Task(description=f"Fetch logs for {build_id} and diagnose failure.", agent=architect)
    t1 = Task(
        description="Fetch logs and diagnose failure.",
        agent=architect,
        inputs={"build_id": build_id}
    )
    t2 = Task(
        description="Create a code fix plan.", 
        agent=engineer, context=[t1])
    
    t3 = Task(
        description="Log the bug in Azure DevOps.", 
        agent=manager, context=[t2])

    # Crew
    crew = Crew(
        agents=[architect, engineer, manager],
        tasks=[t1, t2, t3],
        process=Process.sequential
    )
    return crew.kickoff()