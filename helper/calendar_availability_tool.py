# calendar_availability_tool.py
import os, json, time
from datetime import datetime, timedelta, timezone
from crewai_tools import BaseTool
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarAvailabilityTool(BaseTool):
    name: str = "Calendar Availability Tool"
    description: str = (
        "Checks which of the provided timeslots are free for all participants on the given date."
    )

    def _run(self, data_dict: dict):
        print("[CalendarAvailabilityTool] TOOL STARTED")
        start = time.time()

        try:
            status = data_dict.get("status")
            if not status or status.upper() == "INVALID":
                return json.dumps(data_dict)

            meeting_info = data_dict.get("meeting_info")
            participant_emails = meeting_info["participant_emails"]
            timeslots = meeting_info["timeslots"]
            date = meeting_info["date"]

            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            service = build("calendar", "v3", credentials=creds)
            fmt = "%Y-%m-%dT%H:%M:%S%z"
            IST = timezone(timedelta(hours=5, minutes=30))

            def is_slot_free(calendar_id, start_iso, end_iso):
                events = (
                    service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=start_iso,
                        timeMax=end_iso,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                    .get("items", [])
                )
                return len(events) == 0

            freetimeslots = []
            for slot in timeslots:
                slot_start, slot_end = slot.split("–")
                start_dt = datetime.strptime(f"{date} {slot_start}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date} {slot_end}", "%Y-%m-%d %H:%M")
                start_iso = start_dt.replace(tzinfo=IST).isoformat()
                end_iso = end_dt.replace(tzinfo=IST).isoformat()

                all_free = all(
                    is_slot_free(email, start_iso, end_iso)
                    for email in participant_emails
                )
                if all_free:
                    freetimeslots.append(slot)

            meeting_info["freetimeslots"] = freetimeslots
            return json.dumps({"status": "VALID", "meeting_info": meeting_info})

        finally:
            print(f"[CalendarAvailabilityTool] Took {round(time.time() - start, 2)}s")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
