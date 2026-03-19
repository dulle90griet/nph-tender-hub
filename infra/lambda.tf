data "archive_file" "psycopg_layer" {
  type        = "zip"
  source_dir  = "${path.module}/../build/psycopg-layer"
  output_path = "${path.module}/../packages/layer/psycopg_layer.zip"
}

resource "aws_s3_object" "psycopg_layer" {
  bucket     = var.CODE_BUCKET
  key        = "layers/psycopg-layer.zip"
  source     = data.archive_file.psycopg_layer.output_path
  etag       = data.archive_file.psycopg_layer.output_base64sha256
  depends_on = [data.archive_file.psycopg_layer]
}

resource "aws_lambda_layer_version" "psycopg_layer" {
  layer_name       = "${var.PREFIX}-${var.ENVIRONMENT}-psycopg-layer"
  s3_bucket        = aws_s3_object.psycopg_layer.bucket
  s3_key           = aws_s3_object.psycopg_layer.key
  source_code_hash = data.archive_file.psycopg_layer.output_base64sha256
}

# data "archive_file" "create_instance_lambda_code" {
#   type        = "zip"
#   source_file = "${path.module}/../src/create_budibase_instance.py"
#   output_path = "${path.module}/../packages/lambda-ecs/create_budibase_instance.zip"

# }

resource "aws_lambda_function" "create_instance_lambda" {
  # filename      = data.archive_file.create_instance_lambda_code.output_path
  function_name = "${var.PREFIX}-${var.ENVIRONMENT}-create-instance-lambda"
  s3_bucket     = var.CODE_BUCKET
  s3_key        = "create_budibase_instance/${var.LAMBDA_CREATE_SERVICE_VERSION}.zip"
  role          = aws_iam_role.create_instance_lambda_execution_role.arn
  handler       = "create_budibase_instance.lambda_handler"
  # code_sha256   = data.archive_file.create_instance_lambda_code.output_base64sha256

  source_code_hash = filebase64sha256("${path.module}/../src/create_budibase_instance.py")

  runtime = "python3.12"
  publish = true

  environment {
    variables = {
      TARGET_CLUSTER_NAME = aws_ecs_cluster.budibase_cluster.name
      TARGET_SERVICE_NAME = aws_ecs_service.budibase_ecs_service.name
      ENVIRONMENT         = var.ENVIRONMENT
    }
  }
}

# data "archive_file" "destroy_instance_lambda_code" {
#   type        = "zip"
#   source_file = "${path.module}/../src/destroy_budibase_instance.py"
#   output_path = "${path.module}/../packages/lambda-ecs/destroy_budibase_instance.zip"

# }

resource "aws_lambda_function" "destroy_instance_lambda" {
  # filename      = data.archive_file.destroy_instance_lambda_code.output_path
  function_name = "${var.PREFIX}-${var.ENVIRONMENT}-destroy-instance-lambda"
  s3_bucket     = var.CODE_BUCKET
  s3_key        = "destroy_budibase_instance/${var.LAMBDA_DESTROY_SERVICE_VERSION}.zip"
  role          = aws_iam_role.destroy_instance_lambda_execution_role.arn
  handler       = "destroy_budibase_instance.lambda_handler"
  # code_sha256   = data.archive_file.destroy_instance_lambda_code.output_base64sha256

  source_code_hash = filebase64sha256(("${path.module}/../src/destroy_budibase_instance.py"))

  runtime = "python3.12"
  publish = true

  environment {
    variables = {
      TARGET_CLUSTER_NAME = aws_ecs_cluster.budibase_cluster.name
      TARGET_SERVICE_NAME = aws_ecs_service.budibase_ecs_service.name
      ENVIRONMENT         = var.ENVIRONMENT
    }
  }
}

resource "aws_lambda_function" "ci_checks_for_rds_lambda" {
  function_name = "${var.PREFIX}-${var.ENVIRONMENT}-ci-checks-for-rds-lambda"
  s3_bucket     = var.CODE_BUCKET
  s3_key        = "ci_checks_for_rds/${var.LAMBDA_CI_CHECKS_FOR_RDS_VERSION}.zip"
  role          = aws_iam_role.ci_checks_for_rds_lambda_execution_role.arn
  handler       = "ci_checks_for_rds.lambda_handler"

  source_code_hash = filebase64sha256(("${path.module}/../src/ci_checks_for_rds.py"))

  runtime = "python3.12"
  publish = true
  layers  = [aws_lambda_layer_version.psycopg_layer.arn]
  timeout = 30

  vpc_config {
    subnet_ids = tolist([
      for key in var.SUBNETS_BY_ENV[var.ENVIRONMENT] :
      aws_subnet.private[key].id
    ])
    security_group_ids = [aws_security_group.lambdas_for_rds.id]
  }

  # depends_on = [
  #   aws_iam_role_policy_attachment.ci_checks_for_rds_lambda_policy_attachment,
  #   aws_iam_role_policy_attachment.ci_checks_for_rds_lambda_secrets_access_policy_attachment,
  #   aws_iam_role_policy_attachment.ci_checks_for_rds_lambda_basic_execution_attachment,
  #   aws_iam_role_policy_attachment.ci_checks_for_rds_lambda_eni_managed_policy_attachment,
  #   aws_vpc_security_group_egress_rule.allow_lambda_egress_to_rds,
  #   aws_vpc_security_group_egress_rule.allow_lambda_https_egress_to_internet,
  #   aws_vpc_security_group_egress_rule.allow_psql_egress_from_rds,
  #   aws_vpc_security_group_ingress_rule.allow_lambda_ingress_to_rds,
  #   aws_route_table_private["0"],   # - and associations?
  #   aws_nat_gateway.ngw["0"],
  # ]
}
