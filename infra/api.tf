resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.PREFIX}-${var.ENVIRONMENT}-http-api"
  protocol_type = "HTTP"
  description   = "HTTP API allowing programs to interface with the ${var.CLIENT} ${var.PROJECT} database"
}

resource "aws_lambda_permission" "allow_http_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.http_api_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "http_api_lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"

  connection_type        = "INTERNET"
  description            = "Lambda integration for ${var.CLIENT} ${var.PROJECT} HTTP API"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.http_api_lambda.invoke_arn
  payload_format_version = "2.0"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_apigatewayv2_route" "http_api_get_department_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /department"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"

}

resource "aws_apigatewayv2_route" "http_api_get_job_title_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /job-title"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_job_title_titles_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /job-title/titles"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_post_job_title_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "POST /job-title"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_patch_job_title_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "PATCH /job-title/{job_title_id}"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_consumable_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /consumable"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_consumable_names_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /consumable/names"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_post_consumable_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "POST /consumable"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_patch_consumable_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "PATCH /consumable/{consumable_id}"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_service_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /service"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_service_slug_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /service/slugs"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_post_service_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "POST /service"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_patch_service_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "PATCH /service/{service_id}"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_overhead_cost_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /overhead-cost"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_post_overhead_cost_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "POST /overhead-cost"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_patch_overhead_cost_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "PATCH /overhead-cost/{overhead_cost_id}"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_labour_cost_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /labour-cost"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_post_labour_cost_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "POST /labour-cost"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_patch_labour_cost_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "PATCH /labour-cost/{service_id}/{title_engaged_id}"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_get_direct_cost_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /direct-cost"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_post_direct_cost_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "POST /direct-cost"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "http_api_patch_direct_cost_route" {
  api_id   = aws_apigatewayv2_api.http_api.id
  route_key = "PATCH /direct-cost/{service_id}/{consumable_id}"

  target = "integrations/${aws_apigatewayv2_integration.http_api_lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "http_api_default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}
