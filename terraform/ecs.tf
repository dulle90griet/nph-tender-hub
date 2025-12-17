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

# DEFINE ECS TASK
resource "aws_ecs_task_definition" "budibase_ecs_task" {
    family = "${var.PREFIX}-budibase-ecs-task"

    # Launch type: AWS Fargate
    requires_compatibilities = [ "FARGATE" ]
    # OS: Linux/X86_64
    runtime_platform {
        operating_system_family = "LINUX"
        cpu_architecture        = "X86_64"
    }
    # Task size:
    #   - CPU: 2 vCPU (4GB)
    cpu                = 2
    #   - Memory: 6GB
    memory             = 5723 # 6 GB
    # Task role: NPHBudibaseRoleForECSTask
    task_role_arn      = aws_iam_role.budibase_ecs_task.arn
    # Task execution role: NPHBudibaseRoleForECSTaskExecution
    execution_role_arn = aws_iam_role.budibase_ecs_task_execution.arn

    # Enable ECS Exec -- this moves to aws_ecs_service

    # Volume 1
    volume {
        name = "${var.PREFIX}-budibase-ecs-task-storage"

        # Volume type: EFS
        efs_volume_configuration {
            # File system ID: (the file system we created earlier)
            file_system_id = aws_efs_file_system.budibase_fargate_data.id
            # Root directory: /
            # root_directory = "/"
            # NB warning "When specifying an access point or IAM authorization you must turn on transit encryption." - Go into 'Advanced configurations' and check 'Transit encryption'. Leave 'Port' blank.
            transit_encryption = "ENABLED"
            # Access point ID: nph_budibase_access_point (the access point with /data root we created earlier)
            authorization_config {
                access_point_id = aws_efs_access_point.budibase_fargate_access_point.id
                # iam             = "ENABLED" # check here in event of issues
            }
        }
    }

    # Container 1

    # Environment variables: None?

    container_definitions = jsonencode({
        name      = "${var.PREFIX}-budibase-container-1"
        # Essential: Yes
        essential = true
        image     = "${var.BUDIBASE_IMAGE_URL}:latest"
        # Resource allocation limits:
        #   - CPU: 2 vCPU
        cpu       = 2
        #   - Memory hard limit: 6 GB
        memory    = 5723 # in MiB = 6 GB
        #   - Memory soft limit: 0 GB (default)
        portMappings = [
            {
                name = "${var.PREFIX}-budibase-container-80-tcp"
                containerPort = 80
                approtocol = "http"
            },
            {
                name = "${var.PREFIX}-budibase-container-443-tcp"
                containerPort = 443
            },
            {
                name = "${var.PREFIX}-budibase-container-2222-tcp"
                containerPort = 2222
            },
            {
                name = "${var.PREFIX}-budibase-container-4369-tcp"
                containerPort = 4369
            },
            {
                name = "${var.PREFIX}-budibase-container-5984-tcp"
                containerPort = 5984
            },
            {
                name = "${var.PREFIX}-budibase-container-9100-tcp"
                containerPort = 9100
            }
        ]
        # Add mount point
        mountPoints = [
            {
                sourceVolume = "${var.PREFIX}-budibase-ecs-task-storage"
                containerPath = "/data"
            }
        ]
    })
}
