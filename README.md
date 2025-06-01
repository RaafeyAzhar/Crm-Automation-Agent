# CRM Automation Agent

This project implements an AI-powered autonomous agent system for CRM automation with HubSpot integration and email notifications using free APIs.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- HubSpot account with API key (free tier available)
- MailerSend account with API key (free tier with 3,000 emails/month)
- Hugging Face account with API key (free tier for LLaMA 3 8B Instruct) **OR** OpenRouter account with API key (free tier for LLaMA 4 Maverick)

### 2. Installation

```bash
# Create and activate virtual environment
python -m venv .venv
.\\.venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

- Copy the API config template to create your own config file:

```bash
cp api_config.template.json api_config.json
```

- Update `api_config.json` or `.env` with your API keys:

  - Hugging Face API key: https://huggingface.co/settings/tokens  
  - OpenRouter API key: https://openrouter.ai/settings/keys  
  - HubSpot API key: https://app.hubspot.com/l/api-keys  
  - MailerSend API key: https://app.mailersend.com/api-keys  

- Make sure at least one LLM API key (Hugging Face or OpenRouter) is provided.  
- Verify that all API keys are valid.

### 4. Running the Application

```bash
# Activate virtual environment
.\\.venv\\Scripts\\activate

# Run the main script
python crm_agent.py
```

---

## Project Structure

- `crm_agent.py` - Main application with agent workflow  
- `api_config.template.json` - Template for API configuration  
- `api_config.json` - Your personal API configuration (excluded from Git)  
- `.env` - Environment variables file (excluded from Git)  
- `requirements.txt` - Python dependencies list  

---

## Usage

- The system accepts commands like:  
  - `"create contact"`  
  - `"update contact"`  
  - `"create deal"`  

- The Global Orchestrator delegates tasks to:  
  - HubSpot Agent  
  - Email Agent  

- Task results are printed to the console.

---

## Notes

- **Do not commit** `api_config.json` or `.env` files to Git — these contain sensitive information and are ignored via `.gitignore`.  
- HubSpot and MailerSend free tiers are sufficient for basic CRM and email operations.  
- Use Hugging Face API for LLaMA 3 8B or OpenRouter API for LLaMA 4 Maverick — configure accordingly.  
- Error handling is implemented to manage API failures gracefully.  
- The system uses [LangGraph](https://langgraph.com) for workflow orchestration and task management.

---

## Troubleshooting

- Verify all API keys are valid and have correct permissions.  
- Check your internet connection for external API calls.  
- Confirm Python dependencies are properly installed (`pip install -r requirements.txt`).  
- Monitor rate limits of services used:  
  - Hugging Face: 30 requests/minute, 1 million tokens/day  
  - OpenRouter: 14,400 requests/day  
  - MailerSend: 3,000 emails/month  

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


## Contact

For questions or support, please open an issue on this repository or contact the maintainer directly.
