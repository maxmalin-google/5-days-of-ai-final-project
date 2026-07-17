output "agent_service_url" {
  description = "The URL of the deployed Cloud Run Agent Service"
  value       = google_cloud_run_v2_service.agent_service.uri
}

output "agent_service_account_email" {
  description = "The email of the Service Account running the agent"
  value       = google_service_account.agent_sa.email
}
