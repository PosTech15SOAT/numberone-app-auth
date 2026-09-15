# Diagrama de Sequencia - Autenticacao

Este diagrama consolida o fluxo final da frente de autenticacao: login por CPF,
emissao do JWT e validacao de rotas protegidas pelo Lambda Authorizer.

## Parte 1 - Login por CPF

```mermaid
sequenceDiagram
    actor Cliente
    participant APIGW as API Gateway
    participant Login as Lambda Login
    participant DB as PostgreSQL/RDS

    Cliente->>APIGW: POST /auth/login { cpf } + X-Correlation-Id
    APIGW->>Login: Invoke
    Login->>Login: Normaliza e valida CPF
    Login->>DB: Consulta usuario/status por CPF
    DB-->>Login: Cliente e usuario ativos ou erro de autenticacao
    Login->>DB: Upsert auth_usuario e consulta RBAC
    DB-->>Login: Perfis e permissoes
    Login->>Login: Gera JWT com status, roles e permissions
    Login-->>APIGW: 200 { accessToken, tokenType, expiresIn }
    APIGW-->>Cliente: accessToken
```

## Parte 2 - Rota protegida

```mermaid
sequenceDiagram
    actor Cliente
    participant APIGW as API Gateway
    participant Authz as Lambda Authorizer
    participant Backend as Backend NumberOne

    Cliente->>APIGW: /api/admin/* + Authorization: Bearer JWT
    APIGW->>Authz: Invoke com Bearer JWT
    Authz->>Authz: Valida assinatura, issuer, audience e expiracao
    Authz->>Authz: Cria context com principalId, customerId, userStatus e RBAC
    Authz-->>APIGW: isAuthorized=true + context
    APIGW->>Backend: Proxy com X-Authenticated-* e X-Correlation-Id quando informado
    Backend->>Backend: Cria contexto do usuario autenticado
    Backend-->>APIGW: Resposta
    APIGW-->>Cliente: Resposta
```
