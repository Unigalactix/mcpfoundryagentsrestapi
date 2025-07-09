import asyncio
from datetime import datetime
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import os, json
from typing import Any, Callable, Set, Dict, List, Optional
from azure.ai.agents.models import CodeInterpreterTool, FunctionTool, ToolSet
from openai import AzureOpenAI

from azure.ai.agents.models import ConnectedAgentTool, MessageRole
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType, MessageRole, ListSortOrder, ToolDefinition, FilePurpose, FileSearchTool
from azure.ai.agents.models import MessageTextContent, ListSortOrder

from dotenv import load_dotenv

load_dotenv()

endpoint = os.environ["PROJECT_ENDPOINT"] # Sample : https://<account_name>.services.ai.azure.com/api/projects/<project_name>
model_endpoint = os.environ["MODEL_ENDPOINT"] # Sample : https://<account_name>.services.ai.azure.com
model_api_key= os.environ["MODEL_API_KEY"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"] # Sample : gpt-4o-mini
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true" 

# Create the project client (Foundry project and credentials)
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

client = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_KEY"),  
  api_version="2024-10-21",
)

# Define some custom python function
def fetch_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.

    :param location (str): The location to fetch weather for.
    :return: Weather information as a JSON string.
    :rtype: str
    """
    # In a real-world scenario, you'd integrate with a weather API.
    # Here, we'll mock the response.
    mock_weather_data = {"Seattle": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}
    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    weather_json = json.dumps({"weather": weather})
    return weather_json

def ai_default_agent(query: str) -> str:
    returntxt = ""

    # Define user functions
    user_functions = {fetch_weather}

    # Initialize the FunctionTool with user-defined functions
    functions = FunctionTool(functions=user_functions)

    # Create an agent with the Bing Grounding tool
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],  # Model deployment name
        name="functest-agent",  # Name of the agent
        instructions="You are a helpful agent, use the tools to answer.",  # Instructions for the agent
        # tools=code_interpreter.definitions,  # Attach the tool
        tools=functions.definitions,
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")
    
    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",  # Role of the message sender
        content=query # "What is the weather in Seattle today?",  # Message content
    )
    print(f"Created message, ID: {message['id']}")
    
    # Create and process an agent run
    run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")
    
    # Check if the run failed
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    
    # Fetch and log all messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message.role}, Content: {message.content}")
        returntxt += f"Source: {message.content[0].text.value}\n"
    
    # Delete the agent when done
    project_client.agents.delete_agent(agent.id)
    project_client.agents.threads.delete(thread.id)
    print("Deleted agent and thread")

    return returntxt