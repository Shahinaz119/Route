
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

load_dotenv()

@tool
def get_candidate_status():
    """Return the candidate's current status."""
    return "CV received and ready for analysis"

llm = ChatOpenAI(
    model=os.getenv("AGENT_MODEL", "openrouter/free"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_retries=0,
)

response = llm.bind_tools([get_candidate_status]).invoke(
    "Use get_candidate_status to check the candidate status."
)

print("Content:", response.content)
print("Tool calls:", response.tool_calls)
