# NumberOne App Auth

## 📌 Visão Geral

Servico de autenticacao serverless do Tech Challenge Fase 3 do NumberOne. Ele realiza login por CPF, emite JWT, aplica o modelo RBAC e protege as rotas da aplicacao principal por meio de Lambda Authorizer e API Gateway.

## 🏗️ Arquitetura

Fluxo em production:

```text
Cliente -> API Gateway HTTP API -> Lambda Authorizer -> VPC Link -> NLB interno -> EKS/Spring -> RDS
                 |
                 +-> Lambda de login por CPF -> RDS
```

O login e publico. As rotas de negocio passam pelo authorizer antes de seguir para a aplicacao principal. Os diagramas detalhados estao em [Fluxos de autenticacao e autorizacao](docs/diagrams/auth-flow.md) e [DER da autenticacao](docs/diagrams/auth-rbac-er.md).

## 🧰 Tecnologias

- Python 3.12 e AWS Lambda
- Amazon API Gateway HTTP API, VPC Link e NLB interno
- Amazon RDS PostgreSQL e AWS Secrets Manager
- JWT HS256
- Terraform, GitHub Actions e CloudWatch Logs
- Pytest e Ruff

## 📁 Estrutura do Projeto

```text
src/            Lambdas de login, authorizer e codigo compartilhado
db/migrations/  Migrations do modelo RBAC
infra/          Terraform da frente de autenticacao
docs/           Contratos, diagramas, ADRs e RFCs
tests/          Testes automatizados
scripts/        Build local e de CI da Lambda Layer
```

## ✅ Pré-requisitos

- Python 3.12
- Terraform >= 1.7 para validacao ou operacoes de infraestrutura
- AWS CLI autenticado e acesso ao ambiente AWS Academy para operacoes cloud

## ⚙️ Configuração

Para desenvolvimento e testes locais:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

As Lambdas recebem configuracoes de banco, JWT e rede pelo Terraform. Os detalhes de variaveis e state estao no [README de infraestrutura](infra/README.md).

## ▶️ Execução Local

Execute os testes e gere a layer de dependencias:

```bash
pytest
./scripts/build-lambda-layer.sh
```

Para validar o Terraform sem acessar o backend remoto:

```bash
cd infra
terraform fmt -check
terraform init -backend=false
terraform validate
```

## 🧪 Testes

O projeto usa `ruff check src tests` para lint e `pytest` para os testes automatizados. A CI tambem valida a geracao da Lambda Layer e o Terraform.

## 🔐 Segurança

- O login valida CPF e consulta cliente e usuario de autenticacao ativos.
- Tokens JWT HS256 usam segredo no AWS Secrets Manager; a escolha e registrada no [ADR-002](docs/adr/ADR-002-jwt-strategy.md).
- O authorizer valida JWT nas rotas protegidas. A claim `status` e transformada em `userStatus` no contexto do authorizer e, no gateway, em `X-Authenticated-Status`.
- `POST /auth/login` exige `X-Correlation-Id` para rastreabilidade. Nas rotas protegidas, esse header nao e requisito de autorizacao: se fornecido, segue para a aplicacao e para os logs; sua ausencia nao impede o authorizer.

## 🚀 CI/CD

- Pushes executam lint, testes, build da layer e validacao Terraform.
- Pull requests para `develop` e `main` executam validacao.
- O fluxo de mudanca e `feature/* -> Pull Request -> develop -> Pull Request -> main`.
- Protecao de branches e required checks sao centralizados em `postech15soat-governance`; este repositorio nao os reimplementa.

## ☁️ Deploy

`main` representa production e aciona o deploy automatico pelo workflow `deploy-prod.yml`, usando exclusivamente o GitHub Environment `production` e `TF_VAR_environment=prod`. Nao existe ambiente cloud de homologacao.

## 🔌 APIs

| Rota | Autorizacao | Destino |
| --- | --- | --- |
| `POST /auth/login` | Publica; requer `X-Correlation-Id` | Lambda `auth_login` |
| `ANY /api/public/{proxy+}` | Lambda Authorizer | Aplicacao principal |
| `ANY /api/admin/{proxy+}` | Lambda Authorizer | Aplicacao principal |

O contrato detalhado esta em [OpenAPI](docs/openapi.yaml). A [colecao Postman](docs/postman/numberone-auth.postman_collection.json) inclui uma variavel `correlationId` e salva automaticamente o `accessToken` retornado no login.

Nas rotas protegidas, o backend recebe do API Gateway:

- `X-Authenticated-Subject`
- `X-Authenticated-Customer-Id`
- `X-Authenticated-Status`
- `X-Authenticated-Roles`
- `X-Authenticated-Permissions`
- `X-Correlation-Id`, quando informado pelo cliente

## 📊 Observabilidade

As Lambdas e o API Gateway registram logs no CloudWatch. O gateway registra `requestId` da AWS e o valor recebido de `X-Correlation-Id`; nao ha geracao de fallback para esse header.

## 🗃️ Banco de Dados

O login consulta PostgreSQL/RDS para cliente, usuario, perfis e permissoes. O modelo RBAC e suas migrations ficam em `db/migrations/`; consulte o [DER](docs/diagrams/auth-rbac-er.md). O segredo do RDS e obtido do state de infraestrutura de banco ou pode ser informado por override, conforme [infra/README.md](infra/README.md).

## 📚 Documentação

- [Infraestrutura](infra/README.md)
- [OpenAPI](docs/openapi.yaml)
- [Colecao Postman](docs/postman/numberone-auth.postman_collection.json)
- [Fluxos de autenticacao e autorizacao](docs/diagrams/auth-flow.md)
- [DER da autenticacao](docs/diagrams/auth-rbac-er.md)
- [RFC-001 - Desenho da autenticacao](docs/rfc/RFC-001-authentication-design.md)

## 🧠 Decisões Arquiteturais
### ADRs/RFCs

- [ADR-001 - Lambda e API Gateway](docs/adr/ADR-001-lambda-api-gateway.md)
- [ADR-002 - Estrategia JWT](docs/adr/ADR-002-jwt-strategy.md)
- [ADR-003 - Modelo RBAC](docs/adr/ADR-003-rbac-model.md)
- [ADR-004 - Acesso das Lambdas ao RDS e Secrets Manager](docs/adr/ADR-004-lambda-rds-secrets.md)
- [ADR-005 - Roteamento do API Gateway](docs/adr/ADR-005-api-gateway-routing.md)

## ⚠️ Limitações e decisões do ambiente acadêmico

O ambiente cloud e o AWS Academy. Por essa restricao, o Terraform reutiliza a `LabRole` existente em vez de provisionar IAM roles ou policies. Ha somente ambiente local e production na AWS; a ausencia de homologacao cloud e uma decisao pragmatica do contexto academico.

## 🤝 Contribuição

Crie uma branch `feature/*`, abra Pull Request para `develop` e, apos a integracao, promova de `develop` para `main` por Pull Request. Nao faca push direto para `develop` ou `main`.
