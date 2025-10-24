import os
from pathlib import Path
from crewai import Crew, Process, Agent, Task
# This LLM import is for the new syntax, but you are using the string syntax
# from crewai import LLM 
from langchain_community.llms import Ollama
from crewai_tools import FileReadTool
from textwrap import dedent
from pydantic import BaseModel, Field
# from .documents import job_description_example

# --- Define your desired JSON output structure ---
class CandidateEvaluation(BaseModel):
    """A model to hold the candidate's evaluation score and justification."""
    candidate_name: str = Field(description="The full name of the candidate.")
    position_evaluated: str = Field(description="The job role for which the candidate was evaluated.")
    score: int = Field(description="The calculated score from 0-100.")
    justification: str = Field(description="A concise, evidence-based justification for the score.")

# Note: You might need to install PyYAML: pip install pyyaml
import yaml

# --- 1. Load Configurations and Initialize LLM ---

# Initialize the Ollama model (ensure Ollama is running)
# Note: You are passing the LLM as a string "ollama/llama3" to the Agent,
# so this 'ollama_llm' object isn't currently used.
# This is fine, but just for your awareness.
ollama_llm = Ollama(
    model="llama3",
    base_url="http://localhost:11434"
)

# SCRIPT_DIR is the 'local_test' folder
SCRIPT_DIR = Path(__file__).resolve().parent

# Go up one level (to src/interview_agent) and then into the 'config' folder
AGENTS_CONFIG_PATH = SCRIPT_DIR.parent / "config" / "agents.yaml"
TASKS_CONFIG_PATH = SCRIPT_DIR.parent / "config" / "tasks.yaml"

# Load agent and task configurations from YAML files
with open(AGENTS_CONFIG_PATH, 'r') as f:
    agents_config = yaml.safe_load(f)

with open(TASKS_CONFIG_PATH, 'r') as f:
    tasks_config = yaml.safe_load(f)

job_desc_path = SCRIPT_DIR.parent / "document" / "job_description" / "Senior_DE_requirement.md"
resume_path = SCRIPT_DIR.parent / "document" / "resumes" / "Alex_Carter.md"
transcript_path = SCRIPT_DIR.parent / "document" / "transcripts" / "interview_transcript.md"


# --- 2. Create Dummy Files for Testing ---

# Ensure directories exist
os.makedirs(job_desc_path.parent, exist_ok=True)
os.makedirs(resume_path.parent, exist_ok=True)
os.makedirs(transcript_path.parent, exist_ok=True)


# Create dummy files with sample content for the test run
if not os.path.exists(job_desc_path):
    with open(job_desc_path, "w") as f:
        f.write("Job Title: Senior Python Developer. Requirements: 5+ years of Python, Django, AWS. Strong problem-solving skills.")
if not os.path.exists(resume_path):
    with open(resume_path, "w") as f:
        f.write("Jane Doe - Experienced Python Developer with 6 years in Django and experience deploying on AWS. Led a team of 3 developers.")
if not os.path.exists(transcript_path):
    with open(transcript_path, "w") as f:
        f.write("Interviewer: Can you describe your experience with AWS? Jane: I have used S3, EC2, and Lambda for deploying and managing applications. Interviewer: How do you handle code reviews? Jane: I believe in constructive feedback and use a pull-request-based workflow.")


# --- 3. Instantiate Agents and Tasks ---

# Initialize the tool(s)
# This is a generic tool instance, used by the evaluator_task (which is commented out)
file_read_tool = FileReadTool()

# Create Agent instances from the configuration
recruiter_agent = Agent(**agents_config['recruiter_agent'], llm="ollama/llama3")
# interviewer_agent = Agent(**agents_config['interviewer_agent'], llm="ollama/llama3")
# evaluator_agent = Agent(**agents_config['evaluator_agent'], llm="ollama/llama3")

# Create Task instances from the configuration
match_and_score_candidate_task = Task(
    **tasks_config['match_and_score_candidate_task'],
    agent=recruiter_agent,
    tools=[
        # FIX: Give each tool a unique name, description, and pass the path as a string
        FileReadTool(
            name="Read Resume File",
            description="A tool to read the candidate's resume. The file path is already set.",
            file_path=str(resume_path)
        ),
        FileReadTool(
            name="Read Job Description File",
            description="A tool to read the job description. The file path is already set.",
            file_path=str(job_desc_path)
        ),
    ]
)

# interviewer_task = Task(
#     **tasks_config['interviewer_task'],
#     agent=interviewer_agent
# )

# evaluator_task = Task(
#     **tasks_config['evaluator_task'],
#     agent=evaluator_agent,
#     tools=[file_read_tool] # This uses the generic file read tool
# )


# --- 4. Create and Run the Crew ---

# Define the crew with a sequential process
recruitment_crew = Crew(
    # agents=[recruiter_agent, interviewer_agent, evaluator_agent],
    # tasks=[match_and_score_candidate_task, interviewer_task, evaluator_task],
    agents=[recruiter_agent],
    tasks=[match_and_score_candidate_task],
    process=Process.sequential,
    verbose = True # Use verbose=2 for detailed logs
)

# Define the inputs for the kickoff
# These inputs are used to fill in placeholders in your tasks.yaml
inputs = {
    "job_description_file": str(job_desc_path),
    "resume_file": str(resume_path),
    "job_role": "Senior Data Engineer",
    "job_requirements": "6+ years with Snowflake, dbt, Fivetran, and advanced SQL."
}

print("🚀 Starting the Recruitment Crew...")
result = recruitment_crew.kickoff(inputs=inputs)

print("\n\n########################")
print("## ✅ Final Evaluation")
print("########################\n")

# Check if the result is what you expect. 
# If you defined an 'output_pydantic' for your task, CrewAI will try to parse it.
if isinstance(result, BaseModel):
    print(result.model_dump_json(indent=2))
elif isinstance(result, dict):
    import json
    print(json.dumps(result, indent=2))
else:
    print("The task did not return the expected structured output.")
    print("Raw Output:", result)
