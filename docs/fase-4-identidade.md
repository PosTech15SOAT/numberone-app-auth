# Bloco 1A · Identidade e autorização

A OS mantém o cadastro de clientes. Auth mantém as credenciais, os perfis e as permissões em `numberone_auth`, no RDS compartilhado. O campo `auth_usuario.cliente_id` guarda apenas o UUID do cliente na OS. A consulta à OS ocorre por HTTPS privado e a OS usa a própria conexão para ler seu cadastro.

## Provisionamento

1. Use o usuário de administração do RDS para executar `psql -d postgres -f db/phase4/bootstrap.psql` a partir de uma origem que alcance o RDS. Atribua uma senha ao papel dedicado com `\password numberone_auth_runtime` e grave a credencial no Secrets Manager. Confirme que `numberone_auth_runtime` não tem `CONNECT` no banco de OS e não tem permissões de escrita nas tabelas de Auth. O bootstrap de Database já revoga o `CONNECT` de `PUBLIC` nos bancos dos serviços.
2. Gere uma credencial de serviço aleatória de pelo menos 32 caracteres. Grave o mesmo valor no segredo de Auth `{"token":"..."}` e na chave `token` do Secret `numberone-auth-os-identity` do namespace da OS. A origem HTTPS privada deve encaminhar `POST /internal/auth/customer-identity` à OS. Mantenha essa rota fora da API pública. A OS exige o Bearer e um `X-Correlation-Id` UUID antes de consultar o vínculo.
3. Para cadastrar um operador, o responsável de Auth confirma a identidade e o vínculo funcional e registra a aprovação do papel `ADMIN`. O comando `python -m scripts.enroll_identity --type OPERATOR` pede CPF e senha no terminal. O acesso exige essa credencial individual e a permissão `ADMIN_ACCESS`.
4. Para cadastrar um cliente, o responsável de Auth confirma sua identidade, obtém o UUID e cria a credencial com `python -m scripts.enroll_identity --type CUSTOMER --customer-id <uuid>`. O comando confirma o vínculo com a OS antes de criar a conta. Use as credenciais de um mantenedor do banco para o cadastro. As Lambdas usam o papel de leitura. Entregue a credencial pelo canal acordado com a pessoa verificada.

No ambiente AWS Academy, o segredo de identidade contém `token` e `ca_pem`. O Auth confia nessa CA para validar o certificado HTTPS do proxy privado. O Terraform associa as duas Lambdas ao security group publicado pela Cloud em `os_identity_ingress.client_security_group_id`. Antes do deploy de Auth, a Cloud precisa ter publicado esse output e `OS_IDENTITY_BASE_URL` precisa apontar para `os_identity_ingress.base_url`.

O Login recebe `cpf` e `password`. O cliente usa o tipo padrão `CUSTOMER`. O operador envia `"identityType":"OPERATOR"`. O CPF seleciona a conta no tipo indicado. O cadastro define o perfil. As senhas são persistidas com sal individual e PBKDF2-HMAC-SHA256. As migrations em `db/migrations` descrevem a Fase 3. Em uma migração de dados legados, confirme e recadastre as identidades com novas credenciais antes de habilitá-las.

## Decisões por rota

| Rota | Decisão |
| --- | --- |
| `POST /auth/login` | Login verifica a senha. Para cliente, também confirma UUID, CPF e status ativo com a OS. |
| `/api/admin/…` | Authorizer valida JWT, consulta identidade ativa e exige `ADMIN` com `ADMIN_ACCESS`. |
| `GET /api/public/ordens-servico/{id}/acompanhamento` | Authorizer exige operador autorizado ou cliente ativo com `SERVICE_ORDER_TRACK_OWN`. OS verifica filial e titularidade da ordem. |
| `GET /api/public/veiculos/{vehicleId}/historico-manutencoes` | Authorizer aplica a mesma regra. OS verifica filial e titularidade do veículo antes de consultar DynamoDB. |
| Aprovação por link e webhook do Billing | Use as rotas explícitas do Bloco 1B. Billing valida o token do link ou a assinatura do webhook. |
| `/internal/…` | Comunicação privada. A consulta de identidade exige a credencial de serviço. |

O JWT continua HS256 com `sub`, `customer_id`, `cpf`, `role`, `roles`, `permissions`, `status`, `iss`, `aud`, `iat` e `exp`. O cliente recebe o UUID da OS em `customer_id`. O operador recebe `null`. A duração padrão é de 3600 segundos. O Authorizer verifica o sujeito e as permissões contra o cadastro atual a cada chamada. Quando a rota aceita um cliente, o Authorizer consulta novamente a OS. Para revogar uma identidade, marque `auth_usuario.ativo = false`.

No Bloco 1B, as integrações privadas das rotas protegidas devem sobrescrever os cinco cabeçalhos abaixo. As integrações das rotas dispensadas do JWT devem remover esses cabeçalhos. Só habilite a entrada de negócio com o balanceador e os serviços protegidos de acesso direto por clientes. A OS usa os cabeçalhos escritos pela integração.

| Cabeçalho | Contexto do Authorizer |
| --- | --- |
| `X-Authenticated-Subject` | `$context.authorizer.principalId` |
| `X-Authenticated-Customer-Id` | `$context.authorizer.customerId` |
| `X-Authenticated-Status` | `$context.authorizer.userStatus` |
| `X-Authenticated-Roles` | `$context.authorizer.roles` |
| `X-Authenticated-Permissions` | `$context.authorizer.permissions` |

## Aceite pela URL da Cloud

- Emita dois JWTs com credenciais sintéticas e confira a assinatura no teste local. Use o JWT de operador em `POST /api/admin/clientes` e espere `201`. Repita com o JWT válido de cliente e espere `403`. Repita sem token ou com assinatura inválida e espere `401`.
- Consulte as rotas de acompanhamento e histórico com os clientes sintéticos. Espere `200` para os próprios recursos e `404` para os de outro cliente. Tente injetar os cabeçalhos de identidade de outro cliente e confira a mesma recusa.
- Desative o cadastro de um cliente na OS e tente consultar o próprio recurso com o JWT emitido antes da desativação. O Authorizer deve devolver `401`.

A [configuração Terraform](../infra/README.md) descreve o consumo dos ARNs pela Cloud.
