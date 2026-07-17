from pydantic import BaseModel, Field
import json
import os
from observability import get_tracer, log_event

tracer = get_tracer(__name__)

class TerraformScanInput(BaseModel):
    directory_path: str = Field(..., description="The relative path to the directory containing Terraform files.")

class SecurityPolicyInput(BaseModel):
    query: str = Field(..., description="The security concept or anomaly to query against the compliance database.")

class RemediationPlanInput(BaseModel):
    target_file: str = Field(..., description="The path to the vulnerable Terraform file.")
    proposed_hcl_patch: str = Field(..., description="The proposed HCL code to replace the vulnerable section.")
    justification: str = Field(..., description="Reasoning for why this patch satisfies compliance.")

def scan_terraform_directory(input_data: TerraformScanInput) -> dict:
    """
    Scans a directory for Terraform files and returns their raw contents.
    Provides clear error handling if the directory does not exist.
    
    Args:
        input_data (TerraformScanInput): A Pydantic model containing the 'directory_path' string.
    """
    with tracer.start_as_current_span("scan_terraform_directory"):
        log_event("INTENT", "Scanning Terraform directory", {"path": input_data.directory_path})
        
        if not os.path.exists(input_data.directory_path):
            log_event("OUTCOME", "Failed to scan directory (Not Found)", {"path": input_data.directory_path})
            return {
                "status": "error",
                "message": f"Directory '{input_data.directory_path}' not found.",
                "recovery_instruction": "Verify the directory path and try calling the tool again with the correct path."
            }
        
        files_content = {}
        for filename in os.listdir(input_data.directory_path):
            if filename.endswith(".tf"):
                with open(os.path.join(input_data.directory_path, filename), "r") as f:
                    files_content[filename] = f.read()
                    
        log_event("OUTCOME", "Successfully scanned directory", {"files_found": list(files_content.keys())})
        return {"status": "success", "files": files_content}

def apply_terraform_remediation(input_data: RemediationPlanInput) -> dict:
    """
    Simulates applying a remediation patch to a Terraform file. 
    In a real scenario, this would use the `terraform` CLI.
    
    Args:
        input_data (RemediationPlanInput): A Pydantic model containing the 'target_file' path, 'proposed_hcl_patch', and 'justification'.
    """
    with tracer.start_as_current_span("apply_terraform_remediation"):
        log_event("INTENT", "Applying Terraform Remediation", {"file": input_data.target_file})
        
        # In a real ADK flow, this tool would only execute after a Human-in-the-Loop approval.
        # This function simulates the patching process.
        if not os.path.exists(input_data.target_file):
            return {
                "status": "error",
                "message": f"Target file '{input_data.target_file}' not found.",
                "recovery_instruction": "Ensure the target file path is correct based on the scan results."
            }
            
        with open(input_data.target_file, "w") as f:
            f.write(input_data.proposed_hcl_patch)
            
        log_event("OUTCOME", "Successfully applied remediation", {"file": input_data.target_file})
        return {"status": "success", "message": "Patch applied successfully."}
