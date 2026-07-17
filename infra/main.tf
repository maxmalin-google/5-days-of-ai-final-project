terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

# Enable required APIs
resource "google_project_service" "secretmanager_api" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudrun_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# 1. Service Account for the Agent (Least Privilege)
resource "google_service_account" "agent_sa" {
  account_id   = "devsecops-agent-sa"
  display_name = "DevSecOps Agent Service Account"
}

# 2. Secret Manager Secret for the LLM API Key
resource "google_secret_manager_secret" "llm_api_key" {
  secret_id = "llm-api-key"
  replication {
    auto {}
  }
}

# Give the agent SA permission to access the secret
resource "google_secret_manager_secret_iam_member" "agent_secret_access" {
  secret_id = google_secret_manager_secret.llm_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
  
  depends_on = [google_project_service.secretmanager_api]
}

# 3. Cloud Run Service to host the Agent pipeline
resource "google_cloud_run_v2_service" "agent_service" {
  name     = "devsecops-agent-service"
  location = "us-central1"

  template {
    service_account = google_service_account.agent_sa.email

    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/repo/devsecops-agent:latest"
      
      # The agent requires a lot of memory for ChromaDB vector embeddings
      resources {
        limits = {
          memory = "2Gi"
          cpu    = "1"
        }
      }
    }
  }
  
  depends_on = [google_project_service.cloudrun_api]
}
