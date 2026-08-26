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
7. API Gateway usa Lambda Authorizer para rotas `/api/admin/*`.

## Pontos em aberto

- URL final da aplicacao principal no Kubernetes.
- Ambiente de homologacao e producao na AWS.
- Segredo JWT definitivo.
- Se a aplicacao principal vai consumir apenas validade do token ou tambem claims RBAC.
