# Default VPC keeps cost near-zero (no NAT gateway). Fine for a portfolio deploy.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_subnet" "default" {
  for_each = toset(data.aws_subnets.default.ids)
  id       = each.value
}

locals {
  # Prefer subnets that auto-assign public IPs (typical default-VPC public subnets).
  public_subnet_ids = [
    for id, sn in data.aws_subnet.default : id
    if sn.map_public_ip_on_launch
  ]
  subnet_ids = length(local.public_subnet_ids) >= 2 ? local.public_subnet_ids : data.aws_subnets.default.ids
}

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb"
  description = "ALB ingress for SelfPI API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP from internet / CloudFront"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-alb"
    Project = var.project_name
  }
}

resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-ecs"
  description = "Fargate tasks — only ALB may reach the API port"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "API from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Atlas, GitHub, OpenAPI upstreams"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-ecs"
    Project = var.project_name
  }
}
