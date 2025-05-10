# 📅 Calendar Integration with CrewAI

An intelligent meeting scheduling assistant built with **CrewAI**, **LangChain**, **Google Calendar API**, and **Streamlit**. This app processes natural language prompts to:

- Validate if the prompt is a meeting request.
- Check your calendar for available time slots.
- Confirm with the user to choose a slot.
- Schedule a meeting in Google Calendar automatically.

---

## 🚀 Features

- ✅ Prompt validation using LLM (CrewAI agent)
- 📆 Calendar slot lookup using Google Calendar API
- 🧠 Human confirmation via dropdown
- 🛠️ Automatic meeting creation with invite link
- 🖥️ Streamlit UI for easy interaction

---

## 🧠 CrewAI Agents & Their Responsibilities

| Agent Name                | Description                                                                 | Uses                                                                 |
|--------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------|
| `prompt_validation_agent`| Validates if the user prompt is related to meeting scheduling               | `ValidatorTool` – LLM-based classification                           |
| `check_calendar_agent`   | Retrieves available slots from user's Google Calendar                       | `CalendarAvailabilityTool` – Google Calendar API, time parsing      |
| `human_confirmation_agent`| Simulates or handles human confirmation flow                               | `HumanConfirmationTool` – User input from Streamlit UI              |
| `meeting_creation_agent` | Creates the meeting in user's Google Calendar and returns invite link       | `MeetingSchedulerTool` – Google Calendar API, event generation      |

---

## 📁 Project Structure

```
outlook-meeting-scheduler/
├── agents.py                         # CrewAI agent definitions
├── tasks.py                          # CrewAI task definitions
├── crew.py                         # Kickoff methods using CrewAI
├── tools/
│   ├── __init__.py
│   ├── validator_tool.py             # LLM validation tool
│   ├── calendar_availability_tool.py # Google Calendar slot checker
│   ├── human_confirmation_tool.py    # Tool for user slot confirmation
│   └── meeting_scheduler_tool.py     # Google Calendar event creator
├── streamlit_app.py                  # Main Streamlit UI app
├── credentials/                      # Google API credentials
│   └── token.json
│   └── credentials.json
├── requirements.txt
└── README.md
```

---

## 🛠️ Setup Instructions

### 1. 🔑 Google Calendar API Setup

- Go to [Google Cloud Console](https://console.cloud.google.com/).
- Enable **Google Calendar API**.
- Create OAuth 2.0 credentials (Desktop App).
- Download the `credentials.json` and save in `credentials/` folder.

> On first run, it will open a browser to authorize access and generate `token.json`.

---

### 2. 🐍 Install Dependencies

```bash
git clone https://github.com/yatharth02/CalendarIntegration.git
cd CalendarIntegration

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate (Windows)

pip install -r requirements.txt
```

---

### 3. 🚀 Run the App

```bash
streamlit run streamlit_app.py
```

---

## 🔄 App Workflow

### 🔹 Phase 1: Validation & Time Slot Extraction

Function: `kickoff_meeting_prompt_validation(prompt: str)`

- Agent-1 (`prompt_validation_agent`): Validates if prompt is for a meeting.
- Agent-2 (`check_calendar_agent`): Checks calendar for available time slots.
- Agent-3 (`human_confirmation_agent`): Waits for user slot selection via UI.

### 🔹 Phase 2: Meeting Creation

Function: `kickoff_meeting_creation(data_dict: dict)`

- Agent-4 (`meeting_creation_agent`): Creates the event in Google Calendar and returns the invite link.

---

## 🧪 Sample Prompt

```text
Schedule a team meeting with Deoly and Part for tomorrow for 30 mins in morning
```

---

## 📸 UI Screenshots

> Coming soon: Screenshots of each stage from Streamlit UI.

---

## 🔐 Environment Variables (Optional)

If needed, you can set:
- `GOOGLE_API_SCOPES`
- `GOOGLE_TOKEN_FILE`

---

## 📦 requirements.txt

```
streamlit
crewai
langchain
google-auth
google-auth-oauthlib
google-api-python-client
```

---

## 👨‍💻 Credits

Built by __*Yatharth Deoly*__ using:

- [Streamlit](https://streamlit.io/)
- [CrewAI](https://github.com/joaomdmoura/crewai)
- [LangChain](https://www.langchain.com/)
- [Google Calendar API](https://developers.google.com/calendar)