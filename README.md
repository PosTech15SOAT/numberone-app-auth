# NumberOne App Auth

> O Bloco 1A atualiza o contrato de login e move a entrada HTTP para a Cloud.
> Consulte [Identidade e autorização na Fase 4](docs/fase-4-identidade.md) e
> [Terraform de Auth](infra/README.md). As ADRs e os diagramas da Fase 3
> registram a arquitetura anterior.

## 🧰 Tecnologias

- Python 3.12 e AWS Lambda
- Amazon API Gateway HTTP API e integração privada com a OS
- Amazon RDS PostgreSQL e AWS Secrets Manager
- JWT HS256
- Terraform, GitHub Actions e CloudWatch Logs
- Pytest e Ruff

## 📁 Estrutura do Projeto

```text
src/            Lambdas de login, authorizer e codigo compartilhado
db/migrations/  Migrations legadas e bootstrap da base de identidade
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

O login usa CPF e senha de uma conta provisionada. A OS confirma o vínculo
do cliente. O Authorizer valida o JWT por rota antes de enviar a identidade
aos serviços. O login exige um `X-Correlation-Id` não vazio.

## 🚀 CI/CD

- Pushes executam lint, testes, build da layer e validacao Terraform.
- Pull requests para `develop` e `main` executam validacao.
- O fluxo de mudanca e `feature/* -> Pull Request -> develop -> Pull Request -> main`.
- Protecao de branches e required checks sao centralizados em `postech15soat-governance`; este repositorio nao os reimplementa.

## ☁️ Deploy

`main` representa production e aciona o deploy automatico pelo workflow `deploy-prod.yml`, usando exclusivamente o GitHub Environment `production` e `TF_VAR_environment=prod`. Nao existe ambiente cloud de homologacao.

## 🔌 APIs

`POST /auth/login` é público e exige CPF, senha e correlação. Consulte o
[OpenAPI](docs/openapi.yaml) e a [coleção Postman](docs/postman/numberone-auth.postman_collection.json).
A coleção salva o `accessToken` do login para as próximas requisições.
O Authorizer protege as rotas de negócio configuradas na Cloud. As integrações
preenchem os cabeçalhos de identidade a partir do contexto do Authorizer.
Consulte o [contrato de identidade e autorização](docs/fase-4-identidade.md).

## 🗃️ Banco de dados

As duas funções usam o banco exclusivo de Auth com um papel de leitura.
A OS mantém o cadastro de clientes e confirma o vínculo pela rota privada
de identidade. O bootstrap dessa base fica em `db/phase4`.

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
