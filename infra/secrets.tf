resource "aws_secretsmanager_secret" "rds_connection_info" {
  name        = "${var.PREFIX}-${var.ENVIRONMENT}-rds-secret"
  description = "A secret storing details needed to connect to the ${var.CLIENT} ${var.PROJECT} RDS database in ${var.ENVIRONMENT}."
}

resource "aws_secretsmanager_secret_version" "rds_connection_info_latest" {
  secret_id = aws_secretsmanager_secret.rds_connection_info.id

  secret_string = jsonencode({
    "host" : aws_db_instance.main.address,
    "port" : aws_db_instance.main.port,
    "dbname" : aws_db_instance.main.db_name,
    "user_secret" : aws_db_instance.main.master_user_secret,
  })

  depends_on = [aws_db_instance.main]
}
