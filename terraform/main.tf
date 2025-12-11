# Configure the AWS provider

provider "aws" {
    region = var.AWS_REGION
    default_tags {
      tags = {
        Client        = "NPH"
        Project       = "Tender Hub"
        Repo_name     = "nph-tender-hub"
        Deployed_from = "Terraform"
        Environment   = "dev"
      }
    }
}

# Retrieve details of our current AWS connection

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
