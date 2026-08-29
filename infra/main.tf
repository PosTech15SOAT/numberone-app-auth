locals {
  name_prefix = "${var.project_name}-${var.environment}"
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

resource "aws_iam_role" "lambda" {
  name = "${local.name_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count = length(var.lambda_subnet_ids) > 0 ? 1 : 0

  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_secrets" {
  name = "${local.name_prefix}-lambda-secrets"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.db_secret_arn,
          var.jwt_secret_arn
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "auth_login" {
  function_name = "${local.name_prefix}-auth-login"
  role          = aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "src.auth_login.handler.lambda_handler"

  filename         = data.archive_file.auth_login.output_path
  source_code_hash = data.archive_file.auth_login.output_base64sha256

  layers  = local.lambda_layer_arns
  timeout = 15

  environment {
    variables = {
      DB_SECRET_ARN          = var.db_secret_arn
      JWT_SECRET_ARN         = var.jwt_secret_arn
      JWT_ISSUER             = var.jwt_issuer
      JWT_AUDIENCE           = var.jwt_audience
      JWT_EXPIRATION_SECONDS = tostring(var.jwt_expiration_seconds)
    }
  }

  dynamic "vpc_config" {
    for_each = length(var.lambda_subnet_ids) > 0 ? [1] : []
    content {
      subnet_ids         = var.lambda_subnet_ids
      security_group_ids = var.lambda_security_group_ids
    }
  }

  tags = local.common_tags

  depends_on = [
    aws_cloudwatch_log_group.auth_login
  ]
}

resource "aws_lambda_function" "authorizer" {
  function_name = "${local.name_prefix}-authorizer"
  role          = aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "src.authorizer.handler.lambda_handler"

  filename         = data.archive_file.authorizer.output_path
  source_code_hash = data.archive_file.authorizer.output_base64sha256

  layers  = local.lambda_layer_arns
  timeout = 10

  environment {
    variables = {
      JWT_SECRET_ARN = var.jwt_secret_arn
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
