# RFC-001 - Desenho da Autenticacao

## Objetivo

Implementar autenticacao serverless por CPF para proteger rotas sensiveis da aplicacao NumberOne.

## Proposta

1. Cliente chama `POST /auth/login` com CPF.
2. Lambda valida formato e digitos verificadores do CPF.
3. Lambda consulta `cliente` no PostgreSQL.
4. Lambda cria ou atualiza `auth_usuario`.
5. Lambda consulta perfis e permissoes.
6. Lambda emite JWT.
7. API Gateway usa Lambda Authorizer nas rotas protegidas.
8. API Gateway encaminha as requisicoes para o NLB interno do EKS por VPC Link.

## Decisoes implementadas

- O unico ambiente cloud e `production`: `main` representa production e dispara
  o deploy; `develop` e usado para integracao e CI. Nao ha ambiente cloud de
  homologacao, conforme orientacao academica.
- O JWT usa segredo compartilhado armazenado no AWS Secrets Manager, de acordo
  com a estrategia HS256 registrada no ADR-002.
- O token inclui claims RBAC. O Lambda Authorizer valida o token e entrega o
  contexto autenticado ao API Gateway, que encaminha os headers
  `X-Authenticated-*` para a aplicacao principal.
- A claim JWT de origem para o status do usuario e `status`. O contexto do
  authorizer a expoe como `userStatus`, e o API Gateway a encaminha em
  `X-Authenticated-Status`.

## Evolucoes futuras

As evolucoes recomendadas nos ADRs, como RS256/JWKS e RDS Proxy, permanecem
fora do escopo desta entrega e nao constituem decisoes aceitas por esta RFC.
