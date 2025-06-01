# CRM Automation Agent

This project implements an AI-powered autonomous agent system for CRM automation with HubSpot integration and email notifications using free APIs.

## Setup Instructions

1. **Prerequisites**:
   - Python 3.8+
   - HubSpot account with API key (free tier available)
   - MailerSend account with API key (free tier with 3,000 emails/month)
   - Hugging Face account with API key (free tier for LLaMA 3 8B Instruct) or OpenRouter account with API key (free tier for LLaMA 4 Maverick)

2. **Installation**:
   `ash
   # Create and activate virtual environment
   python -m venv .venv
   .\.venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   `

3. **Configuration**:
   - Copy pi_config.template.json to pi_config.json:
     `ash
     cp api_config.template.json api_config.json
     `
   - Update pi_config.json or .env with your API keys:
     - Hugging Face API key: https://huggingface.co/settings/tokens
     - OpenRouter API key: https://openrouter.ai/settings/keys
     - HubSpot API key: https://app.hubspot.com/l/api-keys
     - MailerSend API key: https://app.mailersend.com/api-keys
   - Ensure at least one LLM API key (Hugging Face or OpenRouter) is provided
   - Ensure all API keys are valid

4. **Running the Application**:
   `ash
   # Activate virtual environment
   .\.venv\Scripts\activate
   
   # Run the main script
   python crm_agent.py
   `

## Project Structure
- crm_agent.py: Main application with agent workflow
- pi_config.template.json: Template for API configuration
- pi_config.json: User-created API configuration (not tracked by Git)
- .env: Environment variables (not tracked by Git)
- equirements.txt: Python dependencies

## Usage
- The system accepts queries like:
  - "create contact"
  - "update contact"
  - "create deal"
- The Global Orchestrator delegates tasks to the HubSpot Agent and Email Agent
- Results are printed to the console

## Notes
- Do not commit pi_config.json or .env to Git (excluded by .gitignore)
- HubSpot and MailerSend free tiers are sufficient for basic operations
- Use Hugging Face for LLaMA 3 8B or OpenRouter for LLaMA 4 Maverick (set the appropriate API key)
- Error handling is implemented for API failures
- The system uses LangGraph for workflow management

## Troubleshooting
- Ensure all API keys are valid
- Check internet connectivity for API calls
- Verify Python dependencies are installed
- Monitor rate limits: Hugging Face (30 requests/minute, 1M tokens/day), OpenRouter (14,400 requests/day), MailerSend (3,000 emails/month)
