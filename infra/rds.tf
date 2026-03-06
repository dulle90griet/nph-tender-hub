resource "aws_db_parameter_group" "main" {
  name   = "${var.PREFIX}-${var.ENVIRONMENT}-db-parameters-main"
  family = "postgres17"

  parameter {
    name  = "application_name"
    value = "${var.PREFIX}-${var.PROJECT}-${var.ENVIRONMENT}"
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }
}

resource "aws_db_subnet_group" "main" {
  description = "DB subnet group for ${var.CLIENT} ${var.PROJECT}"
  name        = "${var.PREFIX}-${var.ENVIRONMENT}-db-subnet-group"

  subnet_ids = tolist([
    for key in var.SUBNETS_BY_ENV[var.ENVIRONMENT] :
    aws_subnet.private[key].id
  ])
}

resource "aws_db_instance" "main" {
  identifier = "${var.PREFIX}-${var.ENVIRONMENT}-db"
  db_name    = "${var.PREFIX}_${var.ENVIRONMENT}"

  instance_class = "db.t4g.micro"
  engine         = "postgres"
  engine_version = "17.9"

  storage_type      = "gp2"
  allocated_storage = 20
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds_encryption_at_rest.arn

  username                      = "${var.PREFIX}_user"
  manage_master_user_password   = true
  master_user_secret_kms_key_id = aws_kms_key.rds_master_user_secret.arn

  parameter_group_name      = aws_db_parameter_group.main.name
  skip_final_snapshot       = var.ENVIRONMENT != "prod"
  final_snapshot_identifier = "${var.PREFIX}-${var.ENVIRONMENT}-db-final-snapshot-${replace(timestamp(), ":", "-")}"
  copy_tags_to_snapshot     = true
  maintenance_window        = "Sun:03:00-Sun:06:00"

  backup_retention_period = 14
  backup_window           = "07:20-08:50"

  # monitoring_interval ?
  # monitoring_role_arn ?
  # performance_insights_enabled ?
  # performance_insights_retention_period ?

  multi_az = false
  # availability_zone ?
  publicly_accessible  = false
  db_subnet_group_name = aws_db_subnet_group.main.name

  apply_immediately = false

  lifecycle {
    ignore_changes = [
      final_snapshot_identifier,
    ]
  }
}
