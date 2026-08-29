# Infraestrutura - NumberOne Auth

Terraform responsavel por provisionar a frente serverless de autenticacao:

- Lambda de login por CPF.
- Lambda Authorizer.
- API Gateway HTTP API.
- IAM roles e policies.
- CloudWatch Log Groups.
- API Gateway access logs em JSON.
- Lambda Layer de dependencias Python.

## Pre-requisitos

- Terraform >= 1.7.
- AWS CLI autenticado.
- Segredo do banco no AWS Secrets Manager.
- Segredo JWT no AWS Secrets Manager.
- Estado remoto da infraestrutura cloud no bucket S3.
- Service `numberone-api-service` implantado no EKS com NLB interno.
- Subnets e Security Groups quando o RDS estiver privado.

## Build do Lambda Layer

Execute na raiz do repositorio:

```bash
./scripts/build-lambda-layer.sh
```

O script gera:

```text
build/lambda-layer.zip
```

## Variaveis obrigatorias

```bash
export TF_VAR_cloud_state_bucket="bucket-de-estado-do-projeto"
export TF_VAR_db_secret_arn="arn:aws:secretsmanager:..."
export TF_VAR_jwt_secret_arn="arn:aws:secretsmanager:..."
export TF_VAR_lambda_layer_zip_path="$(pwd)/../build/lambda-layer.zip"
```

Quando o RDS estiver privado:

```bash
export TF_VAR_lambda_subnet_ids='["subnet-1","subnet-2"]'
export TF_VAR_lambda_security_group_ids='["sg-1"]'
```

## Comandos

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Rotas criadas

| Rota | Autorizacao | Destino |
| --- | --- | --- |
| `POST /auth/login` | Publica | Lambda auth-login |
| `ANY /api/public/health` | Publica | Aplicacao principal |
| `ANY /api/public/{proxy+}` | Lambda Authorizer | Aplicacao principal |
| `ANY /api/admin/{proxy+}` | Lambda Authorizer | Aplicacao principal |

As integracoes da aplicacao sao privadas. O Terraform le `vpc_id` e
`private_subnet_ids` do estado `cloud/terraform.tfstate`, encontra o NLB pela
tag Kubernetes do Service e cria o caminho `API Gateway -> VPC Link -> NLB`.

Ordem de provisionamento:

1. aplicar `postech15soat-infra-cloud`;
2. implantar `numberone-app-auto-service-api`, criando o NLB interno;
3. aplicar este Terraform, criando o VPC Link e o API Gateway.

Os workflows usam estados separados em `auth/hml/terraform.tfstate` e
`auth/prod/terraform.tfstate`, enquanto ambos consomem o estado cloud
compartilhado em `cloud/terraform.tfstate`.

## Headers enviados para a aplicacao principal

Nas rotas protegidas, o API Gateway encaminha:

- `X-Authenticated-Subject`
- `X-Authenticated-Customer-Id`
- `X-Authenticated-Status`
- `X-Authenticated-Roles`
- `X-Authenticated-Permissions`
- `X-Correlation-Id`
