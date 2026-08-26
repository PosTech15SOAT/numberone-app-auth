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
