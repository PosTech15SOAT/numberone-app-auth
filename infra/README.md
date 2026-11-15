# Terraform de Auth

Auth provisiona Login, Authorizer, layer, logs, rede privada e o segredo de assinatura JWT. O stack Cloud configura a HTTP API e é o único que declara `aws_lambda_permission`. O Bloco 0 registrou que `auth/prod/terraform.tfstate` ainda não existia na conta de referência. Se outro ambiente tiver o Gateway legado no state de Auth, transfira ou retire seus recursos de API antes de aplicar esta mudança lá.

## Configuração

- Backend S3 em `auth/prod/terraform.tfstate`. Auth usa os outputs de rede de Cloud e os de conexão e security group de Database.
- `TF_STATE_BUCKET` e o trio de credenciais AWS Academy no environment `production`. A região do workflow é `us-east-1`.
- `AUTH_DB_SECRET_ARN` aponta para o segredo `{"username":"numberone_auth_runtime","password":"..."}`. Crie o banco e o papel com o [bootstrap](../db/phase4/bootstrap.psql). A rede permite o acesso ao RDS compartilhado. Os grants PostgreSQL restringem o usuário ao banco de Auth e à leitura das tabelas de identidade.
- `OS_IDENTITY_BASE_URL` é a origem HTTPS privada da OS, sem caminho. A rota privada e a configuração do listener precisam permitir acesso das Lambdas. `OS_IDENTITY_SECRET_ARN` aponta para um segredo distinto com `{"token":"..."}`, compartilhado com a OS.
- `LabRole` precisa confiar em Lambda e permitir CloudWatch Logs, criação das interfaces VPC e leitura dos segredos de runtime. Ambas as funções usam o endpoint privado de Secrets Manager com policy limitada a três ARNs.
- As funções leem os segredos ao iniciar o processo. Após troca de segredo, recicle as duas funções e a implantação da OS de forma coordenada. A rotação da chave HS256 exige novo login.

## Publicação para a Cloud

Após o apply de Auth, obtenha os quatro outputs e grave o JSON abaixo na variável de Actions `AUTH_LAMBDA_ARNS` da Cloud.

| Campo | Output do Terraform de Auth |
| --- | --- |
| `login` | `auth_login_lambda_arn` |
| `login_invoke` | `auth_login_lambda_invoke_arn` |
| `authorizer` | `authorizer_lambda_arn` |
| `authorizer_invoke` | `authorizer_lambda_invoke_arn` |

A Cloud limita a invocação do Login a `POST /auth/login` no stage `$default`. A permissão do Authorizer é específica ao ID da API e ao ID do Authorizer. Payload v2.0, respostas simples e cache desabilitado são parte do contrato. O Authorizer produz 401 por credenciais ausentes ou inválidas e 403 por falta de autorização para a rota. [Lambda Authorizer para HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html)
