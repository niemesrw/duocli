variable "project_id" {
  description = "GCP project ID to create the secret in"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-east1"
}

variable "secret_id" {
  description = "ID for the secret in Secret Manager"
  type        = string
  default     = "duocli-duo-admin-api"
}

variable "duo_secret_json" {
  description = "Duo credentials as JSON: {\"DUO_IKEY\":\"...\",\"DUO_SKEY\":\"...\",\"DUO_HOST\":\"...\"}"
  type        = string
  sensitive   = true
}

variable "secret_admin_member" {
  description = "IAM member who can manage the secret (e.g. user:alice@example.com)"
  type        = string
}

variable "secret_reader_members" {
  description = "IAM members who can read the secret (e.g. [\"user:bob@example.com\", \"group:duo-admins@example.com\"])"
  type        = list(string)
  default     = []
}
