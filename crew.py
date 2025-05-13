from crewai import Crew
from agents import (
    validator_agent,
    calendar_availability_agent,
    calendar_event_manager_agent,
)
from tasks import (
    validate_task,
    calendar_availability_task,
    calendar_event_manager_task,
)


def kickoff_meeting_prompt_validation(prompt: str):
    """Step 1: Use 3 agents to validate prompt, check calendar, and confirm slot."""
    validate_task.description = f'Prompt: "{prompt}"'

    crew = Crew(
        agents=[validator_agent, calendar_availability_agent],
        tasks=[validate_task, calendar_availability_task],
        verbose=2,
    )

    result = crew.kickoff()
    return result


def kickoff_meeting_creation(input_data: str):
    """Step 2: Use 1 agent to create/cancel the meeting using validated input."""
    calendar_event_manager_task.description = (
        f"Create/Cancel the meeting with this meeting_info: {input_data}"
    )

    crew = Crew(
        agents=[calendar_event_manager_agent],
        tasks=[calendar_event_manager_task],
        verbose=2,
    )

    result = crew.kickoff()
    return result
