terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable Secret Manager API
resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Create the secret (container)
resource "google_secret_manager_secret" "duo_admin_api" {
  secret_id = var.secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

# Store the initial secret version
resource "google_secret_manager_secret_version" "duo_admin_api" {
  secret      = google_secret_manager_secret.duo_admin_api.id
  secret_data = var.duo_secret_json
}

# Grant Secret Accessor role to each reader
resource "google_secret_manager_secret_iam_member" "readers" {
  for_each  = toset(var.secret_reader_members)
  secret_id = google_secret_manager_secret.duo_admin_api.id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value
}

# Grant Secret Admin role to the admin
resource "google_secret_manager_secret_iam_member" "admin" {
  secret_id = google_secret_manager_secret.duo_admin_api.id
  role      = "roles/secretmanager.admin"
  member    = var.secret_admin_member
}

output "secret_name" {
  value       = google_secret_manager_secret.duo_admin_api.name
  description = "Full resource name of the secret"
}

output "secret_id" {
  value       = google_secret_manager_secret.duo_admin_api.secret_id
  description = "Short ID of the secret"
}
