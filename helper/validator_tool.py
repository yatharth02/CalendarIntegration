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

    def _run(self, title: str, natural_date: str, participants: List[str], prompt: str):
        print("[ValidatorTool] TOOL STARTED")
        start = time.time()

        def validate_strict_outlook_prompt(prompt):
            system_instruction = """
            You are a validator that checks if a given prompt is strictly related to Microsoft Outlook meeting scheduling.
            If the prompt contains references to scheduling, setting up meetings, checking calendar availability, or inviting participants — it is VALID.
            ONLY return JSON like: { "status": "VALID" } or { "status": "INVALID", "reason": "..." }
            """
            full_prompt = f"{system_instruction}\n\nPrompt: {prompt}"
            try:
                response = llm.invoke(full_prompt)
                return response.content
            except Exception as e:
                return json.dumps({"status": "INVALID", "reason": str(e)})

        def validate_meeting_date(natural_date):
            cal = parsedatetime.Calendar()
            date_struct, status = cal.parse(natural_date.strip())
            if status <= 0:
                return json.dumps({"status": "INVALID"})
            dt = datetime(*date_struct[:3])
            if dt.weekday() >= 5:
                return json.dumps({"status": "INVALID"})
            return json.dumps(
                {"status": "VALID", "parsedDate": dt.strftime("%Y-%m-%d")}
            )

        def validate_participants_list(participants):
            try:
                test_users = json.load(open(TEST_USER_FILE))["test_users"]
                matched = [
                    email
                    for p in participants
                    for name, email in test_users.items()
                    if p.lower() in name.lower()
                ]
                if len(matched) != len(participants):
                    return json.dumps({"status": "INVALID", "missing": participants})
                return json.dumps({"status": "VALID", "participant_emails": matched})
            except Exception as e:
                return json.dumps({"status": "INVALID", "error": str(e)})

        def extract_duration_and_half(prompt):
            try:
                system_instruction = """
                Extract:
                1. 'duration_minutes' – int (e.g., 30, 60)
                2. preferred_half (e.g., morning, afternoon, full, first, second etc.)
                If not present, default to 60 minutes and 'full'.
                ONLY respond in this JSON format:
                {\n  \"duration_minutes\": <int>,\n  \"preferred_half\": \"<part>\"\n}
                """
                response = llm.invoke(f"Prompt: {prompt}\n{system_instruction}")
                parsed = json.loads(response.content)
                return {
                    "duration_minutes": int(parsed.get("duration_minutes", 60)),
                    "preferred_half": parsed.get("preferred_half", "full").lower(),
                }
            except:
                return {"duration_minutes": 60, "preferred_half": "full"}

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
            fmt = "%H:%M"
            current = datetime.strptime(f"{start_hr}:00", fmt)
            end = datetime.strptime(f"{end_hr}:00", fmt)
            slots = []
            while current + timedelta(minutes=duration) <= end:
                slot_end = current + timedelta(minutes=duration)
                slots.append(f"{current.strftime(fmt)}–{slot_end.strftime(fmt)}")
                current = slot_end
            return slots

        # Init LLM
        global llm
        llm = ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )

        try:
            # Step 1: Prompt
            prompt_result = json.loads(validate_strict_outlook_prompt(prompt))
            if prompt_result.get("status") != "VALID":
                return json.dumps({"status": "INVALID", "reason": "Prompt not valid"})

            # Step 2: Participants
            participants_result = json.loads(validate_participants_list(participants))
            if participants_result.get("status") != "VALID":
                return json.dumps(
                    {"status": "INVALID", "reason": "Participants invalid"}
                )

            # Step 3: Date
            date_result = json.loads(validate_meeting_date(natural_date))
            if date_result.get("status") != "VALID":
                return json.dumps({"status": "INVALID", "reason": "Date invalid"})

            # Step 4: Duration and Time Window
            parsed = extract_duration_and_half(prompt)
            slots = generate_slots(parsed["preferred_half"], parsed["duration_minutes"])
            if not slots:
                return json.dumps({"status": "INVALID", "reason": "No valid timeslots"})

            # Final JSON
            return json.dumps(
                {
                    "status": "VALID",
                    "meeting_info": {
                        "title": title,
                        "date": date_result["parsedDate"],
                        "participants": participants,
                        "participant_emails": participants_result["participant_emails"],
                        "duration_minutes": parsed["duration_minutes"],
                        "preferred_half": parsed["preferred_half"],
                        "timeslots": slots,
                    },
                }
            )

        finally:
            print(f"[ValidatorTool] Took {round(time.time() - start, 2)}s")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
