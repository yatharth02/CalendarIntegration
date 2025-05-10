from crewai import Crew
from agents import (
    validator_agent,
    calendar_availability_agent,
    meeting_scheduler_agent,
)
from tasks import (
    validate_task,
    calendar_availability_task,
    meeting_scheduler_task,
)


def kickoff_meeting_prompt_validation(prompt: str):
    """Step 1: Use 3 agents to validate prompt, check calendar, and confirm slot."""
    validate_task.description = (
        f"Check if the following prompt is related to Outlook meeting scheduling:\n\n"
        f'Prompt: "{prompt}"'
    )

    crew = Crew(
        agents=[validator_agent, calendar_availability_agent],
        tasks=[validate_task, calendar_availability_task],
        verbose=2,
    )

    result = crew.kickoff()
    return result


def kickoff_meeting_creation(input_data: str):
    """Step 2: Use 1 agent to create the meeting using validated input."""
    meeting_scheduler_task.description = (
        f"Create the meeting with this meeting_info: {input_data}"
    )

    crew = Crew(
        agents=[meeting_scheduler_agent], tasks=[meeting_scheduler_task], verbose=2
    )

    result = crew.kickoff()
    return result
