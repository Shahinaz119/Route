
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("AGENT_MODEL", "openrouter/free")

print("Model:", model_name)
print("API key loaded:", bool(api_key))

llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_retries=0,
)

response = llm.invoke("Reply with OK only.")
print("Response:", response.content)
