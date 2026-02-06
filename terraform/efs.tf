resource "aws_efs_file_system" "budibase_fargate_data" {
    creation_token = "${var.PREFIX}-budibase-fargate-efs"

    # Enable encryption of data at rest using Fargate Managed Storage KMS key
    # Use our Fargate Managed Storage KMS key
    encrypted = true
    kms_key_id = aws_kms_key.fargate_managed_storage.arn

    lifecycle_policy {
        transition_to_archive = "AFTER_90_DAYS"
    }
    lifecycle_policy {
        transition_to_ia = "AFTER_30_DAYS"
    }
    lifecycle_policy {
        transition_to_primary_storage_class = "AFTER_1_ACCESS"
    }
    performance_mode = "generalPurpose" # DOUBLE-CHECK THIS
    throughput_mode = "elastic" # DOUBLE-CHECK THIS
    protection {
        replication_overwrite = "ENABLED" # DOUBLE-CHECK THIS
    }

    tags = {
        Name = "${var.PREFIX}_budibase_data"
    }
}

# File system policy: Enforce in-transit encryption for all clients
resource "aws_efs_file_system_policy" "budibase_efs_policy" {
    file_system_id = aws_efs_file_system.budibase_fargate_data.id

    # enforce TLS 1.2 encryption for all clients
    policy = jsonencode({
        Version = "2012-10-17"
        Id      = "EnforceInTransitEncryption"
        Statement = [
            {
                Sid    = "EnforceInTransitEncryption"
                Effect = "Allow"
                Principal = {
                    AWS = "*"
                }
                Action = [
                    "elasticfilesystem:ClientMount",
                    "elasticfilesystem:ClientWrite",
                    "elasticfilesystem:ClientRootAccess"
                ]
                Resource = "${aws_efs_file_system.budibase_fargate_data.arn}"
                Condition = {
                    Bool = {
                        "aws:SecureTransport" = true
                    }
                }
            }
        ]
    })
}


resource "aws_efs_backup_policy" "budibase_fargate_backup_policy" {
    file_system_id = aws_efs_file_system.budibase_fargate_data.id

    backup_policy {
        status = "ENABLED"
    }
}

# Network access:
# Choose the new VPC we've created
# Choose the private subnets and use the EFS Security Group for each
locals {
  efs_mount_targets = {
    "dev"   = tolist(["a", "b", "c"])
    "stage" = tolist(["d", "e", "f"])
    "prod"  = tolist(["g", "h", "i"])
  }
}

resource "aws_efs_mount_target" "budibase_fargate_mount_target" {
    for_each = { for key in local.efs_mount_targets[var.ENVIRONMENT]: key => null }

    file_system_id  = aws_efs_file_system.budibase_fargate_data.id
    subnet_id       = aws_subnet.private[each.key].id
    security_groups = [ aws_security_group.budibase_efs.id ] 
    ip_address_type = "IPV4_ONLY"
}

resource "aws_efs_access_point" "budibase_fargate_access_point" {
    file_system_id = aws_efs_file_system.budibase_fargate_data.id

    posix_user {
        uid = "0"
        gid = "0"
        # secondary_gids = None
    }

    root_directory {
        path = "/data"

        creation_info {
            owner_uid = "0"
            owner_gid = "0"
            permissions = "0755"
        }
    }

    tags = {
        Name = "${var.PREFIX}_budibase_access_point"
    }
}
 