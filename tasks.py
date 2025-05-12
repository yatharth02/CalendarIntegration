from crewai import Task
from agents import (
    validator_agent,
    calendar_availability_agent,
    calendar_event_manager_agent,
)
from tools import (
    validator_tool,
    calendar_availability_tool,
    calendar_event_manager_tool,
)

validate_task = Task(
    name="Validate Prompt Relevance",
    description=(
        "Use the tool to validate and extract meeting details.\n"
        "- Input: prompt, natural date, participants\n"
        "**Rules:**\n"
        "- Call the tool exactly once with the inputs\n"
        "- Do not retry or reprocess\n"
        "- Return only the tool’s output without explanation or formatting"
    ),
    expected_output="A structured JSON only as per the tool.",
    agent=validator_agent,
    output_key="validator_data",
    tools=[validator_tool],
)


calendar_availability_task = Task(
    name="Check Calendar Availability",
    description=(
        "Use tool to find mutually free timeslots for all participants.\n"
        "- Input: { 'data_dict': { 'status': ..., 'meeting_info': ... } }\n"
        "**Rules:**\n"
        "- Call the tool once; do not re-check or explain\n"
        "- Return only raw JSON output from the tool without markdown or reasoning"
    ),
    expected_output="A structured JSON only as per the tool.",
    context=[validate_task],
    agent=calendar_availability_agent,
    output_key="calendar_check_data",
    tools=[calendar_availability_tool],
)


calendar_event_manager_task = Task(
    name="Schedule Meeting and Send Invite or Cancel Meeting",
    description=(
        "Use tool to schedule/cancel the meeting.\n"
        "- Input: { 'meeting_info': ... }\n"
        "**Rules:**\n"
        "- Do not think or explain\n"
        "- Return only the raw JSON result from the tool — no notes or markdown"
    ),
    expected_output="A structured JSON only as per the tool.",
    agent=calendar_event_manager_agent,
    tools=[calendar_event_manager_tool],
    output_key="final_invite_sent",
)
