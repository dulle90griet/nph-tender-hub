# Create symmetric, single-region, encrypt-and-decrypt KMS Key for managed storage used by Fargate, giving `Allow administration of the key`, `Allow use of the key` and `Allow attachment of persistent resources` permissions to the nph_developer user. (And to AWSServiceRoleForECS?)

resource "aws_kms_key" "fargate_managed_storage" {
    description = "KMS key used for encrypting and decrypting managed storage used by Fargate for ${var.CLIENT} ${var.PROJECT}."
    enable_key_rotation = true
    deletion_window_in_days = 30
    policy = aws_iam_policy_document.kms_key_for_fargate.policy

    tags = {
      Name = "${var.PREFIX}-key-for-fargate-managed"
    }
}

# Create symmetric, single-region, encrypt-and-decrypt KMS Key for ephemeral storage used by Fargate, giving `Allow administration of the key`, `Allow use of the key` and `Allow attachment of persistent resources` permissions to the nph_developer user. (And to AWSServiceRoleForECS?)

resource "aws_kms_key" "fargate_ephemeral_storage" {
    description = "KMS key used for encrypting and decrypting ephemeral storage used by Fargate for ${var.CLIENT} ${var.PROJECT}."
    enable_key_rotation = true
    deletion_window_in_days = 30
    policy = aws_iam_policy_document.kms_key_for_fargate.policy

    tags = {
      Name = "${var.PREFIX}-key-for-fargate-ephemeral"
    }
}

resource "aws_iam_policy_document" "kms_key_for_fargate" {
    statement {
        sid = "Enable IAM User Permissions"
        effect = "Allow"
        principals = [ "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" ]
        actions = [ "kms:*" ]
        resources = [ "*" ]
    }
    statement {
        sid = "Allow administration of the key"
        effect = "Allow"
        principals = [ "arn:aws:iam:$${data.aws_caller_identity.current.account_id}:user/nph_developer" ] # Can I get user name from the caller identity or does it need to be a .tfenv var?
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
        sid = "Allow use of the key"
        effect = "Allow"
        principals = [ "arn:aws:iam:$${data.aws_caller_identity.current.account_id}:user/nph_developer" ] # Can I get user name from the caller identity or does it need to be a .tfenv var?
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
        sid = "Allow attachment of persistent resources"
        effect = "Allow"
        principals = [ "arn:aws:iam:$${data.aws_caller_identity.current.account_id}:user/nph_developer" ] # Can I get user name from the caller identity or does it need to be a .tfenv var?
        resources = "*"
    }
}