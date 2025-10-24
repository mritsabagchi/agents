import os
from dotenv import load_dotenv
import yaml
from crewai import LLM,Agent, Task
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI

# --- Load Environment Variables ---
# This will automatically search for and load the .env file in your project's
# root directory. This is the standard and most reliable way to use the library.
# load_dotenv()

# --- Language Model Configuration ---
# Initialize the Google Generative AI model.
# This will be the brain of your agents.
# It now safely accesses the GOOGLE_API_KEY loaded from the .env file.
# api_key = os.getenv("GOOGLE_API_KEY")
# if not api_key:
#     raise ValueError(
#         "GOOGLE_API_KEY not found. Make sure it's set correctly in your .env file."
    # )

# For LLM endpoint connection
# llm = ChatGoogleGenerativeAI(
#     model="gemini-pro", verbose=True, temperature=0.7, google_api_key=api_key
# )

# For internal testing 
llm = LLM(
    model="ollama/llama3",
    base_url="http://localhost:11434"
)


app = FastAPI()  
# --- Function to Load YAML Configuration ---
def load_yaml_config(filepath):
    """Loads a YAML file and returns its content."""
    with open(filepath, "r") as file:
        return yaml.safe_load(file)


# --- Load Agent and Task Definitions ---
# These files define the roles, goals, and instructions for your agents and tasks.
try:
    # Construct paths relative to the current file
    current_dir = os.path.dirname(__file__)
    agents_config_path = os.path.join(current_dir, "config", "agents.yaml")
    tasks_config_path = os.path.join(current_dir, "config", "tasks.yaml")

    agents_config = load_yaml_config(agents_config_path)
    tasks_config = load_yaml_config(tasks_config_path)
except FileNotFoundError as e:
    print(f"Error: Configuration file not found - {e}")
    agents_config = {}
    tasks_config = {}
except Exception as e:
    print(f"An error occurred while loading configuration files: {e}")
    agents_config = {}
    tasks_config = {}


# --- Function to Create Agents from Config ---
def create_agents(config, llm_model):
    """Creates a dictionary of CrewAI Agent objects from a configuration dictionary."""
    agents = {}
    if "agents" in config:
        for agent_info in config["agents"]:
            agents[agent_info["role"]] = Agent(
                role=agent_info["role"],
                goal=agent_info["goal"],
                backstory=agent_info["backstory"],
                verbose=True,
                allow_delegation=False,
                llm=llm_model,
            )
    return agents


# --- Function to Create Tasks from Config ---
def create_tasks(config, agent_map, context_inputs):
    """Creates a list of CrewAI Task objects from a configuration dictionary."""
    tasks = []
    if "tasks" in config:
        for task_info in config["tasks"]:
            # Find the agent object from the map using the role name
            task_agent = agent_map.get(task_info["agent"])
            if task_agent:
                # Format the description with context inputs
                description = task_info["description"].format(**context_inputs)

                tasks.append(
                    Task(
                        description=description,
                        expected_output=task_info["expected_output"],
                        agent=task_agent,
                    )
                )
    return tasks
