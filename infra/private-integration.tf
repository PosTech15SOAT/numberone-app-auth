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

resource "aws_apigatewayv2_vpc_link" "application" {
  name               = "${local.name_prefix}-application"
  subnet_ids         = data.terraform_remote_state.cloud.outputs.private_subnet_ids
  security_group_ids = [aws_security_group.api_gateway_vpc_link.id]

  tags = local.common_tags
}
