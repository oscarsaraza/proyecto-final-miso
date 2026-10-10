terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = var.use_local_emulator ? "test" : null
  secret_key                  = var.use_local_emulator ? "test" : null
  skip_credentials_validation = var.use_local_emulator
  skip_metadata_api_check     = var.use_local_emulator
  skip_requesting_account_id  = var.use_local_emulator

  endpoints {
    s3                     = var.use_local_emulator ? var.local_emulator_endpoint : null
    sqs                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    ecr                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    ecs                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    rds                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    iam                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    kms                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    elbv2                  = var.use_local_emulator ? var.local_emulator_endpoint : null
    ec2                    = var.use_local_emulator ? var.local_emulator_endpoint : null
    cloudfront             = var.use_local_emulator ? var.local_emulator_endpoint : null
    cloudwatchlogs         = var.use_local_emulator ? var.local_emulator_endpoint : null
    cloudwatch             = var.use_local_emulator ? var.local_emulator_endpoint : null
    applicationautoscaling = var.use_local_emulator ? var.local_emulator_endpoint : null
  }

  default_tags {
    tags = {
      Project     = "Solventa"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

