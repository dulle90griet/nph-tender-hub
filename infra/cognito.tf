locals {
  shared_data = try(jsondecode(data.aws_s3_object.shared_data[0].body), {})

  user_pool_id        = var.ENVIRONMENT == "shared" ? aws_cognito_user_pool.main[0].id : local.shared_data.user_pool_id
  user_pool_endpoint  = var.ENVIRONMENT == "shared" ? aws_cognito_user_pool.main[0].endpoint : local.shared_data.user_pool_endpoint
  user_pool_client_id = var.ENVIRONMENT == "shared" ? aws_cognito_user_pool_client.budibase_m2m_client[0].id : local.shared_data.user_pool_client_id
  oauth_scopes        = var.ENVIRONMENT == "shared" ? aws_cognito_resource_server.m2m_resource_server[0].scope : local.shared_data.oauth_scopes
}

resource "aws_cognito_user_pool" "main" {
  count = var.ENVIRONMENT == "shared" ? 1 : 0

  name                = "${var.PREFIX}-shared-user-pool"
  deletion_protection = "ACTIVE"
  user_pool_tier      = "ESSENTIALS"
  alias_attributes    = ["email"]

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
  }
}

data "aws_cognito_user_pool" "main" {
  count = var.ENVIRONMENT == "shared" ? 0 : 1

  user_pool_id = local.user_pool_id
}

resource "aws_cognito_user_pool_domain" "main" {
  count = var.ENVIRONMENT == "shared" ? 1 : 0

  domain       = "${var.PREFIX}-shared-user-pool-domain"
  user_pool_id = aws_cognito_user_pool.main[0].id
}

resource "aws_cognito_user_pool_client" "budibase_m2m_client" {
  count = var.ENVIRONMENT == "shared" ? 1 : 0

  name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-client"

  user_pool_id                  = aws_cognito_user_pool.main[0].id
  generate_secret               = true
  prevent_user_existence_errors = "ENABLED"

  access_token_validity   = 1
  enable_token_revocation = true
  refresh_token_validity  = 5
  id_token_validity       = 1
  auth_session_validity   = 3 # minutes

  token_validity_units {
    id_token      = "hours"
    access_token  = "hours"
    refresh_token = "days"
  }

  explicit_auth_flows                  = ["ALLOW_REFRESH_TOKEN_AUTH"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = aws_cognito_resource_server.m2m_resource_server[0].scope_identifiers
  allowed_oauth_flows                  = ["client_credentials"]
  supported_identity_providers         = ["COGNITO"]

  enable_propagate_additional_user_context_data = false

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
  }
}

data "aws_cognito_user_pool_client" "budibase_m2m_client" {
  count = var.ENVIRONMENT == "shared" ? 0 : 1

  user_pool_id = local.user_pool_id
  client_id    = local.user_pool_client_id
}

resource "aws_cognito_resource_server" "m2m_resource_server" {
  count = var.ENVIRONMENT == "shared" ? 1 : 0

  name         = "${var.PREFIX}-shared-m2m-resource-server"
  user_pool_id = aws_cognito_user_pool.main[0].id
  identifier   = "${var.PREFIX}-shared-m2m-resource-server"

  scope {
    scope_name        = "read"
    scope_description = "Read scope for ${var.PREFIX}-shared-m2m-resource-server"
  }

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
  }
}

resource "aws_apigatewayv2_authorizer" "budibase_m2m_authorizer" {
  name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-authorizer"

  api_id           = aws_apigatewayv2_api.http_api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]


  jwt_configuration {
    audience = [local.user_pool_client_id]
    issuer   = "https://${local.user_pool_endpoint}"
  }
}
