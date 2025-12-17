resource "aws_ecs_cluster" "budibase_cluster" {
    name = "${var.PREFIX}-budibase-cluster"

    # 'Fargate only' method of obtaining compute capacity (under Infrastructure) -- does this move to the ECS Service?

    # Container Insights turned off (under Monitoring)
    setting {
        name = "containerInsights"
        value = "disabled"
    }

    configuration {
        # ECS Exec encryption and logging set to 'Default' (also Monitoring).

        execute_command_configuration {
            kms_key_id = None # What was this in the Console?
            logging = "DEFAULT"
        }

        # Provide AWS KMS keys for encryption of both managed and ephemeral storage.
        managed_storage_configuration {
            kms_key_id = aws_kms_key.fargate_managed_storage.id
            fargate_ephemeral_storage_kms_key_id = aws_kms_key.fargate_ephemeral_storage.id
        }
    }

    depends_on = [ aws_iam_policy_document.kms_key_for_fargate ]
}
