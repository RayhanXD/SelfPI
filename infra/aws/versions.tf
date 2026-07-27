terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# CloudFront ACM certs must live in us-east-1 (only used if you pass a custom cert later).
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
