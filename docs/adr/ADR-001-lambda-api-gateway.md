# ADR-001 - Lambda e API Gateway para autenticacao

## Status

Accepted

## Contexto

A Fase 3 exige API Gateway, Function Serverless para autenticacao por CPF e protecao de rotas sensiveis.

## Decisao

Usar Amazon API Gateway HTTP API com duas Lambdas:

- `auth_login`: valida CPF, consulta cliente e emite JWT.
- `authorizer`: valida JWT antes de encaminhar chamadas para `/api/admin/*`.

## Consequencias

- A autenticacao fica segregada da aplicacao principal.
- O gateway passa a ser ponto central de entrada HTTP.
- As Lambdas precisam acessar segredos e, no caso do login, o banco PostgreSQL/RDS.
- A URL da aplicacao principal precisa ser fornecida ao Terraform.
