# ADR-003 - Modelo RBAC

## Status

Accepted

## Contexto

A frente de autenticacao precisa definir usuario, perfil e permissao, mantendo rastreabilidade com o cliente existente na base da aplicacao.

## Decisao

Criar cinco tabelas:

- `auth_usuario`
- `auth_perfil`
- `auth_permissao`
- `auth_usuario_perfil`
- `auth_perfil_permissao`

O usuario de autenticacao referencia `cliente.id` e usa `cpf` como chave de login.

## Consequencias

- O modelo permite perfis e permissoes sem alterar a tabela `cliente`.
- As Lambdas podem emitir claims de autorizacao no JWT.
- O cadastro inicial de perfis/permissoes fica versionado por migration.
