import json, time
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from crewai_tools import BaseTool
from utils import get_credentials


class CalendarEventManagerTool(BaseTool):
    name: str = "Calendar Event Manager Tool"
    description: str = (
        "Schedules or cancels a meeting on Google Calendar and returns the status with event link or cancellation result."
    )

    def _run(self, meeting_info: dict):
        print("[MeetingSchedulerTool] TOOL STARTED")
        start = time.time()
        try:
            creds = get_credentials()
            service = build("calendar", "v3", credentials=creds)
            intent = meeting_info.get("intent", "schedule").lower()

            if intent == "cancel":
                return self._cancel_event(service, meeting_info)
            else:
                return self._schedule_event(service, meeting_info)

        except Exception as e:
            return json.dumps({"status": "INVALID", "reason": f"Internal error"})

        finally:
            print(f"[MeetingSchedulerTool] Took {round(time.time() - start, 2)}s")

    def _schedule_event(self, service, info):
        title = info.get("title")
        date = info.get("date")
        confirmed_slot = info.get("confirmed_slot")
        participant_emails = info.get("participant_emails")
        reason = info.get("reason", "")

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

        event_body = {
            "summary": title,
            "location": "Google Meet",
            "description": f"{title} scheduled via CrewAI"
            + (f"\nReason: {reason}" if reason else ""),
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

        info["event_link"] = event_result.get("htmlLink")
        return json.dumps({"status": "SUCCESS", "meeting_info": info})

    def _cancel_event(self, service, info):
        email = info.get("participant_emails", [None])[0]
        cancel_ids = info.get("cancel_ids", [])
        calendar_events = info.get("calendar_events", [])

        if not email or not cancel_ids or not calendar_events:
            return json.dumps(
                {"status": "FAILED", "error": "Missing email or event IDs to cancel."}
            )

        id_to_summary = {
            e["event_id"]: e.get("event_summary", "(No Title)") for e in calendar_events
        }
        results = []
        for event_id in cancel_ids:
            try:
                service.events().delete(
                    calendarId=email, eventId=event_id, sendUpdates="all"
                ).execute()
                results.append(
                    {
                        "event_summary": id_to_summary.get(event_id, "(Unknown Title)"),
                        "status": "CANCELLED",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "event_summary": id_to_summary.get(event_id, "(Unknown Title)"),
                        "status": "FAILED",
                    }
                )
        return json.dumps(
            {
                "status": (
                    "PARTIAL"
                    if any(r["status"] == "FAILED" for r in results)
                    else "SUCCESS"
                ),
                "cancelled_events": results,
            }
        )

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
