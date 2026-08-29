# ADR-005 - Roteamento do API Gateway

## Status

Accepted

## Contexto

A Fase 3 exige API Gateway para controle e roteamento, protegendo rotas sensiveis da aplicacao.

## Decisao

Usar Amazon API Gateway HTTP API com:

- `POST /auth/login` publico para emissao de JWT;
- `ANY /api/public/health` publico para health check;
- `ANY /api/public/{proxy+}` protegido por Lambda Authorizer para operacoes do cliente;
- `ANY /api/admin/{proxy+}` protegido por Lambda Authorizer.

Nas rotas protegidas, o gateway encaminha `X-Authenticated-*` e `X-Correlation-Id` para que a aplicacao principal consiga montar o contexto do usuario autenticado.

## Consequencias

- O gateway vira a entrada unica para clientes externos.
- A aplicacao principal nao precisa emitir tokens.
- A aplicacao principal pode remover o login atual e confiar no authorizer/gateway para autenticar chamadas externas.
