locals {
    budibase_container_name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-container"
    budibase_cluster_name   = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-cluster"
}

resource "aws_ecs_cluster" "budibase_cluster" {
    name = "${local.budibase_cluster_name}"

    # 'Fargate only' method of obtaining compute capacity (under Infrastructure) -- does this move to the ECS Service?

    # Container Insights turned off (under Monitoring)
    setting {
        name = "containerInsights"
        value = "disabled"
    }

    configuration {
        # ECS Exec encryption and logging set to 'Default' (also Monitoring).

        execute_command_configuration {
            # kms_key_id = None # What was this in the Console?
            logging = "DEFAULT"
        }

        # Provide AWS KMS keys for encryption of both managed and ephemeral storage.
        managed_storage_configuration {
            kms_key_id = aws_kms_key.fargate_managed_storage.id
            fargate_ephemeral_storage_kms_key_id = aws_kms_key.fargate_ephemeral_storage.arn
        }
    }

    depends_on = [ data.aws_iam_policy_document.kms_key_for_fargate ]
}

# DEFINE ECS TASK
resource "aws_ecs_task_definition" "budibase_ecs_task" {
    # OS: Linux/X86_64
    runtime_platform {
        operating_system_family = "LINUX"
        cpu_architecture        = "X86_64"
    }

    family                   = "${var.PREFIX}-budibase-ecs-task"
    # Launch type: AWS Fargate
    requires_compatibilities = [ "FARGATE" ]
    network_mode             = "awsvpc"
    # Task size:
    #   - CPU: 2 vCPU (4GB)
    cpu                      = 2048
    #   - Memory: 6GB
    memory                   = 6144
    # Task role: NPHBudibaseRoleForECSTask
    task_role_arn            = aws_iam_role.budibase_ecs_task.arn
    # Task execution role: NPHBudibaseRoleForECSTaskExecution
    execution_role_arn       = aws_iam_role.budibase_ecs_task_execution.arn

    # Volume 1
    volume {
        name = "budibase-ecs-task-storage"

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
    container_definitions = jsonencode([
        {
            name      = "${local.budibase_container_name}"
            # Essential: Yes
            essential = true
            image     = "${var.BUDIBASE_IMAGE_URL}:latest"
            # Resource allocation limits:
            #   - CPU: 2 vCPU
            cpu       = 2048
            #   - Memory hard limit: 6 GB
            memory    = 6144
            #   - Memory soft limit: 0 GB (default)
            portMappings = [
                {
                    name          = "80-tcp"
                    containerPort = 80
                    appProtocol    = "http"
                },
                {
                    name          = "443-tcp"
                    containerPort = 443
                },
                {
                    name          = "2222-tcp"
                    containerPort = 2222
                },
                {
                    name          = "4369-tcp"
                    containerPort = 4369
                },
                {
                    name          = "5984-tcp"
                    containerPort = 5984
                },
                {
                    name          = "9100-tcp"
                    containerPort = 9100
                }
            ]
            # Add mount point
            mountPoints = [
                {
                    sourceVolume  = "budibase-ecs-task-storage"
                    containerPath = "/data"
                }
            ]
        }
    ])
}

#   - Application Load Balancer: Create a new load balancer
resource "aws_lb" "budibase_alb" {
    name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-lb"
    #   - Load balancer type: Application Load Balancer
    load_balancer_type = "application"
    security_groups = [ aws_security_group.budibase_load_balancer.id ]
    #   - VPC: as above
    subnets = tolist([
        for key in var.SUBNETS_BY_ENV[var.ENVIRONMENT]:
            aws_subnet.public[key].id
    ])

    enable_deletion_protection = var.ENVIRONMENT == "prod"
}

resource "aws_lb_target_group" "budibase_alb_target_group" {
    name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-lb-tg"
    target_type = "ip"
    #   - VPC: as above
    vpc_id = aws_vpc.main.id
    #       - Protocol: HTTP
    protocol = "HTTP"
    #       - Port: 80
    port = 80
    #       - Deregistration delay: 300
    deregistration_delay = 300
    # slow_start = 90 ?
    health_check {
        #       - Health check protocol: HTTP
        protocol = "HTTP"
        #       - Health check path: /
        path = "/"
        # add the success codes "200-299,301-302"
        matcher = "200-299,301-302"
    }
}

#       - Create new listener
resource "aws_lb_listener" "budibase_alb_listener" {
    load_balancer_arn = aws_lb.budibase_alb.arn
    #       - Protocol: HTTP
    protocol          = "HTTP"
    #       - Port: 80
    port              = 80

    default_action {
        type             = "forward"
        target_group_arn = aws_lb_target_group.budibase_alb_target_group.arn
    }
}

# DEFINE FARGATE SERVICE
resource "aws_ecs_service" "budibase_ecs_service" {
    name                = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-ecs-service"
    cluster             = aws_ecs_cluster.budibase_cluster.id
    task_definition     = aws_ecs_task_definition.budibase_ecs_task.arn
    #   - Launch type: FARGATE
    launch_type         = "FARGATE" 
    #   - Platform version: LATEST
    platform_version    = "LATEST"
    #   - Scheduling strategy: Replica
    scheduling_strategy = "REPLICA"
    # Deployment configuration:
    #   - Desired tasks: 1
    desired_count       = 0
    #   - AZ re-balancing: On
    availability_zone_rebalancing = "ENABLED"
    #   - Health check grace period: 0 (disabled)
    # Enable ECS Exec
    enable_execute_command = true

    # Networking:
    network_configuration {
        #   - VPC: select our new VPC
        #   - Subnets: choose our private egress-only subnets
        subnets = tolist([
            for key in var.SUBNETS_BY_ENV[var.ENVIRONMENT]:
                aws_subnet.private[key].id
        ])
        #   - Security Group: choose the FargateService SG
        security_groups = [ aws_security_group.budibase_fargate.id ]
        #   - Public IP: off
        assign_public_ip = false
    }

    #  Load balancing:
    load_balancer {
        #   - Use load balancing: true
        #   - Container and port: our-new-container-name 80:80
        container_name = local.budibase_container_name
        container_port = 80
        target_group_arn = aws_lb_target_group.budibase_alb_target_group.arn
    }
}
