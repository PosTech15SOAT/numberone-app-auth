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
  default     = "prod"

  validation {
    condition     = var.environment == "prod"
    error_message = "O unico ambiente permitido e prod."
  }
}

variable "cloud_state_bucket" {
  description = "S3 bucket that stores the shared cloud Terraform state."
  type        = string
}

variable "lambda_role_name" {
  description = "Existing AWS Academy IAM role used by the Lambda functions."
  type        = string
  default     = "LabRole"
}

variable "cloud_state_key" {
  description = "S3 key of the shared cloud Terraform state."
  type        = string
  default     = "cloud/terraform.tfstate"
}

variable "database_state_bucket" {
  description = "S3 bucket that stores the database Terraform state. Uses cloud_state_bucket when omitted."
  type        = string
  default     = null
  nullable    = true
}

variable "database_state_key" {
  description = "S3 key of the shared database Terraform state."
  type        = string
  default     = "database/terraform.tfstate"
}

variable "jwt_secret_arn" {
  description = "Optional existing JWT secret ARN. When omitted, this stack creates and manages a secret."
  type        = string
  default     = null
  nullable    = true
  sensitive   = true
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
  description = "Retencao dos logs CloudWatch das Lambdas."
  type        = number
  default     = 14
}

variable "auth_db_secret_arn" {
  description = "ARN do secret do papel de runtime do banco exclusivo de Auth."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^arn:[^:]+:secretsmanager:", var.auth_db_secret_arn))
    error_message = "Informe o ARN do secret de runtime de Auth."
  }
}

variable "os_identity_base_url" {
  description = "Origem HTTPS privada que serve a consulta de identidade da OS."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^https://[a-zA-Z0-9.-]+/?$", var.os_identity_base_url))
    error_message = "Informe a origem HTTPS privada da OS, sem caminho."
  }
}

variable "os_identity_secret_arn" {
  description = "ARN do secret compartilhado para consultar a identidade na OS."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^arn:[^:]+:secretsmanager:", var.os_identity_secret_arn))
    error_message = "Informe o ARN do secret da integração de identidade da OS."
  }
}
