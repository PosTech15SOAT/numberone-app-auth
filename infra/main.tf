locals {
  name_prefix = "${var.project_name}-${var.environment}"
  db_secret_arn = coalesce(
    var.db_secret_arn,
    data.terraform_remote_state.database.outputs.rds_master_secret_arn
  )
  jwt_secret_arn = var.jwt_secret_arn != null ? var.jwt_secret_arn : aws_secretsmanager_secret.jwt[0].arn
  auth_login_subnet_ids = length(var.lambda_subnet_ids) > 0 ? var.lambda_subnet_ids : (
    data.terraform_remote_state.cloud.outputs.private_subnet_ids
  )
  auth_login_security_group_ids = length(var.lambda_security_group_ids) > 0 ? var.lambda_security_group_ids : (
    [aws_security_group.auth_login_lambda.id]
  )
  lambda_layer_arns = concat(
    var.lambda_layer_arns,
    var.lambda_layer_zip_path == null ? [] : [aws_lambda_layer_version.dependencies[0].arn]
  )

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  authenticated_identity_headers = {
    "overwrite:header.X-Authenticated-Subject"     = "$context.authorizer.principalId"
    "overwrite:header.X-Authenticated-Customer-Id" = "$context.authorizer.customerId"
    "overwrite:header.X-Authenticated-Status"      = "$context.authorizer.status"
    "overwrite:header.X-Authenticated-Roles"       = "$context.authorizer.roles"
    "overwrite:header.X-Authenticated-Permissions" = "$context.authorizer.permissions"
    "overwrite:header.X-Correlation-Id"            = "$context.authorizer.correlationId"
  }
}

resource "random_password" "jwt" {
  count = var.jwt_secret_arn == null ? 1 : 0

  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "jwt" {
  count = var.jwt_secret_arn == null ? 1 : 0

  name                    = "${local.name_prefix}/jwt"
  recovery_window_in_days = 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "jwt" {
  count = var.jwt_secret_arn == null ? 1 : 0

  secret_id = aws_secretsmanager_secret.jwt[0].id
  secret_string = jsonencode({
    secret = random_password.jwt[0].result
  })
}

data "archive_file" "auth_login" {
  type        = "zip"
  source_dir  = "${path.module}/.."
  output_path = "${path.module}/auth-login.zip"
  excludes = [
    ".git/*",
    ".github/*",
    ".pytest_cache/*",
    ".terraform/*",
    ".venv/*",
    "build/*",
    "docs/*",
    "infra/.terraform/*",
    "infra/*.zip",
    "tests/*",
  ]
}

data "archive_file" "authorizer" {
  type        = "zip"
  source_dir  = "${path.module}/.."
  output_path = "${path.module}/authorizer.zip"
  excludes = [
    ".git/*",
    ".github/*",
    ".pytest_cache/*",
    ".terraform/*",
    ".venv/*",
    "build/*",
    "docs/*",
    "infra/.terraform/*",
    "infra/*.zip",
    "tests/*",
  ]
}

resource "aws_cloudwatch_log_group" "auth_login" {
  name              = "/aws/lambda/${local.name_prefix}-auth-login"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "authorizer" {
  name              = "/aws/lambda/${local.name_prefix}-authorizer"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.name_prefix}-http-api"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_lambda_layer_version" "dependencies" {
  count = var.lambda_layer_zip_path == null ? 0 : 1

  filename            = var.lambda_layer_zip_path
  layer_name          = "${local.name_prefix}-python-dependencies"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256(var.lambda_layer_zip_path)
}

data "aws_iam_role" "lambda" {
  name = var.lambda_role_name
}

resource "aws_lambda_function" "auth_login" {
  function_name = "${local.name_prefix}-auth-login"
  role          = data.aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "src.auth_login.handler.lambda_handler"

  filename         = data.archive_file.auth_login.output_path
  source_code_hash = data.archive_file.auth_login.output_base64sha256

  layers  = local.lambda_layer_arns
  timeout = 15

  environment {
    variables = {
      DB_SECRET_ARN                = local.db_secret_arn
      DB_NAME                      = var.db_name
      DB_SSL_MODE                  = var.db_ssl_mode
      JWT_SECRET_ARN               = local.jwt_secret_arn
      SECRETS_MANAGER_ENDPOINT_URL = "https://${aws_vpc_endpoint.secretsmanager.dns_entry[0].dns_name}"
      JWT_ISSUER                   = var.jwt_issuer
      JWT_AUDIENCE                 = var.jwt_audience
      JWT_EXPIRATION_SECONDS       = tostring(var.jwt_expiration_seconds)
    }
  }

  vpc_config {
    subnet_ids         = local.auth_login_subnet_ids
    security_group_ids = local.auth_login_security_group_ids
  }

  tags = local.common_tags

  depends_on = [
    aws_cloudwatch_log_group.auth_login
  ]
}

resource "aws_lambda_function" "authorizer" {
  function_name = "${local.name_prefix}-authorizer"
  role          = data.aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "src.authorizer.handler.lambda_handler"

  filename         = data.archive_file.authorizer.output_path
  source_code_hash = data.archive_file.authorizer.output_base64sha256

  layers  = local.lambda_layer_arns
  timeout = 10

  environment {
    variables = {
      JWT_SECRET_ARN = local.jwt_secret_arn
      JWT_ISSUER     = var.jwt_issuer
      JWT_AUDIENCE   = var.jwt_audience
    }
  }

  tags = local.common_tags

  depends_on = [
    aws_cloudwatch_log_group.authorizer
  ]
}

resource "aws_apigatewayv2_api" "this" {
  name          = "${local.name_prefix}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["authorization", "content-type", "x-request-id"]
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_origins = var.allowed_cors_origins
    max_age       = 300
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId          = "$context.requestId"
      ip                 = "$context.identity.sourceIp"
      requestTime        = "$context.requestTime"
      httpMethod         = "$context.httpMethod"
      routeKey           = "$context.routeKey"
      status             = "$context.status"
      protocol           = "$context.protocol"
      responseLength     = "$context.responseLength"
      integrationStatus  = "$context.integrationStatus"
      integrationLatency = "$context.integrationLatency"
      errorMessage       = "$context.error.message"
    })
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "auth_login" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.auth_login.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "application_public_proxy" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = data.aws_lb_listener.application_http.arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.application.id
  payload_format_version = "1.0"
  request_parameters     = local.private_integration_parameters
}

resource "aws_apigatewayv2_integration" "application_health" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = data.aws_lb_listener.application_http.arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.application.id
  payload_format_version = "1.0"

  request_parameters = {
    "overwrite:path" = "$request.path"
  }
}

resource "aws_apigatewayv2_integration" "application_admin_proxy" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = data.aws_lb_listener.application_http.arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.application.id
  payload_format_version = "1.0"
  request_parameters     = local.private_integration_parameters
}

resource "aws_apigatewayv2_authorizer" "lambda" {
  api_id                            = aws_apigatewayv2_api.this.id
  name                              = "${local.name_prefix}-lambda-authorizer"
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = aws_lambda_function.authorizer.invoke_arn
  identity_sources                  = ["$request.header.Authorization"]
  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true
}

resource "aws_apigatewayv2_route" "auth_login" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /auth/login"
  target    = "integrations/${aws_apigatewayv2_integration.auth_login.id}"
}

resource "aws_apigatewayv2_route" "public_proxy" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "ANY /api/public/{proxy+}"
  target             = "integrations/${aws_apigatewayv2_integration.application_public_proxy.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "ANY /api/public/health"
  target    = "integrations/${aws_apigatewayv2_integration.application_health.id}"
}

resource "aws_apigatewayv2_route" "admin_proxy" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "ANY /api/admin/{proxy+}"
  target             = "integrations/${aws_apigatewayv2_integration.application_admin_proxy.id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

resource "aws_lambda_permission" "api_gateway_auth_login" {
  statement_id  = "AllowApiGatewayAuthLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_login.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_authorizer" {
  statement_id  = "AllowApiGatewayAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/authorizers/${aws_apigatewayv2_authorizer.lambda.id}"
}
