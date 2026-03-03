data "aws_cloudwatch_log_group" "budibase_ecs_task" {
  # Log group must be created separately to ensure TF independence
  name="/ecs/${var.PREFIX}-${var.ENVIRONMENT}-budibase-task-family"
}
