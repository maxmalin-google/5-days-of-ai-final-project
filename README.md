# DevSecOps Remediation Agent

This project implements a multi-agent AI system for DevSecOps using Google's Python Agentic Development Kit (ADK). The system scans cloud configuration files (Terraform), identifies security misconfigurations based on company policies, and proposes/applies Terraform remediations.

## Architecture & Features

- **Multi-Agent Orchestration**: Uses a Coordinator pattern to route tasks. A "Scanner Agent" quickly parses raw infrastructure files, an "Architect Agent" reasons over policies to design patches, and a **"Guardrail Agent"** provides self-evaluation before any patch is approved.
- **Context & Memory**: Implements a simulated Vector DB for fast policy retrieval and an **asynchronous context compaction** mechanism to manage LLM token limits over long sessions without blocking the UI.
- **Human-in-the-Loop**: High-stakes actions, such as applying Terraform code, are paused for explicit human review and approval.
- **Observability**: Fully instrumented with OpenTelemetry for distributed tracing. Includes a custom JSON logger that **simulates calling the Google Cloud DLP API** to automatically redact PII and sensitive secrets before logging.
- **Secure Secret Management**: API keys and database tokens are securely injected at runtime via a **Google Cloud Secret Manager mock**, strictly avoiding hardcoded credentials.
- **Strict Interfaces**: Uses Pydantic schemas to strictly validate inputs/outputs and implements guided error recovery for tool failures.

## Getting Started

### Prerequisites
- Python 3.9+
- Recommended: Virtual Environment

### Installation
1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage (Local)
Run the main coordinator pipeline locally to scan the `mock_infra/` directory and propose remediations:
```bash
python main.py
```

### Usage (ADK CLI)
This project is configured for the Google Agentic Development Kit CLI via `agent.yaml`.
To deploy the agent and its required infrastructure (Cloud Run, Secret Manager) to GCP:
```bash
agent deploy --config agent.yaml
```

### Running Evals
To run the automated test suite against the dataset of vulnerable infrastructure:
```bash
pytest evals.py
```
