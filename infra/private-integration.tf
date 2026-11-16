data "terraform_remote_state" "cloud" {
  backend = "s3"

  config = {
    bucket = var.cloud_state_bucket
    key    = var.cloud_state_key
    region = var.aws_region
  }
}

data "terraform_remote_state" "database" {
  backend = "s3"

  config = {
    bucket = coalesce(var.database_state_bucket, var.cloud_state_bucket)
    key    = var.database_state_key
    region = var.aws_region
  }
}

locals {
  auth_security_group_ids = [
    aws_security_group.auth_login_lambda.id,
    data.terraform_remote_state.cloud.outputs.os_identity_ingress.client_security_group_id,
  ]
}

resource "aws_security_group" "auth_login_lambda" {
  name        = "${local.name_prefix}-auth-login-lambda"
  description = "Network access for Auth functions"
  vpc_id      = data.terraform_remote_state.cloud.outputs.vpc_id

  tags = local.common_tags
}

resource "aws_vpc_security_group_egress_rule" "auth_to_rds" {
  security_group_id            = aws_security_group.auth_login_lambda.id
  referenced_security_group_id = data.terraform_remote_state.database.outputs.rds_security_group_id
  from_port                    = data.terraform_remote_state.database.outputs.rds_port
  to_port                      = data.terraform_remote_state.database.outputs.rds_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_auth_login" {
  security_group_id            = data.terraform_remote_state.database.outputs.rds_security_group_id
  referenced_security_group_id = aws_security_group.auth_login_lambda.id
  description                  = "Allow PostgreSQL from Auth functions"
  from_port                    = data.terraform_remote_state.database.outputs.rds_port
  to_port                      = data.terraform_remote_state.database.outputs.rds_port
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "secretsmanager_endpoint" {
  name        = "${local.name_prefix}-secretsmanager-endpoint"
  description = "Private Secrets Manager access for Auth functions"
  vpc_id      = data.terraform_remote_state.cloud.outputs.vpc_id

  tags = local.common_tags
}

resource "aws_vpc_security_group_ingress_rule" "secretsmanager_from_auth_login" {
  security_group_id            = aws_security_group.secretsmanager_endpoint.id
  referenced_security_group_id = aws_security_group.auth_login_lambda.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = data.terraform_remote_state.cloud.outputs.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.terraform_remote_state.cloud.outputs.private_subnet_ids
  security_group_ids  = [aws_security_group.secretsmanager_endpoint.id]
  private_dns_enabled = false

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = "secretsmanager:GetSecretValue"
      Resource  = [var.auth_db_secret_arn, var.os_identity_secret_arn, local.jwt_secret_arn]
    }]
  })

  tags = local.common_tags
}
