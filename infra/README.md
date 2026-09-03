# Infraestrutura - NumberOne Auth

Terraform responsavel por provisionar a frente serverless de autenticacao:

- Lambda de login por CPF.
- Lambda Authorizer.
- API Gateway HTTP API.
- IAM roles e policies.
- CloudWatch Log Groups.
- API Gateway access logs em JSON.
- Lambda Layer de dependencias Python.
- VPC Link para o NLB interno da API.
- Acesso privado da Lambda de login ao RDS e ao Secrets Manager.

## Pre-requisitos

- Terraform >= 1.7.
- AWS CLI autenticado.
- Estados remotos das infraestruturas cloud e database no bucket S3.
- Service `numberone-api-service` implantado no EKS com NLB interno.

O ARN do segredo gerenciado pelo RDS e obtido automaticamente do state
`database/terraform.tfstate`. O segredo JWT e criado por este Terraform quando
nenhum ARN externo e informado.

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
export TF_VAR_lambda_layer_zip_path="$(pwd)/../build/lambda-layer.zip"
```

Os seguintes overrides continuam disponiveis, mas nao sao necessarios no fluxo
padrao:

```bash
export TF_VAR_db_secret_arn="arn:aws:secretsmanager:..."
export TF_VAR_jwt_secret_arn="arn:aws:secretsmanager:..."
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

As integracoes da aplicacao sao privadas. O Terraform le a VPC e as subnets do
estado `cloud/terraform.tfstate`, le o RDS e seu secret do estado
`database/terraform.tfstate`, encontra o NLB pela tag Kubernetes do Service e
cria o caminho `API Gateway -> VPC Link -> NLB`.

A Lambda de login e conectada as subnets privadas por um Security Group
dedicado. Uma regra libera somente esse grupo no PostgreSQL, e um endpoint
privado do Secrets Manager e injetado na Lambda para evitar a necessidade de
NAT Gateway no AWS Academy.

Ordem de provisionamento:

1. aplicar `postech15soat-infra-cloud`;
2. aplicar `postech15soat-infra-database`;
3. implantar `numberone-app-auto-service-api`, criando o NLB interno;
4. aplicar este Terraform, criando as Lambdas, o VPC Link e o API Gateway.

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
