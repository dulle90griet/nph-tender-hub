data "archive_file" "create_instance_lambda_code" {
    type = "zip"
    source_file = "${path.module}/../src/create_budibase_instance.py"
    output_path = "${path.module}/../packages/lambda-ecs/create_budibase_instance.zip"

}

resource "aws_lambda_function" "create_instance_lambda" {
    filename         = data.archive_file.create_instance_lambda_code.output_path
    function_name    = "${var.PREFIX}-create-instance-lambda"
    role             = aws_iam_role.lambda_execution_role.arn
    handler          = "create_budibase_instance.lambda_handler"
    code_sha256      = data.archive_file.create_instance_lambda_code.output_base64sha256

    runtime = "python3.12"
    publish = true

    environment {
        variables = {
            TARGET_CLUSTER_NAME = aws_ecs_cluster.budibase_cluster.name
            TARGET_SERVICE_NAME = aws_ecs_service.budibase_ecs_service.name
        }
    }
}
