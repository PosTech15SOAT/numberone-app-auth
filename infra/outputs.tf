output "auth_login_lambda_arn" {
  description = "ARN da função de Login para a permissão de invocação na Cloud."
  value       = aws_lambda_function.auth_login.arn
}

output "auth_login_lambda_invoke_arn" {
  description = "URI AWS_PROXY da função de Login para a Cloud."
  value       = aws_lambda_function.auth_login.invoke_arn
}

output "authorizer_lambda_arn" {
  description = "ARN da função de Authorizer para a permissão de invocação na Cloud."
  value       = aws_lambda_function.authorizer.arn
}

output "authorizer_lambda_invoke_arn" {
  description = "URI do Lambda Authorizer para a Cloud."
  value       = aws_lambda_function.authorizer.invoke_arn
}
