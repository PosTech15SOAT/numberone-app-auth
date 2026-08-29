variable "aws_region" {
  description = "Regiao AWS usada para publicar os recursos."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome base usado nos recursos AWS."
  type        = string
  default     = "numberone-auth"
}

variable "environment" {
  description = "Ambiente alvo."
  type        = string
  default     = "hml"
}

variable "cloud_state_bucket" {
  description = "S3 bucket that stores the shared cloud Terraform state."
  type        = string
}

variable "cloud_state_key" {
  description = "S3 key of the shared cloud Terraform state."
  type        = string
  default     = "cloud/terraform.tfstate"
}

variable "application_namespace" {
  description = "Kubernetes namespace used to discover the internal application NLB by tag."
  type        = string
  default     = null
  nullable    = true
}

variable "db_secret_arn" {
  description = "ARN do Secrets Manager com credenciais do PostgreSQL."
  type        = string
}

variable "jwt_secret_arn" {
  description = "ARN do Secrets Manager com segredo JWT."
  type        = string
}

variable "jwt_issuer" {
  description = "Issuer usado nos tokens JWT."
  type        = string
  default     = "numberone-auth"
}

variable "jwt_audience" {
  description = "Audience usada nos tokens JWT."
  type        = string
  default     = "numberone-api"
}

variable "jwt_expiration_seconds" {
  description = "Tempo de expiracao do access token."
  type        = number
  default     = 3600
}

variable "allowed_cors_origins" {
  description = "Origins liberadas no CORS do API Gateway."
  type        = list(string)
  default     = ["*"]
}

variable "lambda_layer_arns" {
  description = "Layers Lambda com dependencias Python, como PyJWT e psycopg."
  type        = list(string)
  default     = []
}

variable "lambda_layer_zip_path" {
  description = "Caminho opcional do zip com dependencias Python para criar um Lambda Layer."
  type        = string
  default     = null
}

variable "log_retention_days" {
  description = "Retencao dos logs CloudWatch das Lambdas e do API Gateway."
  type        = number
  default     = 14
}

variable "lambda_subnet_ids" {
  description = "Subnets privadas para execucao das Lambdas quando acessarem RDS privado."
  type        = list(string)
  default     = []
}

variable "lambda_security_group_ids" {
  description = "Security Groups das Lambdas quando acessarem RDS privado."
  type        = list(string)
  default     = []
}
