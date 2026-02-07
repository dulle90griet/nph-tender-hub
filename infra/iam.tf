# Create ECS Task Iam role. Trusted entity type: AWS service. Use case: Elastic Container Service Task. Permissions policies: none for now. Add client and project tags. Once created, use the `aws:SourceAccount` or `aws:SourceArn` condition keys in the trust relationship policy to prevent the confused deputy security issue. See here (https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html?icmpid=docs_ecs_hp-task-definition) and here (https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html). Add a statement allowing "ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel", "ssmmessages:OpenControlChannel" and "ssmmessages:OpenDataChannel".

resource "aws_iam_role" "budibase_ecs_task" {
    name = "${var.PREFIX}${var.ENVIRONMENT}BudibaseTFRoleForECSTask"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "ecs-tasks.amazonaws.com"
                }
            },
        ]
    })
}

resource "aws_iam_policy" "budibase_ecs_task_policy" {
    name = "${var.PREFIX}${var.ENVIRONMENT}BudibaseECSTaskPolicy"

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenDataChannel",
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:OpenControlChannel"
                ]
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "budbase_ecs_task_policy" {
    role = aws_iam_role.budibase_ecs_task.name
    policy_arn = aws_iam_policy.budibase_ecs_task_policy.arn
}

# Create ECS Task Execution IAM role. Trusted entity type: AWS service. Use case: Elastic Container Service Task Execution Role. Permissions policies: just the required AmazonECSTaskExecutionRolePolicy to begin with. Add client and project tags. Not sure if I need to worry about the confused deputy security issue in this case.

resource "aws_iam_role" "budibase_ecs_task_execution" {
    name = "${var.PREFIX}${var.ENVIRONMENT}BudibaseTFRoleForECSTaskExecution"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "ecs-tasks.amazonaws.com"
                }
            },
        ]
    })
}

data "aws_iam_policy" "ecs_task_execution_role_policy" {
    arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create IAM policy allowing `kms:GenerateDataKeyWithoutPlaintext` and `kms:Decrypt` on the ARN of the KMS key for managed storage. Add client and project tags.
# Create IAM policy allowing `kms:GenerateDataKeyWithoutPlaintext` and `kms:Decrypt` on the ARN of the KMS key for ephemeral storage. Add client and project tags.

resource "aws_iam_policy" "budibase_task_execution_kms_policy" {
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "kms:GenerateDataKeyWithoutPlaintext",
                    "kms:Decrypt"
                ]
                Resource = [
                    "${aws_kms_key.fargate_managed_storage.arn}",
                    "${aws_kms_key.fargate_ephemeral_storage.arn}"
                ]
            }
        ]
    })
}

# Add these policies to the Task Execution Role.

resource "aws_iam_role_policy_attachment" "budibase_task_execution_managed_policy" {
    role       = aws_iam_role.budibase_ecs_task_execution.name
    policy_arn = data.aws_iam_policy.ecs_task_execution_role_policy.arn
}

resource "aws_iam_role_policy_attachment" "budibase_task_execution_kms_policy" {
    role       = aws_iam_role.budibase_ecs_task_execution.name
    policy_arn = aws_iam_policy.budibase_task_execution_kms_policy.arn
}


# IAM roles and policies for Lambda execution
data "aws_iam_policy_document" "lambda_assume_role" {
    statement {
        effect = "Allow"

        principals {
          type        = "Service"
          identifiers = [ "lambda.amazonaws.com" ]
        }

        actions = [ "sts:AssumeRole" ]
    }
}

resource "aws_iam_role" "create_instance_lambda_execution_role" {
    name               = "${var.PREFIX}${var.ENVIRONMENT}BudibaseRoleForCreateInstanceLambda"
    assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role" "destroy_instance_lambda_execution_role" {
    name               = "${var.PREFIX}${var.ENVIRONMENT}BudibaseRoleForDestroyInstanceLambda"
    assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "generic_create_log_group_policy_doc" {
    statement {
        sid       = "GenericCreateLogGroup"
        effect    = "Allow"
        actions   = [ "logs:CreateLogGroup" ]
        resources = [ "arn:aws:logs:${var.AWS_REGION}:${data.aws_caller_identity.current.account_id}:*" ]
    }
}

data "aws_iam_policy_document" "generic_update_service_policy_doc" {
    statement {
        sid       = "GenericUpdateService"
        effect    = "Allow"
        actions   = [ "ecs:UpdateService" ]
        resources = [ "arn:aws:ecs:${var.AWS_REGION}:${data.aws_caller_identity.current.account_id}:service/*" ]
    }
}

data "aws_iam_policy_document" "create_instance_lambda_policy_doc" {
    source_policy_documents = [
        data.aws_iam_policy_document.generic_create_log_group_policy_doc.json,
        data.aws_iam_policy_document.generic_update_service_policy_doc.json
    ]

    statement {
        sid       = "CreateInstanceLambdaLogging"
        effect    = "Allow"
        
        actions = [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
        ]

        resources = [ "arn:aws:logs:${var.AWS_REGION}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.PREFIX}-create-instance-lambda:*" ]
    }
}

data "aws_iam_policy_document" "destroy_instance_lambda_policy_doc" {
    source_policy_documents = [
        data.aws_iam_policy_document.generic_create_log_group_policy_doc.json,
        data.aws_iam_policy_document.generic_update_service_policy_doc.json
    ]

    statement {
        sid       = "DestroyInstanceLambdaLogging"
        effect    = "Allow"
        
        actions = [
            "logs:DestroyLogStream",
            "logs:PutLogEvents"
        ]

        resources = [ "arn:aws:logs:${var.AWS_REGION}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.PREFIX}-destroy-instance-lambda:*" ]
    }
}

resource "aws_iam_policy" "create_instance_lambda_policy" {
    name        = "${var.PREFIX}${var.ENVIRONMENT}BudibasePolicyForCreateInstanceLambda"
    description = "Policy allowing the Budibase Create Instance Lambda to write logs and update the Budibase ECS service."
    policy      = data.aws_iam_policy_document.create_instance_lambda_policy_doc.json
}

resource "aws_iam_policy" "destroy_instance_lambda_policy" {
    name        = "${var.PREFIX}${var.ENVIRONMENT}BudibasePolicyForDestroyInstanceLambda"
    description = "Policy allowing the Budibase Destroy Instance Lambda to write logs and update the Budibase ECS service."
    policy      = data.aws_iam_policy_document.destroy_instance_lambda_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "create_instance_lambda_policy_attachment" {
    role       = aws_iam_role.create_instance_lambda_execution_role.name
    policy_arn = aws_iam_policy.create_instance_lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "destroy_instance_lambda_policy_attachment" {
    role       = aws_iam_role.destroy_instance_lambda_execution_role.name
    policy_arn = aws_iam_policy.destroy_instance_lambda_policy.arn
}
