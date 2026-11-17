locals {
  auth_db_secret_arn = data.terraform_remote_state.database.outputs.application_secret_arns["auth"]
  name_prefix        = "${var.project_name}-${var.environment}"
  jwt_secret_arn     = var.jwt_secret_arn != null ? var.jwt_secret_arn : aws_secretsmanager_secret.jwt[0].arn
  lambda_layer_arns = concat(
    var.lambda_layer_arns,
    var.lambda_layer_zip_path == null ? [] : [aws_lambda_layer_version.dependencies[0].arn]
  )

  runtime_environment = {
    DB_SECRET_ARN                = local.auth_db_secret_arn
    DB_HOST                      = data.terraform_remote_state.database.outputs.rds_endpoint
    DB_PORT                      = tostring(data.terraform_remote_state.database.outputs.rds_port)
    DB_NAME                      = "numberone_auth"
    DB_RUNTIME_USERNAME          = "numberone_auth_runtime"
    DB_SSL_MODE                  = "require"
    JWT_SECRET_ARN               = local.jwt_secret_arn
    SECRETS_MANAGER_ENDPOINT_URL = "https://${aws_vpc_endpoint.secretsmanager.dns_entry[0].dns_name}"
    JWT_ISSUER                   = var.jwt_issuer
    JWT_AUDIENCE                 = var.jwt_audience
    JWT_EXPIRATION_SECONDS       = tostring(var.jwt_expiration_seconds)
    OS_IDENTITY_BASE_URL         = data.terraform_remote_state.cloud.outputs.os_identity_ingress.base_url
  }

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
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

data "archive_file" "functions" {
  type        = "zip"
  output_path = "${path.module}/auth-functions.zip"

  dynamic "source" {
    for_each = fileset("${path.module}/..", "src/**/*.py")
    content {
      filename = source.value
      content  = file("${path.module}/../${source.value}")
    }
  }
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

  filename         = data.archive_file.functions.output_path
  source_code_hash = data.archive_file.functions.output_base64sha256

  layers      = local.lambda_layer_arns
  timeout     = 15
  memory_size = 512

  environment {
    variables = local.runtime_environment
  }

  vpc_config {
    subnet_ids         = data.terraform_remote_state.cloud.outputs.private_subnet_ids
    security_group_ids = local.auth_security_group_ids
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

  filename         = data.archive_file.functions.output_path
  source_code_hash = data.archive_file.functions.output_base64sha256

  layers  = local.lambda_layer_arns
  timeout = 10

  environment {
    variables = local.runtime_environment
  }

  vpc_config {
    subnet_ids         = data.terraform_remote_state.cloud.outputs.private_subnet_ids
    security_group_ids = local.auth_security_group_ids
  }

  tags = local.common_tags

  depends_on = [
    aws_cloudwatch_log_group.authorizer
  ]
}
