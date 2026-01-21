output "lb_url" {
    description = "URL of load balancer"
    value       = "http://${aws_lb.budibase_alb.dns_name}/"
}
