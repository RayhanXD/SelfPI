resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 14
  tags              = { Project = var.project_name }
}

resource "aws_ecs_cluster" "main" {
  name = var.project_name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = { Project = var.project_name }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

locals {
  # Placeholder until the first image is pushed; CI updates the service to a digest/tag.
  container_image = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"

  secret_keys = [
    "MONGODB_URI",
    "SESSION_SECRET",
    "GITHUB_APP_ID",
    "GITHUB_APP_PRIVATE_KEY",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "ANTHROPIC_API_KEY",
  ]
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = local.container_image
      essential = true
      portMappings = [{
        containerPort = 8000
        hostPort      = 8000
        protocol      = "tcp"
      }]
      environment = [
        { name = "ENV", value = "production" },
        { name = "PORT", value = "8000" },
        { name = "MONGODB_DB", value = "selfpi" },
        { name = "INCLUDE_DEMO_APIS", value = "false" },
        { name = "WATCH_ENABLED", value = "true" },
        { name = "WATCH_INTERVAL_SECONDS", value = "300" },
        { name = "AUTH_REQUIRED", value = "true" },
        { name = "FRONTEND_URL", value = var.frontend_url },
        { name = "CORS_ORIGINS", value = local.cors_origins },
        {
          name  = "GITHUB_OAUTH_REDIRECT_URI"
          value = "https://${aws_cloudfront_distribution.api.domain_name}/auth/github/callback"
        },
        { name = "GITHUB_APP_INSTALLATION_ID", value = "" },
      ]
      secrets = [
        for key in local.secret_keys : {
          name      = key
          valueFrom = "${aws_secretsmanager_secret.app.arn}:${key}::"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 40
      }
    }
  ])

  tags = { Project = var.project_name }
}

resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]

  tags = { Project = var.project_name }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
