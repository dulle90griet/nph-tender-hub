# Create symmetric, single-region, encrypt-and-decrypt KMS Key for managed storage used by Fargate, giving `Allow administration of the key`, `Allow use of the key` and `Allow attachment of persistent resources` permissions to the dev IAM user. (And to AWSServiceRoleForECS?)

resource "aws_kms_key" "fargate_managed_storage" {
    description             = "KMS key used for encrypting and decrypting managed storage used by Fargate for ${var.CLIENT} ${var.PROJECT}."
    enable_key_rotation     = true
    deletion_window_in_days = 30
    policy                  = data.aws_iam_policy_document.kms_key_for_fargate.json

    tags = {
      Name = "${var.PREFIX}-key-for-fargate-managed"
    }
}

# Create symmetric, single-region, encrypt-and-decrypt KMS Key for ephemeral storage used by Fargate, giving `Allow administration of the key`, `Allow use of the key` and `Allow attachment of persistent resources` permissions to the dev IAM user. (And to AWSServiceRoleForECS?)

resource "aws_kms_key" "fargate_ephemeral_storage" {
    description             = "KMS key used for encrypting and decrypting ephemeral storage used by Fargate for ${var.CLIENT} ${var.PROJECT}."
    enable_key_rotation     = true
    deletion_window_in_days = 30
    policy                  = data.aws_iam_policy_document.kms_key_for_fargate.json

    tags = {
      Name = "${var.PREFIX}-key-for-fargate-ephemeral"
    }
}

data "aws_iam_policy_document" "kms_key_for_fargate" {
    statement {
        sid       = "Enable IAM User Permissions"
        effect    = "Allow"
        principals {
            type        = "AWS"
            identifiers = [ "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" ]
        }
        actions   = [ "kms:*" ]
        resources = [ "*" ]
    }

    statement {
        sid    = "AllowUserAdministrationOfKey"
        effect = "Allow"
        principals {
            type        = "AWS"
            identifiers = [ "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/${var.IAM_USER}" ] # Can I get user name from the caller identity or does it need to be a .tfenv var?
        }
        actions = [
            "kms:ReplicateKey",
            "kms:Create*",
            "kms:Describe*",
            "kms:Enable*",
            "kms:List*",
            "kms:Put*",
            "kms:Update*",
            "kms:Revoke*",
            "kms:Disable*",
            "kms:Get*",
            "kms:Delete*",
            "kms:ScheduleKeyDeletion",
            "kms:CancelKeyDeletion"
        ]
        resources = [ "*" ]
    }

    statement {
        sid    = "AllowUserToUseKey"
        effect = "Allow"
        principals {
            type        = "AWS"
            identifiers = [ "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/${var.IAM_USER}" ] # Can I get user name from the caller identity or does it need to be a .tfenv var?
        }
        actions = [
            "kms:DescribeKey",
            "kms:Encrypt",
            "kms:Decrypt",
            "kms:ReEncrypt*",
            "kms:GenerateDataKey",
            "kms:GenerateDataKeyWithoutPlaintext"
        ]
        resources = [ "*" ]
    }

    statement {
        sid    = "AllowUserToAttachPersistentResources"
        effect = "Allow"
        principals {
            type        = "AWS"
            identifiers = [ "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/${var.IAM_USER}" ] # Can I get user name from the caller identity or does it need to be a .tfenv var?
        }
        actions = [
            "kms:CreateGrant",
            "kms:ListGrants",
            "kms:RevokeGrants"
        ]
        resources = [ "*" ]
        condition {
            test     = "Bool"
            variable = "kms:GrantIsForAWSResource"
            values   = [ true ]
        }
    }

    statement {
        sid       = "AllowFargateToGenerateKey"
        effect    = "Allow"
        principals {
            type        = "Service"
            identifiers = [ "fargate.amazonaws.com" ]
        }
        actions   = [ "kms:GenerateDataKeyWithoutPlaintext" ]
        resources = [ "*" ]
        condition {
            test     = "StringEquals"
            variable = "kms:EncryptionContext:aws:ecs:clusterAccount"
            values   = [ "${data.aws_caller_identity.current.account_id}" ]
        }
        condition {
            test     = "StringEquals"
            variable = "kms:EncryptionContext:aws:ecs:clusterName"
            values   = [ "${var.BUDIBASE_CLUSTER_NAME}" ]
        }

    }

    statement {
        sid       = "AllowFargateToCreateGrant"
        effect    = "Allow"
        principals {
            type        = "Service"
            identifiers = [ "fargate.amazonaws.com" ]
        }
        actions   = [ "kms:CreateGrant" ]
        resources = [ "*" ]
        condition {
            test     = "StringEquals"
            variable = "kms:EncryptionContext:aws:ecs:clusterAccount"
            values   = [ "${data.aws_caller_identity.current.account_id}" ]
        }
        condition {
            test     = "StringEquals"
            variable = "kms:EncryptionContext:aws:ecs:clusterName"
            values   = [ "${var.BUDIBASE_CLUSTER_NAME}" ]
        }
        condition {
            test     = "ForAllValues:StringEquals"
            variable = "kms:GrantOperations"
            values   = [ "Decrypt" ]
        }
    }

    statement {
        sid    = "AllowEFSToUseKey"
        effect = "Allow"
        principals {
            type        = "Service"
            identifiers = [ "fargate.amazonaws.com" ]
        }
        actions = [
            "kms:Decrypt",
            "kms:GenerateDataKeyWithoutPlaintext",
            "kms:DescribeKey",
            "kms:CreateGrant"
        ]
        resources = [ "*" ]
        condition {
            test     = "StringEquals"
            variable = "kms:ViaService"
            values   = [ "elasticfilesystem.${var.AWS_REGION}.amazonaws.com" ]
        }
        condition {
            test     = "StringEquals"
            variable = "kms:CallerAccount"
            values   = [ "${data.aws_caller_identity.current.account_id}" ]
        }
    }
}
