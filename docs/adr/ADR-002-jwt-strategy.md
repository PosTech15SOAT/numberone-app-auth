# ADR-002 - Estrategia JWT

## Status

Accepted

## Contexto

A aplicacao principal NumberOne ja possui validacao JWT com segredo compartilhado. A Fase 3 precisa emitir tokens a partir da autenticacao por CPF.

## Decisao

Iniciar com JWT HS256 para compatibilidade com a aplicacao principal.

Claims principais:

- `sub`: id do usuario de autenticacao.
- `customer_id`: id do cliente.
- `cpf`: CPF autenticado.
- `role`: primeiro perfil do usuario, mantido para compatibilidade com a aplicacao principal atual.
- `roles`: perfis RBAC.
- `permissions`: permissoes RBAC.
- `iss`: issuer.
- `aud`: audience.
- `iat`: data de emissao.
- `exp`: expiracao.

## Consequencias

- Menor alteracao na aplicacao principal.
- O segredo precisa ser compartilhado com seguranca via Secrets Manager.
- Evolucao futura recomendada: RS256 com JWKS para reduzir compartilhamento de segredo simetrico.
