# RFC-001 - Desenho da Autenticacao

## Objetivo

Implementar autenticacao serverless por CPF para proteger rotas sensiveis da aplicacao NumberOne.

## Proposta

1. Cliente chama `POST /auth/login` com CPF.
2. Lambda valida formato e digitos verificadores do CPF.
3. Lambda consulta `cliente` no PostgreSQL.
4. Lambda cria ou atualiza `auth_usuario`.
5. Lambda consulta perfis e permissoes.
6. Lambda emite JWT com `user_status`, perfis e permissoes.
7. API Gateway usa Lambda Authorizer para rotas `/api/admin/*`.
8. Lambda Authorizer valida o JWT e devolve context para o API Gateway.
9. API Gateway encaminha headers `X-Authenticated-*` para a aplicacao principal.

## Decisoes confirmadas

- Login sera por CPF valido e cliente ativo no PostgreSQL.
- Tokens serao JWT HS256 com segredo no AWS Secrets Manager.
- Rotas administrativas passarao pelo Lambda Authorizer.
- Contexto autenticado sera repassado ao backend por headers `X-Authenticated-*`.
- RBAC sera enviado no JWT e nos headers de contexto.

## Dependencias de integracao

Os itens abaixo dependem dos demais repositorios/ambiente AWS e nao alteram as
decisoes tecnicas desta RFC:

- URL final da aplicacao principal no Kubernetes/Load Balancer.
- Ambientes `homolog` e `production` na AWS.
- ARNs finais dos segredos de banco e JWT.
- Aplicacao principal consumir os headers `X-Authenticated-*` para montar o contexto do usuario.
