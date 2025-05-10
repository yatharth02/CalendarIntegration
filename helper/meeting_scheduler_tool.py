import os, json, time
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from crewai_tools import BaseTool

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class MeetingSchedulerTool(BaseTool):
    name: str = "Meeting Scheduler Tool"
    description: str = (
        "Schedules the confirmed meeting using Google Calendar and returns an event link."
    )

    def _run(self, meeting_info: dict):
        print("[MeetingSchedulerTool] TOOL STARTED")
        start = time.time()

        try:
            title = meeting_info.get("title")
            date = meeting_info.get("date")
            confirmed_slot = meeting_info.get("confirmed_slot")
            participant_emails = meeting_info.get("participant_emails")

            start_str, end_str = confirmed_slot.split("–")
            IST = timezone(timedelta(hours=5, minutes=30))
            start_dt = (
                datetime.strptime(f"{date} {start_str}", "%Y-%m-%d %H:%M")
                .replace(tzinfo=IST)
                .isoformat()
            )
            end_dt = (
                datetime.strptime(f"{date} {end_str}", "%Y-%m-%d %H:%M")
                .replace(tzinfo=IST)
                .isoformat()
            )

            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            service = build("calendar", "v3", credentials=creds)

            event_body = {
                "summary": title,
                "location": "Google Meet",
                "description": f"{title} scheduled via CrewAI",
                "start": {"dateTime": start_dt, "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_dt, "timeZone": "Asia/Kolkata"},
                "attendees": [{"email": e} for e in participant_emails],
                "conferenceData": {
                    "createRequest": {
                        "requestId": f"{title.lower().replace(' ', '-')}-{date}"
                    }
                },
            }

            event_result = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    conferenceDataVersion=1,
                    sendUpdates="all",
                )
                .execute()
            )

            meeting_info["event_link"] = event_result.get("htmlLink")
            return json.dumps({"status": "SUCCESS", "meeting_info": meeting_info})

        except HttpError as e:
            return json.dumps({"status": "FAILED", "error": str(e)})

        finally:
            print(f"[MeetingSchedulerTool] Took {round(time.time() - start, 2)}s")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
