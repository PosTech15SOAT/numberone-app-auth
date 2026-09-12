# TODO - Marcelo Auth

## Passo 1 - Base do repositorio

- [x] Criar estrutura inicial do repositorio.
- [x] Criar README com objetivo, stack, fluxos e execucao.
- [x] Criar modelo RBAC.
- [x] Criar DER em Mermaid.
- [x] Criar migrations iniciais.
- [x] Criar esqueleto das Lambdas.
- [x] Criar Terraform inicial.
- [x] Criar workflows de CI e deploy.
- [x] Criar ADRs iniciais.
- [x] Adicionar OpenAPI/Postman da autenticacao.
- [x] Adicionar logs JSON nas Lambdas.
- [x] Adicionar API Gateway access logs.
- [x] Adicionar build de Lambda Layer.

## Passo 2 - Validacao local

- [x] Instalar Python dependencies.
- [x] Rodar `ruff check`.
- [x] Rodar `pytest`.
- [x] Gerar `build/lambda-layer.zip`.
- [x] Instalar Terraform.
- [x] Rodar `terraform fmt`.
- [x] Rodar `terraform init` com backend S3 remoto.
- [x] Rodar `terraform validate`.

## Passo 3 - Integracao com o grupo

- [x] Integrar o API Gateway ao NLB interno da aplicacao por VPC Link.
- [ ] Confirmar segredo JWT compativel com a API principal.
- [ ] Confirmar dados do RDS e estrategia de acesso da Lambda ao banco.
- [ ] Confirmar se a API principal vai consumir claims RBAC.
- [ ] Configurar o unico GitHub Environment `production` para deploy de `main`.

## Passo 4 - AWS e entrega

- [ ] Criar secrets no AWS Secrets Manager.
- [ ] Configurar OIDC/IAM para GitHub Actions.
- [ ] Validar o deploy production via `main`.
- [ ] Testar `POST /auth/login`.
- [ ] Testar rota `/api/admin/*` com Lambda Authorizer.
- [x] Proteger branch `main`. Ja aparece protegida na organizacao.
- [ ] Atualizar README com links finais de deploy.
