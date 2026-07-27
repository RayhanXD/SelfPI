locals {
  cors_origins = var.cors_origins != "" ? var.cors_origins : var.frontend_url

  app_secret = {
    MONGODB_URI            = var.mongodb_uri
    SESSION_SECRET         = var.session_secret
    GITHUB_APP_ID          = var.github_app_id
    GITHUB_APP_PRIVATE_KEY = var.github_app_private_key
    GITHUB_CLIENT_ID       = var.github_client_id
    GITHUB_CLIENT_SECRET   = var.github_client_secret
    ANTHROPIC_API_KEY      = var.anthropic_api_key
  }
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${var.project_name}/api"
  recovery_window_in_days = 0
  tags                    = { Project = var.project_name }
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id     = aws_secretsmanager_secret.app.id
  secret_string = jsonencode(local.app_secret)
}
