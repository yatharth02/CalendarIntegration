from crewai import Task
from agents import (
    validator_agent,
    calendar_availability_agent,
    meeting_scheduler_agent,
)
from tools import (
    validator_tool,
    calendar_availability_tool,
    meeting_scheduler_tool,
)

validate_task = Task(
    name="Validate Prompt Relevance",
    description=(
        f"You are a strict validator for Microsoft Outlook meeting scheduling prompts.\n\n"
        "Instructions:\n"
        "Analyze the prompt and check if it is related to scheduling a meeting in Microsoft Outlook.\n"
        "- Extract:\n"
        "  - meeting title — either extracted or inferred from the prompt. If not explicitly mentioned, infer intelligently based on intent (e.g., sync, catch-up, discussion)\n\n"
        "  - participants (full names)\n"
        "  - natural date (e.g., 'next Monday')\n"
        "  - natural time (e.g., '5pm')\n\n"
        " You must call the `validator_main_tool(prompt, natural_date, participants)` tool exactly once to perform all validations.\n\n"
        " **Output ONLY the result from the tool.**"
        "**Important:**"
        "- Do NOT call any tool more than once with the same input."
        "- Store and reuse the output from previous tool calls."
        "- You must build the final JSON using the tool responses — never retry them unless input changes."
    ),
    expected_output="A structured JSON only as per the tool.",
    agent=validator_agent,
    output_key="validator_data",
    tools=[validator_tool],
)


calendar_availability_task = Task(
    name="Check Calendar Availability",
    description=(
        "You are responsible for checking which timeslots are mutually free for all participants "
        "on a given date using Google Calendar. Extracted data_dict will be given as dictionary:\n"
        '{ "data_dict": {"status": "status", "meeting_info": "meeting_info"} }\n\n'
        "DO NOT think, reason, explain, or generate output yourself.\n\n"
        "ONLY call the tool: `check_calendar_availability(data_dict)`\n"
        "The tool will check mutual availability for all participants and return available slots.\n\n"
        " **Output ONLY the result from the tool.**"
        "**Do not re-check participants or date. Only check mutual availability.**\n"
        "**Respond only with raw JSON. No markdown, no explanations.**"
    ),
    expected_output="A structured JSON only as per the tool.",
    context=[validate_task],
    agent=calendar_availability_agent,
    output_key="calendar_check_data",
    tools=[calendar_availability_tool],
)


meeting_scheduler_task = Task(
    name="Schedule Meeting and Send Invite",
    description=(
        " Extracted data_dict will be given as dictionary:\n"
        '{ "meeting_info": "meeting_info" }\n\n'
        "DO NOT think, reason, explain, or generate output yourself.\n\n"
        "- Call the tool `create_calendar_event(data_dict)`.\n"
        " **Output ONLY the result from the tool.**"
        "**Return only the final JSON — no notes or markdown.**"
    ),
    expected_output="A structured JSON only as per the tool.",
    context=[human_confirmation_task],
    agent=meeting_scheduler_agent,
    tools=[meeting_scheduler_tool],
    output_key="final_invite_sent",
)
