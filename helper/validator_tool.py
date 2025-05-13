import json
import os
import time
import parsedatetime
from datetime import datetime, timedelta
from typing import List
from crewai_tools import BaseTool
from langchain.chat_models import ChatOpenAI

TEST_USER_FILE = "test_users.json"


class ValidatorTool(BaseTool):
    name: str = "Validator Tool"
    description: str = (
        "Performs prompt, date, participant, and timeslot validations for meeting scheduling."
    )

    def _run(
        self,
        natural_date: str,
        participants: List[str],
        prompt: str,
    ):
        print("[ValidatorTool] TOOL STARTED")
        start = time.time()
        global llm
        llm = ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )

        def llm_json(prompt_text):
            try:
                response = llm.invoke(prompt_text)
                content = response.content
                return json.loads(content)
            except Exception as e:
                return {"status": "INVALID", "reason": str(e)}

        def validate_prompt(prompt):
            return llm_json(
                f"""
                Determine if the prompt is related to scheduling, rescheduling, or cancelling a meeting in Microsoft Outlook.
                Return only: {{ "status": "VALID" }} or {{ "status": "INVALID", "reason": "..." }}
                Prompt: {prompt}
                """
            )

        def validate_date(natural_date):
            cal = parsedatetime.Calendar()
            date_struct, status = cal.parse(natural_date.strip())
            if status <= 0 or datetime(*date_struct[:3]).weekday() >= 5:
                return {"status": "INVALID"}
            return {
                "status": "VALID",
                "parsedDate": datetime(*date_struct[:3]).strftime("%Y-%m-%d"),
            }

        def validate_participants(participants):
            try:
                test_users = json.load(open(TEST_USER_FILE))["test_users"]
                matched = [
                    email
                    for p in participants
                    for name, email in test_users.items()
                    if p.lower() in name.lower()
                ]
                if len(matched) != len(participants):
                    return {"status": "INVALID", "missing": participants}
                return {"status": "VALID", "participant_emails": matched}
            except Exception as e:
                return {"status": "INVALID", "error": str(e)}

        def extract_duration_half(prompt):
            data = llm_json(
                f"""
                Extract:
                1. 'duration_minutes' (int)
                2. 'preferred_half' (e.g., morning, afternoon, full)
                Return: {{ "duration_minutes": ..., "preferred_half": "..." }}
                Prompt: {prompt}
                """
            )
            return {
                "duration_minutes": int(data.get("duration_minutes", 60)),
                "preferred_half": data.get("preferred_half", "full").lower(),
            }

        def extract_details(prompt):
            data = llm_json(
                f"""
                Extract:
                1. 'intent' – "schedule", "reschedule", or "cancel" (default: "schedule")
                2. 'title' – concise meeting title
                Return: {{ "intent": "...", "title": "..." }}
                Prompt: {prompt}
                """
            )
            return {
                "intent": data.get("intent", "schedule").lower(),
                "title": data.get("title", "Schedule Meeting").strip(),
            }

        def generate_slots(preferred_half, duration):
            part_map = {
                "full": (9, 18),
                "first": (9, 13),
                "second": (14, 18),
                "morning": (9, 12),
                "afternoon": (12, 16),
                "evening": (16, 18),
            }
            if preferred_half not in part_map:
                return []
            start_hr, end_hr = part_map[preferred_half]
            current = datetime.strptime(f"{start_hr}:00", "%H:%M")
            end = datetime.strptime(f"{end_hr}:00", "%H:%M")
            return [
                f"{current.strftime('%H:%M')}–{(current + timedelta(minutes=duration)).strftime('%H:%M')}"
                for _ in range((end.hour - start_hr) * 60 // duration)
                if not (current := current + timedelta(minutes=duration)) > end
            ]

        try:
            # Step 1: Prompt
            if validate_prompt(prompt).get("status") != "VALID":
                return json.dumps({"status": "INVALID", "reason": "Prompt not valid"})

            # Step 2: Extract other usefull details
            details = extract_details(prompt)
            intent = details["intent"]

            # Step 3: Participants
            participants_result = validate_participants(participants)
            if participants_result.get("status") != "VALID":
                return json.dumps(
                    {"status": "INVALID", "reason": "Participants invalid"}
                )

            if (
                len(participants_result["participant_emails"]) <= 1
                and intent != "cancel"
            ):
                return json.dumps(
                    {"status": "INVALID", "reason": "Minimum 2 participants required"}
                )
            if (
                len(participants_result["participant_emails"]) != 1
                and intent == "cancel"
            ):
                return json.dumps(
                    {
                        "status": "INVALID",
                        "reason": "Only 1 participant allowed for cancel",
                    }
                )

            # Step 4: Date
            date_result = validate_date(natural_date)
            if date_result.get("status") != "VALID":
                return json.dumps({"status": "INVALID", "reason": "Date invalid"})

            if intent == "cancel":
                return json.dumps(
                    {
                        "status": "VALID",
                        "meeting_info": {
                            "intent": intent,
                            "date": date_result["parsedDate"],
                            "participants": participants,
                            "participant_emails": participants_result[
                                "participant_emails"
                            ],
                        },
                    }
                )

            # Step 5: Duration and Time Window
            parsed = extract_duration_half(prompt)
            slots = generate_slots(parsed["preferred_half"], parsed["duration_minutes"])
            if not slots:
                return json.dumps({"status": "INVALID", "reason": "No valid timeslots"})

            # Final JSON
            return json.dumps(
                {
                    "status": "VALID",
                    "meeting_info": {
                        "intent": intent,
                        "title": details["title"],
                        "date": date_result["parsedDate"],
                        "participants": participants,
                        "participant_emails": participants_result["participant_emails"],
                        "duration_minutes": parsed["duration_minutes"],
                        "preferred_half": parsed["preferred_half"],
                        "timeslots": slots,
                    },
                }
            )
        except:
            return json.dumps({"status": "INVALID", "reason": "Internal issues"})
        finally:
            print(f"[ValidatorTool] Took {round(time.time() - start, 2)}s")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
