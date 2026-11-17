# Terraform de Auth

Auth provisiona Login, Authorizer, layer, logs, rede privada e o segredo de assinatura JWT. O stack Cloud configura a HTTP API e é o único que declara `aws_lambda_permission`. O Bloco 0 registrou que `auth/prod/terraform.tfstate` ainda não existia na conta de referência. Se outro ambiente tiver o Gateway legado no state de Auth, transfira ou retire seus recursos de API antes de aplicar esta mudança lá.

## Configuração

- Backend S3 em `auth/prod/terraform.tfstate`. Auth usa os outputs de rede de Cloud e os de conexão e security group de Database.
- `TF_STATE_BUCKET` e o trio de credenciais AWS Academy no environment `production`. A região do workflow é `us-east-1`.
- Database cria o Secret `numberone-auth-database` e publica seu ARN em `application_secret_arns["auth"]`. Auth o injeta como `DB_SECRET_ARN`, sem variável manual. O conteúdo esperado é `{"username":"numberone_auth_runtime","password":"..."}`. O [bootstrap](../db/phase4/bootstrap.psql) cria o banco e o papel; a senha desse papel precisa corresponder ao Secret. Os grants PostgreSQL restringem o usuário ao banco de Auth e à leitura das tabelas de identidade.
- Cloud publica `os_identity_ingress.base_url` como origem HTTP privada, sem caminho, e `os_identity_ingress.client_security_group_id` como SG cliente da integração. Auth consome ambos diretamente do remote state. Não há token, CA privada ou Secret de identidade entre serviços.
- A origem aceita pelo cliente é `http://` com DNS de balanceador AWS `internal-…` (formatos `internal-….<região>.elb.amazonaws.com` ou `internal-….elb.<região>.amazonaws.com`, incluindo partição China), ou IPv4 RFC1918, com porta opcional. Outras origens, caminhos, credenciais e parâmetros são recusados. O destino deve ser provisionado pela Cloud; DNS público arbitrário e proxies de ambiente não são usados.
- O SG cliente publicado pela Cloud precisa permitir o tráfego para a porta HTTP do listener privado, com ingresso correspondente no destino. A rota `POST /internal/auth/customer-identity` deve permanecer fora da API pública. A proteção dessa integração é de rede.
- `LabRole` precisa confiar em Lambda e permitir CloudWatch Logs, criação das interfaces VPC e leitura dos segredos de banco e JWT. Ambas as funções usam o endpoint privado de Secrets Manager com policy limitada a esses dois ARNs. As regras TCP/443 do endpoint são preservadas; HTTP vale apenas para Auth → OS.
- As funções leem os segredos ao iniciar o processo. Após troca de segredo, recicle as duas funções. A rotação da chave HS256 exige novo login.

## Contrato dos remote states e ordem de implantação

| State | Output obrigatório | Uso |
| --- | --- | --- |
| Database | `application_secret_arns["auth"]` | ARN do Secret do papel PostgreSQL de runtime |
| Database | `rds_endpoint`, `rds_port`, `rds_security_group_id` | Conexão PostgreSQL e regras de rede |
| Cloud | `vpc_id`, `private_subnet_ids` | Rede das Lambdas e endpoint Secrets Manager |
| Cloud | `os_identity_ingress.base_url` | Origem HTTP privada da OS |
| Cloud | `os_identity_ingress.client_security_group_id` | SG cliente associado às duas Lambdas |

Os nomes/campos acima são o contrato esperado, sem fallback para entradas manuais. Se Database usar uma chave diferente no mapa, será necessário alinhar esse contrato antes do deploy. Valores secretos não são publicados por Auth.

Prepare Database (incluindo banco, papel, grants e Secret) e implante Cloud para publicar rede e integração HTTP privada. Em seguida implante Auth e depois Cloud novamente para configurar as integrações e permissões de invocação com os outputs de Auth. Os states continuam separados; esta alteração não migra recursos entre states.

O workflow mantém AWS Academy, backend, environment `production` e permissões existentes. `AUTH_DB_SECRET_ARN`, `OS_IDENTITY_BASE_URL` e `OS_IDENTITY_SECRET_ARN` deixam de ser variáveis de Actions necessárias. `OS_IDENTITY_BASE_URL` continua existindo apenas como configuração de runtime preenchida pelo Terraform a partir da Cloud.

Para validação local: `ruff check src tests`, `pytest`, `terraform -chdir=infra fmt -check`, `terraform -chdir=infra init -backend=false` e `terraform -chdir=infra validate`. Esses comandos não comprovam que os outputs já existem na AWS. A ausência dos outputs/Secret, a configuração do listener/SG e o bootstrap PostgreSQL são pendências externas de integração; exigem validação no ambiente preparado antes da implantação.

## Publicação para a Cloud

Após o apply de Auth, obtenha os quatro outputs e grave o JSON abaixo na variável de Actions `AUTH_LAMBDA_ARNS` da Cloud.

| Campo | Output do Terraform de Auth |
| --- | --- |
| `login` | `auth_login_lambda_arn` |
| `login_invoke` | `auth_login_lambda_invoke_arn` |
| `authorizer` | `authorizer_lambda_arn` |
| `authorizer_invoke` | `authorizer_lambda_invoke_arn` |

A Cloud limita a invocação do Login a `POST /auth/login` no stage `$default`. A permissão do Authorizer é específica ao ID da API e ao ID do Authorizer. Payload v2.0, respostas simples e cache desabilitado são parte do contrato. O Authorizer produz 401 por credenciais ausentes ou inválidas e 403 por falta de autorização para a rota. [Lambda Authorizer para HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html)
