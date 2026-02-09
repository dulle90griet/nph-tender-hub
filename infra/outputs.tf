output "lb_url" {
  description = "URL of load balancer"
  value       = "http://${aws_lb.budibase_alb.dns_name}/"
}

output "budibase_ecs_list_tasks_command" {
  description = "Command to get list of Budibase TASK ARNs"
  value       = "aws ecs list-tasks --cluster ${aws_ecs_cluster.budibase_cluster.name} --service ${aws_ecs_service.budibase_ecs_service.name}"
}

output "budibase_ecs_exec_command" {
  description = "Command to connect to ECS Exec shell on desired Budibase container instance"
  value       = "aws ecs execute-command --region ${var.AWS_REGION} --cluster ${aws_ecs_cluster.budibase_cluster.name} --task [TASK ID FROM LIST-TASKS] --container ${var.PREFIX}-budibase-container --interactive --command '/bin/sh'"
}
