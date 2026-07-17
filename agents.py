import json
from tools import scan_terraform_directory, apply_terraform_remediation, TerraformScanInput, RemediationPlanInput
from memory import query_security_policy

# Mocking the ADK syntax for this assignment
class Agent:
    def __init__(self, name, model, system_prompt, tools=None):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        
    def prompt(self, message: str):
        """Mock LLM response for demonstration purposes."""
        if self.name == "Scanner Agent":
            return json.dumps({
                "anomalies": [
                    {"file": "mock_infra/vulnerable_gcs.tf", "issue": "allUsers binding detected on GCS bucket"}
                ]
            })
        elif self.name == "Architect Agent":
            # Propose a fixed terraform string
            fixed_tf = '''resource "google_storage_bucket" "vulnerable_bucket" {
  name          = "my-company-public-data-bucket-123"
  location      = "US"
  force_destroy = true
}

# Remediation applied: removed public read binding to comply with SOC2-001
'''
            return json.dumps({
                "target_file": "mock_infra/vulnerable_gcs.tf",
                "proposed_hcl_patch": fixed_tf,
                "justification": "SOC2-001 prohibits allUsers on GCS buckets."
            })
        return "Generic response."


# Scanner Agent uses a fast model (e.g. Flash) to parse raw config files cheaply
scanner_agent = Agent(
    name="Scanner Agent",
    model="gemini-1.5-flash", 
    system_prompt="""You are a Security Scanner. Your job is to parse raw configuration files (like Terraform) and flag potential anomalies. 
Focus on identifying public access, missing encryption, or overly permissive IAM roles. Output findings in strict JSON format.""",
    tools=[scan_terraform_directory]
)

# Architect Agent uses a reasoning model (e.g. Pro) to design fixes based on Vector DB policies
architect_agent = Agent(
    name="Architect Agent",
    model="gemini-1.5-pro",
    system_prompt="""You are a DevSecOps Architect. You take anomalies found by the Scanner, query the company security policy (Vector DB) to understand the requirements, and then formulate a remediation plan (Terraform patch). You must justify your changes based on policy docs.""",
    tools=[query_security_policy, apply_terraform_remediation]
)

# Guardrail Agent checks the proposed changes before they reach the user
guardrail_agent = Agent(
    name="Guardrail Agent",
    model="gemini-1.5-pro",
    system_prompt="""You are a Security Guardrail. Your job is to perform a static self-evaluation on proposed infrastructure changes. 
Reject any changes that introduce new vulnerabilities or attempt destructive actions (like dropping a database without a backup). Output {"approved": true/false, "reason": "..."}."""
)
