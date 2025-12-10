# Configure the AWS provider

provider "aws" {
    region = var.AWS_REGION
    default_tags {
      tags = {
        Project_name = "NPH Pricing and Tender Hub"
        Repo_name = "nph-tender-hub"
        Deployed_from = "Terraform"
        Environment = "dev"
      }
    }
}

# Define output data helpful for troubleshooting

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
