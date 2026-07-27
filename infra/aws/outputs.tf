output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.api.name
}

output "ecs_task_family" {
  value = aws_ecs_task_definition.api.family
}

output "alb_dns_name" {
  value = aws_lb.api.dns_name
}

output "api_url" {
  description = "HTTPS API origin (set VITE_API_URL and GitHub App URLs to this)."
  value       = "https://${aws_cloudfront_distribution.api.domain_name}"
}

output "github_oauth_callback" {
  value = "https://${aws_cloudfront_distribution.api.domain_name}/auth/github/callback"
}

output "github_setup_url" {
  value = "https://${aws_cloudfront_distribution.api.domain_name}/auth/github/installed"
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.api.name
}
