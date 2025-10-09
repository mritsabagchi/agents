import streamlit as st
import requests
import json

# URL of your running FastAPI backend
BACKEND_URL = "http://127.0.0.1:8000"

st.title("AI Interview Chatbot 🤖")

# Initialize chat history in session state if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.interview_started = False

# --- Sidebar for Job Description ---
with st.sidebar:
    st.header("Job Details")
    job_reqs = st.text_area("Paste the Job Requirements here:", height=200)
    
    if st.button("Start Interview") and job_reqs:
        # Call the /start_interview endpoint
        response = requests.post(f"{BACKEND_URL}/start_interview", json={"job_requirements": job_reqs})
        if response.status_code == 200:
            first_question = response.json().get("question")
            st.session_state.chat_history.append({"role": "assistant", "content": first_question})
            st.session_state.interview_started = True
        else:
            st.error("Failed to start the interview. Is the backend running?")
    
    if st.session_state.interview_started:
        if st.button("Finish & Analyze Interview"):
            # Create the full transcript string
            transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])
            
            # Call the /analyze_interview endpoint
            payload = {"job_requirements": job_reqs, "interview_transcript": transcript}
            with st.spinner("Analyzing performance..."):
                response = requests.post(f"{BACKEND_URL}/analyze_interview", json=payload)
                if response.status_code == 200:
                    analysis = response.json().get("analysis")
                    st.session_state.analysis = analysis # Store analysis
                else:
                    st.error("Failed to get analysis.")

# --- Main Chat Interface ---
if st.session_state.interview_started:
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if user_answer := st.chat_input("Your answer..."):
        # Add user answer to history and display it
        st.session_state.chat_history.append({"role": "user", "content": user_answer})
        with st.chat_message("user"):
            st.markdown(user_answer)

        # Get the next question from the backend
        transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])
        payload = {"job_requirements": job_reqs, "chat_history": transcript}
        
        with st.spinner("Thinking..."):
            response = requests.post(f"{BACKEND_URL}/next_question", json=payload)
            if response.status_code == 200:
                next_question = response.json().get("question")
                st.session_state.chat_history.append({"role": "assistant", "content": next_question})
                # Rerun the script to display the new question
                st.experimental_rerun()
            else:
                st.error("Failed to get the next question.")

# --- Display Final Analysis ---
if 'analysis' in st.session_state:
    st.header("Interview Analysis Report")
    report = st.session_state.analysis
    st.subheader("Overall Summary")
    st.write(report.get("summary", "N/A"))

    st.subheader("Key Strengths")
    for strength in report.get("strengths", []):
        st.markdown(f"- {strength}")

    st.subheader("Areas for Improvement")
    for weakness in report.get("weaknesses", []):
        st.markdown(f"- {weakness}")
    
    st.subheader("Final Score")
    st.progress(report.get("final_score", 0) / 100)
    st.markdown(f"**{report.get('final_score', 0)} / 100**")