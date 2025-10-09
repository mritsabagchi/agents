import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title = "AI Interview Chatbot"
    layout= "wide",
    initial_sidebar_state="expanded"
)

#----------- Constants -------------
BACKEND_URL = "https://127.0.0.1:8000" # URL of your running FastAPI backened

#----- Session State Initialization ----------
# This is crucial for maintaining the conversation state acrosss user interactions.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.interview_started = False
    st.session_state.analysis = None #Not required
    st.session_state.job_reqs = " " #Needs to be taken from the main job requirement

#-------- Helper Functions ----------
def clean_json_response(response_text: str):
    """" Helper to clean and parse JSON that might be in a markdown block. """
    try:
        # Find the start and end of JSON block
        json_start = response_text.find('```json') + len('```json\n')
        json_end = response_text.rfind('```')

        if json_start > -1 and json_end > -1:
            json_part = response_text[json_start:json_end].strip()
            return json.loads(json_part)
        else:
            # If no markdown block, try parsing the whole string
            return json.loads(json_part)    
