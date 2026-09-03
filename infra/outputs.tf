output "api_gateway_url" {
  description = "URL publica do API Gateway."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "auth_login_lambda_name" {
  description = "Nome da Lambda de login por CPF."
  value       = aws_lambda_function.auth_login.function_name
}

output "authorizer_lambda_name" {
  description = "Nome da Lambda Authorizer."
  value       = aws_lambda_function.authorizer.function_name
}

output "vpc_link_id" {
  description = "Identificador do VPC Link usado pela integracao privada."
  value       = aws_apigatewayv2_vpc_link.application.id
}

output "application_load_balancer_arn" {
  description = "ARN do NLB interno descoberto pela tag do Service Kubernetes."
  value       = data.aws_lb.application.arn
}

output "db_secret_arn" {
  description = "RDS managed secret consumed by the login Lambda."
  value       = local.db_secret_arn
  sensitive   = true
}

output "jwt_secret_arn" {
  description = "JWT signing secret consumed by the login and authorizer Lambdas."
  value       = local.jwt_secret_arn
  sensitive   = true
}
