from fastapi import FastAPI, Request
from pydantic import BaseModel
import sys
import os
import json

# Add your crm_agent.py folder to path
sys.path.append("C:/Users/raafe/OneDrive/Documents/ai_workflow_automation/crm_automation_agent")

from crm_agent import create_workflow

app = FastAPI()

workflow = create_workflow()

class QueryRequest(BaseModel):
    query: str

@app.post("/run")
async def run_workflow(request: QueryRequest):
    initial_state = {"query": request.query}
    try:
        result = workflow.invoke(initial_state)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/")
async def root():
    return {"message": "CRM Automation Agent is running."}
