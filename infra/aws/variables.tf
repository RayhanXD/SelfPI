variable "aws_region" {
  type        = string
  description = "Region for ECR, ECS, ALB (not CloudFront)."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Name prefix for AWS resources."
  default     = "selfpi"
}

variable "image_tag" {
  type        = string
  description = "ECR image tag the ECS service should run."
  default     = "latest"
}

variable "frontend_url" {
  type        = string
  description = "Vercel origin, e.g. https://selfpi.vercel.app (no trailing slash)."
}

variable "cors_origins" {
  type        = string
  description = "Comma-separated allowed origins. Defaults to frontend_url if empty."
  default     = ""
}

variable "cpu" {
  type        = number
  description = "Fargate task CPU units (256 = 0.25 vCPU)."
  default     = 512
}

variable "memory" {
  type        = number
  description = "Fargate task memory (MiB)."
  default     = 1024
}

variable "desired_count" {
  type        = number
  description = "Number of Fargate tasks. Use 0 until the first image is in ECR, then set to 1."
  default     = 0
}

# --- secrets (set via TF_VAR_* or terraform.tfvars; never commit real values) ---

variable "mongodb_uri" {
  type        = string
  sensitive   = true
  description = "Atlas connection string."
}

variable "session_secret" {
  type        = string
  sensitive   = true
  description = "Long random session signing secret."
}

variable "github_app_id" {
  type        = string
  sensitive   = true
  description = "GitHub App ID."
}

variable "github_app_private_key" {
  type        = string
  sensitive   = true
  description = "GitHub App private key PEM (literal newlines OK)."
}

variable "github_client_id" {
  type        = string
  sensitive   = true
}

variable "github_client_secret" {
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Optional; adjudicator / PR copy."
}
