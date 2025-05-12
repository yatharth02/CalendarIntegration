import streamlit as st
from crew import kickoff_meeting_prompt_validation, kickoff_meeting_creation
import json, time, ast

# ----------------- Utility Functions ----------------- #


def schedule_meeting():
    with st.spinner("Creating meeting..."):
        st.session_state.validated_result["meeting_info"][
            "confirmed_slot"
        ] = st.session_state.selected_slot
        try:
            result = kickoff_meeting_creation(st.session_state.validated_result)
            final_json = (
                result if isinstance(result, dict) else ast.literal_eval(result)
            )
            duration = st.session_state.duration + (
                time.time() - st.session_state.start_time
            )

            st.subheader("Execution Duration")
            st.write(f"{duration:.2f} seconds")

            st.subheader("Meeting Creation Output")
            if final_json.get("status") == "SUCCESS":
                link = final_json["meeting_info"].get("event_link")
                if link:
                    st.markdown(
                        f"✅ **[Click here to open your meeting invite]({link})**"
                    )
            st.code(json.dumps(final_json, indent=2), language="json")

        except Exception as e:
            st.error(f"Error: {e}")


def cancel_meeting():
    with st.spinner("Canceling meetings..."):
        selected_ids = [
            st.session_state.cancel_events[i]["event_id"]
            for i in st.session_state.selected_indices
        ]
        st.session_state.validated_result["meeting_info"]["cancel_ids"] = selected_ids
        try:
            result = kickoff_meeting_creation(st.session_state.validated_result)
            final_json = (
                result if isinstance(result, dict) else ast.literal_eval(result)
            )
            duration = st.session_state.duration + (
                time.time() - st.session_state.start_time
            )

            st.subheader("Execution Duration")
            st.write(f"{duration:.2f} seconds")

            st.subheader("Meeting Cancellation Output")
            st.code(json.dumps(final_json, indent=2), language="json")

        except Exception as e:
            st.error(f"Error: {e}")


def validator_event_check():
    with st.spinner("Running agents to process your request..."):
        st.session_state.start_time = time.time()
        try:
            result = kickoff_meeting_prompt_validation(st.session_state.test_prompt)
            st.session_state.duration = time.time() - st.session_state.start_time

            result_json = (
                result if isinstance(result, dict) else ast.literal_eval(result)
            )
            status = result_json.get("status", "").upper()
            intent = result_json.get("meeting_info", {}).get("intent", "").lower()

            if status == "INVALID":
                st.error("Prompt is not related to Outlook meeting scheduling.")
                return

            if intent == "cancel":
                events = result_json["meeting_info"].get("calendar_events", [])
                if not events:
                    st.warning("No events found to cancel.")
                    return
                st.session_state.cancel_events = [
                    {
                        "email": e["email"],
                        "event_id": e["event_id"],
                        "event_summary": e.get("event_summary", "(No Title)"),
                        "start_time": e["start_time"],
                        "end_time": e["end_time"],
                    }
                    for e in events
                ]
            elif intent == "schedule":
                slots = result_json["meeting_info"].get("freetimeslots", [])
                if not slots:
                    st.warning("No available time slots found.")
                    return
                st.session_state.slots = slots
                st.session_state.selected_slot = slots[0]

            st.session_state.validated_result = result_json

        except Exception as e:
            st.error(f"Error: {e}")


# ----------------- Streamlit UI ----------------- #

st.set_page_config(page_title="Calendar Integration", layout="centered")
st.title("Calendar Integration with CrewAI")

# Session state initialization
for key, default in {
    "validated_result": None,
    "selected_slot": None,
    "slots": [],
    "duration": None,
    "cancel_events": [],
    "selected_indices": [],
    "test_prompt": "Schedule a team meeting with Deoly and Part for tomorrow for 30 mins in morning",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Input Prompt
st.session_state.test_prompt = st.text_area(
    "Enter your scheduling prompt", st.session_state.test_prompt
)

# Step 1: Validation
if st.button("Run Meeting Scheduler"):
    validator_event_check()

# Slot selection for scheduling
if st.session_state.slots:
    st.selectbox(
        "Select a timeslot to confirm meeting",
        st.session_state.slots,
        index=(
            st.session_state.slots.index(st.session_state.selected_slot)
            if st.session_state.selected_slot in st.session_state.slots
            else 0
        ),
        key="selected_slot",
    )
    if st.button("Confirm and Create Meeting"):
        schedule_meeting()

# Cancel flow: Event table and selection
if st.session_state.cancel_events:
    st.subheader("Select Events to Cancel")
    table_data = [
        {
            "Index": i,
            "Summary": e["event_summary"],
            "Start Time": e["start_time"],
            "End Time": e["end_time"],
            "Email": e["email"],
        }
        for i, e in enumerate(st.session_state.cancel_events)
    ]
    st.dataframe(table_data, use_container_width=True)

    st.session_state.selected_indices = st.multiselect(
        "Choose events to cancel", options=[e["Index"] for e in table_data]
    )
    if st.session_state.selected_indices and st.button("Cancel Selected Events"):
        cancel_meeting()

# Footer
st.markdown("---")
st.caption("Built with CrewAI, LangChain, Google Calendar API, and Streamlit ✨")
