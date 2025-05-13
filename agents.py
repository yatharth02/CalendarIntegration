from crewai import Agent
from langchain.chat_models import ChatOpenAI
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
# llm = ChatOpenAI(
#     model_name="gpt-4o-mini-2024-07-18",
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
#     temperature=0,
# )

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash-latest")

# Agent 1: Unified Validator Agent
validator_agent = Agent(
    name="UnifiedValidatorAgent",
    role="Validation Orchestrator",
    goal="Analyze the user prompt and validate intent, participants, time, office policy, and timezones.",
    description=(
        "An intelligent validator that performs comprehensive validation of prompts for Outlook meeting scheduling. "
        "It ensures the prompt is relevant, validates participant identities, checks date feasibility, "
        "verifies office hours and holidays, and ensures timezone compatibility."
    ),
    backstory=(
        "You are the first checkpoint in an AI meeting scheduling pipeline. Your role is to make sure that everything "
        "from prompt intent to policy checks is handled before availability lookup and scheduling happens."
    ),
    allow_delegation=False,
    llm=llm,
    cache=True,
)

# Agent 2: Calendar Availability Agent
calendar_availability_agent = Agent(
    name="CalendarAvailabilityAgent",
    role="Calendar Availability Validator",
    goal="Identify mutually available timeslots from Google Calendar for all attendees.",
    description=(
        "You check participant calendars to identify common free timeslots based on validated input."
    ),
    backstory=(
        "You're the calendar coordination specialist who ensures the meeting can be scheduled when everyone is free."
    ),
    allow_delegation=False,
    llm=llm,
)

# Agent 3: Calendar Event Manager Agent
calendar_event_manager_agent = Agent(
    name="Calendar Event Manager Agent",
    role="Calendar Event Manager",
    goal="Schedule, reschedule, or cancel meetings using Google Calendar integration.",
    description=(
        "You finalize the meeting by creating, updating, or canceling the calendar event and sending invites."
    ),
    backstory=(
        "You're the calendar operator responsible for creating accurate and timely events for all participants."
    ),
    allow_delegation=False,
    llm=llm,
)
