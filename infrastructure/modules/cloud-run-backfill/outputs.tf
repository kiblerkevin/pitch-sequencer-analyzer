output "scheduler_service_account_email" {
  description = "Email of the Cloud Scheduler service account"
  value       = google_service_account.scheduler.email
}
