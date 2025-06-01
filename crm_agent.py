from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import json
import os
from dotenv import load_dotenv
import requests
import logging
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load API configuration from api_config.json
config_path = "api_config.json"
api_config = {}
if os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if content:
                api_config = json.loads(content)
            else:
                logger.warning("api_config.json is empty, falling back to environment variables")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in api_config.json: {e}, falling back to environment variables")
    except Exception as e:
        logger.error(f"Error reading api_config.json: {e}, falling back to environment variables")
else:
    logger.info("api_config.json not found, using environment variables")

# Fallback to environment variables
if not api_config:
    api_config = {
        "HUGGINGFACE_API_KEY": os.getenv("HUGGINGFACE_API_KEY"),
        "HUBSPOT_CLIENT_ID": os.getenv("HUBSPOT_CLIENT_ID"),
        "HUBSPOT_CLIENT_SECRET": os.getenv("HUBSPOT_CLIENT_SECRET"),
        "HUBSPOT_REFRESH_TOKEN": os.getenv("HUBSPOT_REFRESH_TOKEN"),
        "HUBSPOT_API_KEY": os.getenv("HUBSPOT_API_KEY"),
        "MAILERSEND_API_KEY": os.getenv("MAILERSEND_API_KEY"),
        "MAILERSEND_SENDER_EMAIL": os.getenv("MAILERSEND_SENDER_EMAIL"),
        "MAILERSEND_RECIPIENT_EMAIL": os.getenv("MAILERSEND_RECIPIENT_EMAIL"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY")
    }

# State definition for the graph
class AgentState(TypedDict):
    query: str
    operation: Optional[str]
    payload: Optional[dict]
    result: Optional[dict]
    email_status: Optional[str]

# LLM-based Orchestrator Agent
class GlobalOrchestrator:
    def __init__(self):
        groq_api_key = api_config.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is required for LLM")

        # Initialize Groq LLM (Llama 4 Scout 17B Instruct)
        self.chat_model = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            api_key=groq_api_key,
            temperature=0.7,
            max_tokens=500,
            top_p=0.95
        )

        # Define prompt template for query parsing
        prompt_template = """
        You are a CRM assistant that processes user queries to perform operations in HubSpot (create contact, update contact, create deal).
        Given a user query, identify the operation and extract relevant details to create a JSON payload for the HubSpot API.
        Supported operations:
        - create_contact: Requires email, firstname, lastname (optional).
        - update_contact: Requires contact_id, fields to update (e.g., firstname, lastname, email).
        - create_deal: Requires dealname, amount (optional).

        Return a JSON object with:
        - "operation": The identified operation (e.g., "create_contact").
        - "payload": The HubSpot API payload (e.g., {{"properties": {{"email": "john.doe@example.com", "firstname": "John", "lastname": "Doe"}}}}).

        If the query is unclear or unsupported, return {{"operation": null, "payload": {{}}}}.

        Query: {query}

        Examples:
        Query: "Create a contact for John Doe with email john.doe@example.com"
        Output: {{"operation": "create_contact", "payload": {{"properties": {{"email": "john.doe@example.com", "firstname": "John", "lastname": "Doe"}}}}}}

        Query: "Update contact ID 123 with firstname Jane"
        Output: {{"operation": "update_contact", "payload": {{"properties": {{"firstname": "Jane"}}, "contact_id": "123"}}}}

        Query: "Create a deal named Big Sale for $5000"
        Output: {{"operation": "create_deal", "payload": {{"properties": {{"dealname": "Big Sale", "amount": "5000"}}}}}}
        """
        self.prompt = ChatPromptTemplate.from_template(prompt_template)
        self.parser = JsonOutputParser()
        self.chain = self.prompt | self.chat_model | self.parser

    def process_query(self, state: AgentState):
        try:
            query = state["query"]
            result = self.chain.invoke({"query": query})
            state["operation"] = result.get("operation")
            state["payload"] = result.get("payload")
            if not state["operation"]:
                state["result"] = {"error": "Unsupported or unclear query"}
        except Exception as e:
            logger.error(f"LLM query processing failed: {str(e)}")
            state["operation"] = None
            state["result"] = {"error": f"Query processing failed: {str(e)}"}
        return state

# HubSpot Agent
class HubSpotAgent:
    def __init__(self):
        self.client_id = api_config.get("HUBSPOT_CLIENT_ID") or os.getenv("HUBSPOT_CLIENT_ID")
        self.client_secret = api_config.get("HUBSPOT_CLIENT_SECRET") or os.getenv("HUBSPOT_CLIENT_SECRET")
        self.refresh_token = api_config.get("HUBSPOT_REFRESH_TOKEN") or os.getenv("HUBSPOT_REFRESH_TOKEN")
        self.api_key = api_config.get("HUBSPOT_API_KEY") or os.getenv("HUBSPOT_API_KEY")
        self.base_url = "https://api.hubapi.com"

        if all([self.client_id, self.client_secret, self.refresh_token]):
            self.auth_type = "oauth"
            try:
                self.access_token = self.get_access_token()
            except Exception as e:
                logger.error(f"Failed to get OAuth access token: {str(e)}")
                self.auth_type = "api_key" if self.api_key else None
        elif self.api_key:
            self.auth_type = "api_key"
        else:
            raise ValueError("Either HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, and HUBSPOT_REFRESH_TOKEN or HUBSPOT_API_KEY are required")

    def get_access_token(self):
        if self.auth_type != "oauth":
            return None
        url = "https://api.hubapi.com/oauth/v1/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            logger.error(f"OAuth token request failed: {response.status_code} {response.text}")
        response.raise_for_status()
        return response.json().get("access_token")

    def get_headers(self):
        if self.auth_type == "oauth" and hasattr(self, "access_token"):
            return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def execute_operation(self, state: AgentState):
        operation = state.get("operation")
        payload = state.get("payload", {})
        if not operation or not payload:
            state["result"] = {"error": "Invalid operation or payload"}
            return state

        try:
            if operation == "create_contact":
                response = self.create_contact(payload)
            elif operation == "update_contact":
                response = self.update_contact(payload)
            elif operation == "create_deal":
                response = self.create_deal(payload)
            else:
                response = {"error": "Invalid operation"}
            state["result"] = response
        except Exception as e:
            state["result"] = {"error": str(e)}
        return state

    def create_contact(self, payload):
        url = f"{self.base_url}/crm/v3/objects/contacts"
        headers = self.get_headers()
        email = payload.get("properties", {}).get("email")
        if not email:
            return {"error": "Email is required for create_contact"}

        # Check if contact exists
        search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
        search_data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }],
            "properties": ["email"]
        }
        search_response = requests.post(search_url, headers=headers, json=search_data)
        search_response.raise_for_status()
        search_results = search_response.json()
        if search_results.get("total", 0) > 0:
            return {"error": f"Contact with email {email} already exists", "existing_id": search_results["results"][0]["id"]}

        # Create new contact
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def update_contact(self, payload):
        contact_id = payload.get("contact_id")
        if not contact_id:
            return {"error": "contact_id is required for update_contact"}
        url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
        headers = self.get_headers()
        update_payload = {"properties": payload.get("properties", {})}
        response = requests.patch(url, headers=headers, json=update_payload)
        response.raise_for_status()
        return response.json()

    def create_deal(self, payload):
        url = f"{self.base_url}/crm/v3/objects/deals"
        headers = self.get_headers()
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

# Email Agent with MailerSend
class EmailAgent:
    def __init__(self):
        self.email_api_key = api_config.get("MAILERSEND_API_KEY") or os.getenv("MAILERSEND_API_KEY")
        self.sender_email = api_config.get("MAILERSEND_SENDER_EMAIL") or os.getenv("MAILERSEND_SENDER_EMAIL")
        self.recipient_email = api_config.get("MAILERSEND_RECIPIENT_EMAIL") or os.getenv("MAILERSEND_RECIPIENT_EMAIL")
        if not self.email_api_key:
            raise ValueError("MAILERSEND_API_KEY is required")
        if not self.sender_email:
            logger.warning("MAILERSEND_SENDER_EMAIL is missing, email notifications will be skipped")
            self.sender_email = None
        if not self.recipient_email:
            logger.warning("MAILERSEND_RECIPIENT_EMAIL is missing, email notifications will be skipped")
            self.recipient_email = None
        self.base_url = "https://api.mailersend.com/v1"

    def send_notification(self, state: AgentState):
        if not (self.sender_email and self.recipient_email):
            state["email_status"] = "skipped: MAILERSEND_SENDER_EMAIL or MAILERSEND_RECIPIENT_EMAIL is missing"
            return state
        try:
            operation = state["operation"]
            result = state["result"]
            url = f"{self.base_url}/email"
            headers = {
                "Authorization": f"Bearer {self.email_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "from": {"email": self.sender_email, "name": "CRM Agent"},
                "to": [{"email": self.recipient_email}],
                "subject": f"CRM Operation: {operation}",
                "html": f"<p>Operation {operation} completed with result: {json.dumps(result)}</p>"
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code not in (200, 202):
                logger.error(f"MailerSend request failed: {response.status_code} {response.text}")
            response.raise_for_status()
            state["email_status"] = "sent"
            logger.info(f"MailerSend request succeeded: {response.status_code} {response.text}")
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

# # Main execution
if __name__ == "__main__":
    workflow = create_workflow()
    initial_state = {"query": "Create a contact for John Doe with email john.doe@example.com"}
    result = workflow.invoke(initial_state)
    print(json.dumps(result, indent=2))

