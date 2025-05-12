import json, time
from datetime import datetime, timedelta, timezone
from crewai_tools import BaseTool
from googleapiclient.discovery import build
from utils import get_credentials


class CalendarAvailabilityTool(BaseTool):
    name: str = "Calendar Availability Tool"
    description: str = (
        "Checks which of the provided timeslots are free for all participants on the given date, or returns all events if intent is 'cancel'."
    )

    def _run(self, data_dict: dict):
        print("[CalendarAvailabilityTool] TOOL STARTED")
        start = time.time()
        try:
            if data_dict.get("status", "").upper() != "VALID":
                return json.dumps(data_dict)
            info = data_dict.get("meeting_info")
            creds = get_credentials()
            service = build("calendar", "v3", credentials=creds)
            ist = timezone(timedelta(hours=5, minutes=30))
            return (
                self._fetch_events(service, info, ist)
                if info["intent"].lower() == "cancel"
                else self._fetch_freetimes(service, info, ist)
            )
        except Exception as e:
            print(f"Exception -> {e}")
            return json.dumps({"status": "INVALID", "reason": "Internal issues"})
        finally:
            print(f"[CalendarAvailabilityTool] Took {round(time.time() - start, 2)}s")

    def _is_slot_free(self, service, calendar_id, start, end):
        events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )
        return len(events) == 0

    def _fetch_freetimes(self, service, info, ist):
        slots, emails, date = (
            info["timeslots"],
            info["participant_emails"],
            info["date"],
        )
        fmt, free = "%Y-%m-%d %H:%M", []
        for slot in slots:
            s, e = [
                datetime.strptime(f"{date} {t}", fmt).replace(tzinfo=ist).isoformat()
                for t in slot.split("–")
            ]
            if all(self._is_slot_free(service, email, s, e) for email in emails):
                free.append(slot)
        info["freetimeslots"] = free
        return json.dumps({"status": "VALID", "meeting_info": info})

    def _fetch_events(self, service, info, ist):
        date, email = info["date"], info["participant_emails"][0]
        start = (
            datetime.strptime(f"{date} 00:00", "%Y-%m-%d %H:%M")
            .replace(tzinfo=ist)
            .isoformat()
        )
        end = (
            datetime.strptime(f"{date} 23:59", "%Y-%m-%d %H:%M")
            .replace(tzinfo=ist)
            .isoformat()
        )
        events = (
            service.events()
            .list(
                calendarId=email,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )
        if not events:
            info["calendar_events"] = []
        else:
            info["calendar_events"] = [
                {
                    "event_id": e.get("id"),
                    "email": e.get("creator", {}).get("email"),
                    "event_summary": e.get("summary"),
                    "start_time": e.get("start", {}).get("dateTime"),
                    "end_time": e.get("end", {}).get("dateTime"),
                }
                for e in events
                if e.get("creator", {}).get("email") == email
            ]
        return json.dumps({"status": "VALID", "meeting_info": info})

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
