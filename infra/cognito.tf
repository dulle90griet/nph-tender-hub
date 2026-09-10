resource "aws_cognito_user_pool" "main" {
  name                = "${var.PREFIX}-${var.ENVIRONMENT}-user-pool"
  deletion_protection = "ACTIVE"
  user_pool_tier      = "ESSENTIALS"
  alias_attributes    = ["email"]

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
  }
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.PREFIX}-${var.ENVIRONMENT}-user-pool-domain"
  user_pool_id = aws_cognito_user_pool.main.id
}


resource "aws_cognito_user_pool_client" "budibase_m2m_client" {
  name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-client"

  user_pool_id                  = aws_cognito_user_pool.main.id
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
  allowed_oauth_scopes                 = aws_cognito_resource_server.m2m_resource_server.scope_identifiers
  allowed_oauth_flows                  = ["client_credentials"]
  supported_identity_providers         = ["COGNITO"]

  enable_propagate_additional_user_context_data = false

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
  }
}

resource "aws_cognito_resource_server" "m2m_resource_server" {
  name         = "${var.PREFIX}-${var.ENVIRONMENT}-m2m-resource-server"
  user_pool_id = aws_cognito_user_pool.main.id
  identifier   = "${var.PREFIX}-${var.ENVIRONMENT}-m2m-resource-server"

  scope {
    scope_name        = "read"
    scope_description = "Read scope for ${var.PREFIX}-${var.ENVIRONMENT}-m2m-resource-server"
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
    audience = [aws_cognito_user_pool_client.budibase_m2m_client.id]
    issuer   = "https://${aws_cognito_user_pool.main.endpoint}"
  }
}
