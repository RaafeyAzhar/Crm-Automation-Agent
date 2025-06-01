from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_huggingface import HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
import json
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Load API configuration from api_config.json if .env is not used
config_path = "api_config.json"
api_config = {}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        api_config = json.load(f)
else:
    api_config = {
        "HUGGINGFACE_API_KEY": os.getenv("HUGGINGFACE_API_KEY"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "HUBSPOT_API_KEY": os.getenv("HUBSPOT_API_KEY"),
        "MAILERSEND_API_KEY": os.getenv("MAILERSEND_API_KEY")
    }

# State definition for the graph
class AgentState(TypedDict):
    query: str
    operation: str
    result: dict
    email_status: str

# Global Orchestrator Agent
class GlobalOrchestrator:
    def __init__(self):
        huggingface_key = api_config.get("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")
        openrouter_key = api_config.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

        if openrouter_key:
            # Use OpenRouter's LLaMA 4 Maverick (free tier)
            self.llm = ChatOpenAI(
                model="meta-llama/llama-4-maverick",
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
                temperature=0.7,
                max_tokens=500
            )
        elif huggingface_key:
            # Use Hugging Face's LLaMA 3 8B Instruct (free tier)
            self.llm = HuggingFaceEndpoint(
                repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
                huggingfacehub_api_token=huggingface_key,
                temperature=0.7,
                max_new_tokens=500,
                top_k=50,
                top_p=0.95
            )
        else:
            raise ValueError("No valid API key provided for LLM (HuggingFace or OpenRouter)")

    def process_query(self, state: AgentState):
        query = state["query"]
        # Simple query parsing logic (can be enhanced with LLM)
        if "create contact" in query.lower():
            state["operation"] = "create_contact"
        elif "update contact" in query.lower():
            state["operation"] = "update_contact"
        elif "create deal" in query.lower():
            state["operation"] = "create_deal"
        return state

# HubSpot Agent
class HubSpotAgent:
    def __init__(self):
        self.api_key = api_config.get("HUBSPOT_API_KEY") or os.getenv("HUBSPOT_API_KEY")
        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY is required")
        self.base_url = "https://api.hubapi.com"
    
    def execute_operation(self, state: AgentState):
        operation = state["operation"]
        try:
            if operation == "create_contact":
                response = self.create_contact(state["query"])
            elif operation == "update_contact":
                response = self.update_contact(state["query"])
            elif operation == "create_deal":
                response = self.create_deal(state["query"])
            else:
                response = {"error": "Invalid operation"}
            state["result"] = response
        except Exception as e:
            state["result"] = {"error": str(e)}
        return state
    
    def create_contact(self, query):
        # Simplified contact creation using HubSpot free tier API
        url = f"{self.base_url}/crm/v3/objects/contacts"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"properties": {"email": "example@email.com", "firstname": "Test", "lastname": "User"}}
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
    def update_contact(self, query):
        # Simplified contact update using HubSpot free tier API
        url = f"{self.base_url}/crm/v3/objects/contacts/1"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"properties": {"firstname": "Updated"}}
        response = requests.patch(url, headers=headers, json=data)
        return response.json()
    
    def create_deal(self, query):
        # Simplified deal creation using HubSpot free tier API
        url = f"{self.base_url}/crm/v3/objects/deals"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"properties": {"dealname": "Test Deal", "amount": "1000"}}
        response = requests.post(url, headers=headers, json=data)
        return response.json()

# Email Agent
class EmailAgent:
    def __init__(self):
        self.email_api_key = api_config.get("MAILERSEND_API_KEY") or os.getenv("MAILERSEND_API_KEY")
        if not self.email_api_key:
            raise ValueError("MAILERSEND_API_KEY is required")
        self.base_url = "https://api.mailersend.com/v1"
    
    def send_notification(self, state: AgentState):
        try:
            operation = state["operation"]
            result = state["result"]
            url = f"{self.base_url}/email"
            headers = {
                "Authorization": f"Bearer {self.email_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "from": {"email": "no-reply@example.com", "name": "CRM Agent"},
                "to": [{"email": "recipient@example.com"}],
                "subject": f"CRM Operation: {operation}",
                "html": f"<p>Operation {operation} completed with result: {json.dumps(result)}</p>"
            }
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            state["email_status"] = "sent"
        except Exception as e:
            state["email_status"] = f"failed: {str(e)}"
        return state

# Define the workflow
def create_workflow():
    workflow = StateGraph(AgentState)
    
    orchestrator = GlobalOrchestrator()
    hubspot_agent = HubSpotAgent()
    email_agent = EmailAgent()
    
    workflow.add_node("orchestrator", orchestrator.process_query)
    workflow.add_node("hubspot", hubspot_agent.execute_operation)
    workflow.add_node("email", email_agent.send_notification)
    
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "hubspot")
    workflow.add_edge("hubspot", "email")
    workflow.add_edge("email", END)
    
    return workflow.compile()

# Main execution
if __name__ == "__main__":
    workflow = create_workflow()
    initial_state = {"query": "create contact"}
    result = workflow.invoke(initial_state)
    print(result)
