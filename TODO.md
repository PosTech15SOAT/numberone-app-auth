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

- [ ] Instalar Python dependencies. Bloqueado localmente: ambiente sem `pip`/`venv`.
- [ ] Rodar `pytest`. Deve rodar no GitHub Actions.
- [ ] Instalar Terraform. Bloqueado localmente: binario ausente.
- [ ] Rodar `terraform fmt`. Deve rodar no GitHub Actions.
- [ ] Rodar `terraform init -backend=false`. Deve rodar no GitHub Actions.
- [ ] Rodar `terraform validate`. Deve rodar no GitHub Actions.

## Passo 3 - Integracao com o grupo

- [ ] Confirmar endpoint da aplicacao principal no Kubernetes.
- [ ] Confirmar segredo JWT compativel com a API principal.
- [ ] Confirmar dados do RDS e estrategia de acesso da Lambda ao banco.
- [ ] Confirmar se a API principal vai consumir claims RBAC.
- [ ] Definir ambientes `homolog` e `production` no GitHub.

## Passo 4 - AWS e entrega

- [ ] Criar secrets no AWS Secrets Manager.
- [ ] Configurar OIDC/IAM para GitHub Actions.
- [ ] Aplicar Terraform em homologacao.
- [ ] Testar `POST /auth/login`.
- [ ] Testar rota `/api/admin/*` com Lambda Authorizer.
- [x] Proteger branch `main`. Ja aparece protegida na organizacao.
- [ ] Atualizar README com links finais de deploy.
