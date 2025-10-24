from fastapi import FastAPI, APIRouter # 1. Import FastAPI
from pydantic import BaseModel
from crewai import Agent, Task, Crew
import yaml
import json
import uuid
from typing import List, Dict
import os

from .main import llm, agents_config, tasks_config

# --- Create the main FastAPI app instance ---
app = FastAPI() # 2. Create the 'app' object uvicorn is looking for

# --- Define the Path to Your Job File ---

# Get the absolute path to the directory containing this script (backendapi.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_REQUIREMENTS_FILE_PATH = os.path.join(
    SCRIPT_DIR, "document", "job_description", "Senior_DE_requirement.md"
)

# Also, update the variable name to match your code
job_desc_path = JOB_REQUIREMENTS_FILE_PATH


# --- In-Memory Storage for Interview Sessions ---
interview_sessions: Dict[str, Dict] = {}


# --- Helper Function to read YAML ---
def load_job_requirements(file_path: str) -> str:
    """Reads a text or markdown file and returns its content as a string."""
    try:
        with open(file_path,"r") as file:
            return file.read()
    except FileNotFoundError:
        return "Error: Job requirements file not found."
    except Exception as e:
        return f"Error description : {e}"



# --- Pydantic Models ---
class NextQuestionRequest(BaseModel):
    interview_id: str
    latest_answer: str


class StartInterviewResponse(BaseModel):
    question: str
    interview_id: str


# --- Create an API Router ---
router = APIRouter()

# --- Create Agent Instance ---
interviewer_agent = Agent(**agents_config["interviewer_agent"], llm=llm)


# --- Define API Endpoints ---
@router.post("/start_interview", response_model=StartInterviewResponse)
async def start_interview():
    """
    Endpoint to start the interview.
    """
    job_requirements_str = load_job_requirements(job_desc_path)
    interview_id = str(uuid.uuid4())
    print("InterviewID : "+interview_id)
    topic_generation_task = Task(
        description=f"""Analyze the following job description and extract 5-7 key interview topics.
            Job Description:
            ---
            {job_requirements_str}
            ---
            
            Respond ONLY with a valid JSON object. Do not add "Thought:", "Final Answer:", or any other text.
            Your response must be a JSON object with a single key "topics", containing a list of strings.
            
            Example:
            {{
              "topics": ["Topic 1", "Topic 2", "Topic 3"]
            }}
        """,
        agent=interviewer_agent,
        expected_output="A JSON object with a single key 'topics' which contains a list of strings.",
        )
    topic_crew = Crew(
        agents=[interviewer_agent], tasks=[topic_generation_task], verbose=True
    )
    topic_result_str = topic_crew.kickoff()
    topics = json.loads(topic_result_str.raw).get("topics",[])

    task_info = tasks_config["interview_the_candidate_task"]
    start_task = Task(
        description=task_info["description"].format(
            job_requirements=job_requirements_str,
            candidates_data="N/A",
            chat_history=f"The interview is just beginning. Your plan is to cover these topics: {', '.join(topics)}. Start with the first one.",
        ),
        agent=interviewer_agent,
        expected_output=task_info["expected_output"],
    )

    question_crew = Crew(agents=[interviewer_agent], tasks=[start_task], verbose=True)
    question_result = question_crew.kickoff()
    first_question = question_result.raw

    initial_chat_history = f"assistant: {first_question}"
    interview_sessions[interview_id] = {
        "topics": topics,
        "chat_history": initial_chat_history,
    }

    return {"question": first_question, "interview_id": interview_id}


@router.post("/next_question")
async def next_question(request: NextQuestionRequest):
    """
    Endpoint to get the next question.
    """
    session = interview_sessions.get(request.interview_id)
    if not session:
        return {"question": "Error: Invalid session ID. Please start a new interview."}

    session["chat_history"] += f"\nuser: {request.latest_answer}"
    job_requirements_str = load_job_requirements(job_desc_path)
    task_info = tasks_config["interview_the_candidate_task"]

    next_question_task = Task(
        description=f"""
            You are an interviewer following a plan. The topics to cover are: {", ".join(session["topics"])}.The full job description is: '{job_requirements_str}'.The conversation so far is:---{session["chat_history"]}---Based on the plan and history, ask the next logical question. Do not repeat topics

            IMPORTANT: If the user's last message is a question like
            "what was the last question?" or "can you repeat that?",
            you MUST repeat your previous question.
            Otherwise, ask a new question.
        """,
        agent=interviewer_agent,
        expected_output=task_info["expected_output"],
    )
    crew = Crew(agents=[interviewer_agent], tasks=[next_question_task], verbose=True)
    question_resut = crew.kickoff()
    question = question_resut.raw

    session["chat_history"] += f"\nassistant: {question}"
    return {"question": question}


# --- Attach the router to the main app ---
app.include_router(router) # 3. Attach all routes from the router to the app