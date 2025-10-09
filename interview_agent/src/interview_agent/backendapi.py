from fastapi import APIRouter
from pydantic import BaseModel
from crewai import Agent, Task, Crew
from main import llm, agents_config, tasks_config, get_job_requirements_from_file

# --- 1. Pydantic Model for Interview Requests ---
class InterviewRequest(BaseModel):
    job_file_name: str
    chat_history: str = ""

# --- 2. Create an API Router ---
# This router will hold all our interview-related endpoints
router = APIRouter()

# --- 3. Create Agent Instance ---
# Only the interviewer agent is needed for the conversation
interviewer_agent = Agent(**agents_config['interviewer_agent'], llm=llm)


# --- 4. Define API Endpoints on the Router ---
@router.post("/start_interview")
async def start_interview(request: InterviewRequest):
    """Endpoint to start the interview."""
    job_requirements_str = get_job_requirements_from_file(request.job_file_name)
    task_info = tasks_config['interview_the_candidate_task']
    
    start_task = Task(
        description=task_info['description'].format(
            job_requirements=job_requirements_str,
            candidates_data="N/A", # CV data is not part of this workflow
            chat_history="The interview is just beginning."
        ),
        agent=interviewer_agent,
        expected_output=task_info['expected_output']
    )
    
    crew = Crew(agents=[interviewer_agent], tasks=[start_task], verbose=2)
    first_question = crew.kickoff()
    return {"question": first_question}


@router.post("/next_question")
async def next_question(request: InterviewRequest):
    """Endpoint to get the next question based on the ongoing conversation."""
    job_requirements_str = get_job_requirements_from_file(request.job_file_name)
    task_info = tasks_config['interview_the_candidate_task']
    
    next_question_task = Task(
        description=task_info['description'].format(
            job_requirements=job_requirements_str,
            candidates_data="N/A", # CV data is not part of this workflow
            chat_history=request.chat_history
        ),
        agent=interviewer_agent,
        expected_output=task_info['expected_output']
    )
    
    crew = Crew(agents=[interviewer_agent], tasks=[next_question_task], verbose=2)
    question = crew.kickoff()
    return {"question": question}

