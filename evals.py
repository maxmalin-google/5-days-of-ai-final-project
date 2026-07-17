import os
import json
import asyncio
from main import run_devsecops_pipeline

def test_golden_dataset():
    """
    Automated Evaluation Suite.
    Tests that the agent correctly removes the allUsers binding from vulnerable_gcs.tf.
    """
    test_file_path = "mock_infra/vulnerable_gcs.tf"
    
    # 1. Reset the golden dataset to vulnerable state
    vulnerable_content = '''resource "google_storage_bucket" "vulnerable_bucket" {
  name          = "my-company-public-data-bucket-123"
  location      = "US"
  force_destroy = true
}

# Vulnerability: Setting IAM binding to public (allUsers)
resource "google_storage_bucket_iam_binding" "public_read" {
  bucket = google_storage_bucket.vulnerable_bucket.name
  role   = "roles/storage.objectViewer"

  members = [
    "allUsers",
  ]
}
'''
    with open(test_file_path, "w") as f:
        f.write(vulnerable_content)
        
    # 2. Run the agent pipeline
    asyncio.run(run_devsecops_pipeline("mock_infra"))
    
    # 3. Assert the outcome
    with open(test_file_path, "r") as f:
        fixed_content = f.read()
        
    # The agent should have removed the public read binding
    assert "allUsers" not in fixed_content, "Agent failed to remove allUsers from GCS bucket."
    assert "google_storage_bucket" in fixed_content, "Agent accidentally deleted the entire bucket resource."
    print("✅ Evals passed: Agent successfully remediated the vulnerability without breaking the resource.")
