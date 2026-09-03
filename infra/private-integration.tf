locals {
  application_namespace = var.application_namespace != null ? var.application_namespace : (
    var.environment == "prod" ? "numberone-production" : "numberone-homolog"
  )
  private_integration_parameters = merge(
    local.authenticated_identity_headers,
    { "overwrite:path" = "$request.path" }
  )
}

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

data "aws_lb" "application" {
  tags = {
    "kubernetes.io/service-name" = "${local.application_namespace}/numberone-api-service"
  }
}

data "aws_lb_listener" "application_http" {
  load_balancer_arn = data.aws_lb.application.arn
  port              = 80
}

resource "aws_security_group" "api_gateway_vpc_link" {
  name        = "${local.name_prefix}-apigw-vpc-link"
  description = "API Gateway VPC Link access to the internal application NLB"
  vpc_id      = data.terraform_remote_state.cloud.outputs.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "auth_login_lambda" {
  name        = "${local.name_prefix}-auth-login-lambda"
  description = "Network access for the auth login Lambda"
  vpc_id      = data.terraform_remote_state.cloud.outputs.vpc_id

  tags = local.common_tags
}

resource "aws_vpc_security_group_egress_rule" "auth_login_lambda" {
  security_group_id = aws_security_group.auth_login_lambda.id
  description       = "Allow the auth login Lambda to reach RDS and AWS private endpoints"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_auth_login" {
  security_group_id            = data.terraform_remote_state.database.outputs.rds_security_group_id
  referenced_security_group_id = aws_security_group.auth_login_lambda.id
  description                  = "Allow PostgreSQL from the auth login Lambda"
  from_port                    = data.terraform_remote_state.database.outputs.rds_port
  to_port                      = data.terraform_remote_state.database.outputs.rds_port
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "secretsmanager_endpoint" {
  name        = "${local.name_prefix}-secretsmanager-endpoint"
  description = "Private Secrets Manager access for the auth login Lambda"
  vpc_id      = data.terraform_remote_state.cloud.outputs.vpc_id

  tags = local.common_tags
}

resource "aws_vpc_security_group_ingress_rule" "secretsmanager_from_auth_login" {
  security_group_id            = aws_security_group.secretsmanager_endpoint.id
  referenced_security_group_id = aws_security_group.auth_login_lambda.id
  description                  = "Allow HTTPS from the auth login Lambda"
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "secretsmanager_endpoint" {
  security_group_id = aws_security_group.secretsmanager_endpoint.id
  description       = "Allow endpoint response traffic"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = data.terraform_remote_state.cloud.outputs.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.terraform_remote_state.cloud.outputs.private_subnet_ids
  security_group_ids  = [aws_security_group.secretsmanager_endpoint.id]
  private_dns_enabled = false

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-secretsmanager"
  })
}

resource "aws_apigatewayv2_vpc_link" "application" {
  name               = "${local.name_prefix}-application"
  subnet_ids         = data.terraform_remote_state.cloud.outputs.private_subnet_ids
  security_group_ids = [aws_security_group.api_gateway_vpc_link.id]

  tags = local.common_tags
}
