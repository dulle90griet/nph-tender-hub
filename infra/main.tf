# Configure the AWS provider

provider "aws" {
  region = var.AWS_REGION
  default_tags {
    tags = {
      Client        = var.CLIENT
      Project       = var.PROJECT
      Repo_name     = var.REPO_NAME
      Deployed_from = "Terraform"
      Environment   = var.ENVIRONMENT
    }
  }
}

# Retrieve details of our current AWS connection

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
