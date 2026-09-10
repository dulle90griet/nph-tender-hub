resource "aws_cognito_user_pool" "main" {
  name                = "${var.PREFIX}-${var.ENVIRONMENT}-user-pool"
  deletion_protection = "ACTIVE"
  user_pool_tier      = "ESSENTIALS"
  alias_attributes    = ["email"]
}

resource "aws_cognito_user_pool_client" "budibase_m2m_client" {
  name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-client"

  user_pool_id = aws_cognito_user_pool.main.id
  # supported_identity_providers = ? (look into aws_cognito_identity_provider)
  generate_secret = true

  access_token_validity   = 1 # hours
  enable_token_revocation = true
  refresh_token_validity  = 5 #days
  id_token_validity       = 1 # hours
  auth_session_validity   = 3 # minutes

  explicit_auth_flows                  = ["ALLOW_REFRESH_TOKEN_AUTH"]
  allowed_oauth_flows_user_pool_client = false

  # read_attributes = leave as default?
  # write_attributes = leave as default?

  enable_propagate_additional_user_context_data = false
  prevent_user_existence_errors                 = "ENABLED"
}

resource "aws_apigatewayv2_authorizer" "budibase_m2m_authorizer" {
  name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-authorizer"

  api_id                            = aws_apigatewayv2_api.http_api.id
  authorizer_type                   = "JWT"
  identity_sources                  = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.budibase_m2m_client.id]
    issuer   = "https://${aws_cognito_user_pool.main.endpoint}"
  }
}

# aws_apigatewayv2_route (existing)
###################################
# authorization_scopes = ? (I think none needed)
# authorization_type = "JWT"
# authorizer_id connects to aws_apigatewayv2_authorizer
