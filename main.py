import json
import asyncio
from agents import scanner_agent, architect_agent, guardrail_agent
from tools import scan_terraform_directory, apply_terraform_remediation, TerraformScanInput, RemediationPlanInput, SecurityPolicyInput
from memory import query_security_policy, ContextCompactor
from observability import log_event, get_tracer
from secrets import secret_manager

tracer = get_tracer(__name__)
context_manager = ContextCompactor()

async def run_devsecops_pipeline(directory: str):
    """
    Implements the Coordinator pattern:
    1. Scanner agent finds anomalies.
    2. Architect agent proposes fixes.
    3. Human-in-the-Loop validates.
    """
    with tracer.start_as_current_span("devsecops_coordinator_pipeline"):
        log_event("SYS", "Starting DevSecOps Pipeline", {"target_dir": directory})
        
        # 0. INITIALIZATION: Securely fetch API keys
        api_key = secret_manager.access_secret_version("llm-api-key")
        log_event("SYS", "API Key loaded securely from Secret Manager.", {"status": "success"})
        
        # 1. SCAN PHASE (Flash Model)
        log_event("SYS", "Invoking Scanner Agent", {"model": scanner_agent.model})
        # Simulate tool call to scan
        scan_results = scan_terraform_directory(TerraformScanInput(directory_path=directory))
        context_manager.add_interaction("system", f"Scan Results: {list(scan_results.get('files', {}).keys())}")
        
        # Scanner LLM logic (mocked)
        anomalies_response = json.loads(scanner_agent.prompt(f"Analyze files in {directory}"))
        anomalies = anomalies_response.get("anomalies", [])
        
        if not anomalies:
            log_event("SYS", "No anomalies found. Exiting.")
            return
            
        context_manager.add_interaction("assistant", f"Anomalies found: {anomalies}")
        log_event("OUTCOME", "Scanner Agent complete", {"anomalies_count": len(anomalies)})
        
        # 2. ARCHITECT PHASE (Pro Model)
        for anomaly in anomalies:
            log_event("SYS", "Invoking Architect Agent", {"anomaly": anomaly["issue"]})
            
            # Architect queries policies
            policy_results = query_security_policy(SecurityPolicyInput(query=anomaly["issue"]))
            context_manager.add_interaction("system", f"Policy results: {policy_results}")
            
            # Architect designs fix (mocked LLM call)
            plan_response = json.loads(architect_agent.prompt(f"Fix anomaly: {anomaly}"))
            
            # 3. GUARDRAIL PHASE (Self-Eval)
            log_event("SYS", "Invoking Guardrail Agent", {"file": plan_response['target_file']})
            guardrail_eval = {"approved": True, "reason": "No destructive actions detected. Fix adheres to least-privilege."} # Mocked response from guardrail_agent
            
            if not guardrail_eval["approved"]:
                log_event("OUTCOME", "Guardrail rejected the plan", {"reason": guardrail_eval["reason"]})
                print(f"🛑 Guardrail blocked execution: {guardrail_eval['reason']}")
                continue
                
            log_event("OUTCOME", "Guardrail approved the plan", {"reason": guardrail_eval["reason"]})

            # 4. HUMAN IN THE LOOP (HITL)
            print("\n" + "="*50)
            print("🚨 HIGH STAKES ACTION PENDING 🚨")
            print(f"Target File: {plan_response['target_file']}")
            print(f"Justification: {plan_response['justification']}")
            print("Proposed HCL Patch:")
            print("-" * 40)
            print(plan_response['proposed_hcl_patch'])
            print("-" * 40)
            
            # Simulate waiting for user input
            # In a real environment, you'd use input() or an API endpoint.
            # We bypass the actual `input()` here so the CI/tests don't hang, 
            # but assume the user approved it.
            approval = "yes" # input("Do you approve this change? (yes/no): ")
            log_event("INTENT", "Waiting for Human Approval", {"file": plan_response['target_file']})
            
            if approval.lower().strip() == 'yes':
                log_event("OUTCOME", "Human approved change.")
                apply_terraform_remediation(RemediationPlanInput(**plan_response))
                context_manager.add_interaction("assistant", f"Applied fix to {plan_response['target_file']}")
            else:
                log_event("OUTCOME", "Human rejected change.")
                
        log_event("SYS", "DevSecOps Pipeline complete", {})
        
        # Give async compaction tasks time to finish before exiting in this simple script
        await asyncio.sleep(1.5)

if __name__ == "__main__":
    asyncio.run(run_devsecops_pipeline("mock_infra"))
