import os
from dotenv import loadenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Tasks, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

#Import API Key
load_dotenv()

# 1. Initialize Language Model(LLM)

llm=ChatGoogleGenerativeAI(
    model="gemini-pro"
    verbose=True
    temparature=0.7
    google_api_key=os.environ.get("GOOGLE_API_KEY")
    )

# 2. ----Pydantic Models for API Request Validation----
# Defines the structure of the data and the API expects for each endpoint.

class InterviewRequest(BaseModel):
    job_file_name: str
    chat_history: str = " "

class AnalysisRequest(BaseModel):
    job_file_name: str
    interview_transcript: str

# 3. YAML Loading Utility
def load_yaml_config(filepath:str):
    """ Loads a YAML file and returns its content. """
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)
    



# 3. Setup FastAPI web server
app = FastAPI(
    title= "CrewAI Chatbot Backend"
    description= "A server that uses CrewAI to power an interview chatbot."
)

# Adds CORS middleware to allow requests from any origin
# This is crucial for connecting a web-based frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allows all origins.
    # For production, you would restrict this to your Streamlit app's actual domain.
    # allow_origins=["http://localhost:8501", "https://your-deployed-app.com"],
    allow_credentials=["*"],
    allow_medhod=["*"],
    allow_headers=["*"]  # Allows all headers
)

#---- 4. AI Model and Agent Initialization ----
try:

    agents_config = load_yaml_config('agents.yaml')
    tasks_config = load_yaml_config('tasks.yaml')
    
except FileNotFoundError:
    raise RuntimeError("agents.yaml and tasks,yaml not found. Please ensure they are in the same directory")


#-------API Endpoints-------
@app.post("/start_interview")
async def start_interview(request: InterviewRequest):