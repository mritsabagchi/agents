from pydantic import BaseModel
import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Interview Chatbot", layout="wide", initial_sidebar_state="expanded"
)

# --- Constants ---
BACKEND_URL = "http://127.0.0.1:8000"  # URL of your running FastAPI backend

# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.interview_started = False


# --- Helper Function ---
def parse_response(response: requests.Response) -> dict:
    """Parses the JSON response from the backend."""
    try:
        return response.json()
    except json.JSONDecodeError:
        st.error(
            "Received an invalid response from the backend. Please check the server logs."
        )
        st.info(f"Raw Response: {response.text}")
        return {}


# --- Sidebar UI ---
with st.sidebar:
    st.header("📋 Interview Controls")

    # The button to start the interview is now the main control.
    if st.button("🚀 Start Interview", use_container_width=True):
        # Reset state for a new interview
        st.session_state.interview_started = True
        st.session_state.chat_history = []
        with st.spinner("Preparing first question..."):

            try:
                # Use request.post to CALL the backend endpoint
                response = requests.post(f"{BACKEND_URL}/start_interview")
                response.raise_for_status()

                response_data = parse_response(response)
                first_question = response_data.get("question", "I'am ready to start")
                interview_id = response_data.get("interview_id")

                st.session_state.interview_id = interview_id
                st.session_state.chat_history.append({"role": "assistant", "content": first_question})
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to BackendAPI. Error: {e}")

# --- Main Chat Interface ---
st.title("AI Interview Chatbot 🤖")

if not st.session_state.interview_started:
    st.info("Click 'Start New Interview' in the sidebar to begin.")

if st.session_state.interview_started:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_answer := st.chat_input("Your answer..."):
        st.session_state.chat_history.append({"role": "user", "content": user_answer})
        
        with st.chat_message("user"):
            st.markdown(user_answer)
        
        payload = {
            "interview_id": st.session_state.interview_id,
            "latest_answer": user_answer
        }
        
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{BACKEND_URL}/next_question", json=payload)
                response.raise_for_status()
                
                response_data = parse_response(response)
                next_question = response_data.get("question", "I seem to have a technical issue.")
                
                st.session_state.chat_history.append({"role": "assistant", "content": next_question})
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to get next question. Error: {e}")