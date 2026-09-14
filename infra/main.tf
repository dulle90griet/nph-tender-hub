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

# Save or retrieve shared data

resource "aws_s3_object" "shared_data" {
  count = var.ENVIRONMENT == "shared" ? 1 : 0

  bucket = var.SHARED_DATA_BUCKET
  key    = "shared_data.json"

  content = jsonencode({
    user_pool_id        = aws_cognito_user_pool.main[0].id
    user_pool_endpoint  = aws_cognito_user_pool.main[0].endpoint
    user_pool_client_id = aws_cognito_user_pool_client.budibase_m2m_client[0].id
    oauth_scopes        = aws_cognito_resource_server.m2m_resource_server[0].scope
  })

  content_type = "application/json"
}

data "aws_s3_object" "shared_data" {
  count = var.ENVIRONMENT == "shared" ? 0 : 1

  bucket = var.SHARED_DATA_BUCKET
  key    = "shared_data.json"
}
