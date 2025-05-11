import streamlit as st
from crew import kickoff_meeting_prompt_validation, kickoff_meeting_creation
import json
import time
import ast

st.set_page_config(page_title="Calendar Integration", layout="centered")
st.title("Calendar Integration with CrewAI")

# Input prompt
test_prompt = st.text_area(
    "Enter your scheduling prompt",
    "Schedule a team meeting with Deoly and Part for tomorrow for 30 mins in morning",
)

# Session state initialization
if "validated_result" not in st.session_state:
    st.session_state.validated_result = None
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None
if "slots" not in st.session_state:
    st.session_state.slots = []
if "duration" not in st.session_state:
    st.session_state.duration = None
flag = False

# Step 1: Run validation and calendar check
if st.button("Run Meeting Scheduler"):
    with st.spinner("Running agents to process your request..."):
        start_time = time.time()
        try:
            result = kickoff_meeting_prompt_validation(test_prompt)
            st.session_state.duration = time.time() - start_time

            try:
                result_json = (
                    result if isinstance(result, dict) else ast.literal_eval(result)
                )
            except Exception as e:
                st.error("Failed to parse result. Please RETRY!!!")
                st.code(result)
                st.stop()

            status = result_json.get("status", "").upper()
            if status == "INVALID":
                st.error("Prompt is not related to Outlook meeting scheduling.")
            elif not result_json.get("meeting_info", {}).get("freetimeslots"):
                st.warning("No available time slots found.")
            elif result_json["meeting_info"]["intent"].lower() == "schedule":
                st.session_state.validated_result = result_json
                st.session_state.slots = result_json["meeting_info"]["freetimeslots"]
                st.session_state.selected_slot = st.session_state.slots[0]

        except Exception as e:
            st.error(f"Error: {e}")

# Show slot selection dropdown if available
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
    flag = True

# Step 2: Confirm and create meeting
if flag and st.button("Confirm and Create Meeting"):
    with st.spinner("Creating meeting..."):
        st.session_state.validated_result["meeting_info"][
            "confirmed_slot"
        ] = st.session_state.selected_slot
        try:
            final_result = kickoff_meeting_creation(st.session_state.validated_result)
            start_time = time.time()

            try:
                final_json = (
                    final_result
                    if isinstance(final_result, dict)
                    else ast.literal_eval(final_result)
                )
            except Exception as e:
                st.error("Failed to parse meeting creation result.")
                st.code(final_result)
                st.stop()

            total_duration = st.session_state.duration + (time.time() - start_time)
            st.subheader("Execution Duration")
            st.write(f"{total_duration:.2f} seconds")

            st.subheader("Meeting Creation Output")
            if final_json.get("status") == "SUCCESS":
                event_link = final_json["meeting_info"].get("event_link")
                if event_link:
                    st.markdown(
                        f"✅ **[Click here to open your meeting invite]({event_link})**"
                    )
            st.code(
                json.dumps(final_json, indent=2, ensure_ascii=False), language="json"
            )

        except Exception as e:
            st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("Built with CrewAI, LangChain, Google Calendar API, and Streamlit ✨")
