resource "aws_cognito_user_pool" "main" {
  name = "${var.PREFIX}-${var.ENVIRONMENT}-user-pool"
  deletion_protection = "ACTIVE"
  user_pool_tier = "ESSENTIAL"
  alias_attributes = "email"
}

# aws_cognito_user_pool_client
##############################
# user_pool_id connects to aws_cognito_user_pool
# access_token_validity = 1 (default unit is hours)
# allowed_oauth_flows_user_pool_client = true (allow OAuth 2.0 features)
# allowed_oauth_flows = "code" / "implicit" / "client_credentials"?
# allowed_oauth_scopes = "phone" / "email" / "openid" / "profile" / "aws.cognito.signin.user.admin"?
# auth_session_validity = 3 (minutes)
# callback_urls = ?
# default_redirect_uri = ?
# enable_token_revocation = true
# enable_propagate_additional_user_context_data = false
# explicit_auth_flows = ALLOW_REFRESH_TOKEN_AUTH and *maybe* ADMIN_NO_SRP_AUTH ?
# generate_secret = true
# id_token_validity = 1 (default unit is hours)
# logout_urls = ?
# prevent_user_existence_errors = "ENABLED"
# read_attributes = leave as default?
# refresh_token_rotation = ?
# refresh_token_validity = 5 (default unit is days)
# supported_identity_providers = ? (look into aws_cognito_identity_provider)
# write_attributes = leave as default?

# aws_apigatewayv2_authorizer
#############################
# api_id connects to aws_apigatewayv2_api
# authorizer_type = "JWT"
# identity_sources = ["$request.header.Authorization"]
# jwt_configuation.audience = ? (leave blank?)
# jwt_configuration.issuer = https://issuer-cognito-idp.<my-region>.amazonaws.com/<my-user-pood-id>
# name = "nph-tender-hub-authorizer"
# authorization_payload_format_version = "2.0"

# aws_apigatewayv2_route (existing)
###################################
# authorization_scopes = ? (I think none needed)
# authorization_type = "JWT"
# authorizer_id connects to aws_apigatewayv2_authorizer
