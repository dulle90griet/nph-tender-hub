output "lb_url" {
  description = "URL of load balancer"
  value       = "http://${aws_lb.budibase_alb.dns_name}/"
}

output "budibase_ecs_cluster_name" {
  description = "The name of the Budibase ECS/Fargate cluster"
  value       = aws_ecs_cluster.budibase_cluster.name
}

output "budibase_ecs_service_name" {
  description = "The name of the Budibase ECS/Fargate service"
  value       = aws_ecs_service.budibase_ecs_service.name
}

output "budibase_ecs_list_tasks_command" {
  description = "Command to get list of Budibase TASK ARNs"
  value       = "aws ecs list-tasks --cluster ${aws_ecs_cluster.budibase_cluster.name} --service ${aws_ecs_service.budibase_ecs_service.name}"
}

output "budibase_ecs_exec_command" {
  description = "Command to connect to ECS Exec shell on desired Budibase container instance"
  value       = "aws ecs execute-command --region ${var.AWS_REGION} --cluster ${aws_ecs_cluster.budibase_cluster.name} --task [TASK ID FROM LIST-TASKS] --container ${var.PREFIX}-budibase-container --interactive --command '/bin/sh'"
}

output "lambda_create_service_name" {
  description = "The name of the create_service Lambda function"
  value       = aws_lambda_function.create_instance_lambda.function_name
}

output "lambda_destroy_service_name" {
  description = "The name of the destroy_service Lambda function"
  value       = aws_lambda_function.destroy_instance_lambda.function_name
}