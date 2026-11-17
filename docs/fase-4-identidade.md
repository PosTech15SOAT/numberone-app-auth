# Bloco 1A · Identidade e autorização

A OS mantém o cadastro de clientes. Auth mantém as credenciais, os perfis e as permissões em `numberone_auth`, no RDS compartilhado. O campo `auth_usuario.cliente_id` guarda apenas o UUID do cliente na OS. A consulta à OS ocorre por HTTP privado e a OS usa a própria conexão para ler seu cadastro.

## Provisionamento

1. Prepare o banco e o papel dedicado com o [bootstrap](../db/phase4/bootstrap.psql) a partir de uma origem autorizada a alcançar o RDS. Database cria o Secret `numberone-auth-database` com a credencial do papel `numberone_auth_runtime` e publica seu ARN em `application_secret_arns["auth"]`. A senha PostgreSQL deve corresponder ao Secret. Confirme que o papel não tem `CONNECT` no banco de OS nem permissões de escrita nas tabelas de Auth. O bootstrap de Database já revoga o `CONNECT` de `PUBLIC` nos bancos dos serviços.
2. Cloud provisiona a origem HTTP privada e publica `os_identity_ingress.base_url` e `os_identity_ingress.client_security_group_id`. A origem deve encaminhar `POST /internal/auth/customer-identity` à OS, fora da API pública. A consulta usa `X-Correlation-Id` UUID e JSON com `customerId` e `cpf`, sem autenticação HTTP entre serviços. A OS retorna `204` apenas para o vínculo ativo e correspondente, ou `404` para vínculo inválido/inativo.
3. Para cadastrar um operador, o responsável de Auth confirma a identidade e o vínculo funcional e registra a aprovação do papel `ADMIN`. O comando `python -m scripts.enroll_identity --type OPERATOR` pede CPF e senha no terminal. O acesso exige essa credencial individual e a permissão `ADMIN_ACCESS`.
4. Para cadastrar um cliente, o responsável de Auth confirma sua identidade, obtém o UUID e cria a credencial com `python -m scripts.enroll_identity --type CUSTOMER --customer-id <uuid>`. O comando confirma o vínculo com a OS antes de criar a conta. Use as credenciais de um mantenedor do banco para o cadastro. As Lambdas usam o papel de leitura. Entregue a credencial pelo canal acordado com a pessoa verificada.

O Terraform consome a URL e o SG diretamente do state Cloud e o ARN do Secret PostgreSQL diretamente do state Database. Não se configura manualmente `AUTH_DB_SECRET_ARN`, `OS_IDENTITY_BASE_URL` ou `OS_IDENTITY_SECRET_ARN` nas Actions. O cliente aceita somente HTTP para DNS de balanceador AWS interno ou IPv4 RFC1918, conforme o [contrato de infraestrutura](../infra/README.md), sem proxies de ambiente ou redirects e com timeout de dois segundos. Não lê token ou CA de identidade e não envia `Authorization`. Qualquer falha da OS impede a concessão de acesso: Login retorna erro e Authorizer falha sem autorizar.

A ordem permanece Database preparado → Cloud → Auth → Cloud. O SG publicado pela Cloud precisa permitir HTTP até o listener privado e impedir acesso público à rota interna. O endpoint Secrets Manager e suas regras TCP/443 continuam necessários para banco e JWT. O comando de cadastro local também precisa usar a origem provisionada pela Cloud, a partir de uma rede autorizada.

O Login recebe `cpf` e `password`. O cliente usa o tipo padrão `CUSTOMER`. O operador envia `"identityType":"OPERATOR"`. O CPF seleciona a conta no tipo indicado. O cadastro define o perfil. As senhas são persistidas com sal individual e PBKDF2-HMAC-SHA256. As migrations em `db/migrations` descrevem a Fase 3. Em uma migração de dados legados, confirme e recadastre as identidades com novas credenciais antes de habilitá-las.

## Decisões por rota

| Rota | Decisão |
| --- | --- |
| `POST /auth/login` | Login verifica a senha. Para cliente, também confirma UUID, CPF e status ativo com a OS. |
| `/api/admin/…` | Authorizer valida JWT, consulta identidade ativa e exige `ADMIN` com `ADMIN_ACCESS`. |
| `GET /api/public/ordens-servico/{id}/acompanhamento` | Authorizer exige operador autorizado ou cliente ativo com `SERVICE_ORDER_TRACK_OWN`. OS verifica filial e titularidade da ordem. |
| `GET /api/public/veiculos/{vehicleId}/historico-manutencoes` | Authorizer aplica a mesma regra. OS verifica filial e titularidade do veículo antes de consultar DynamoDB. |
| Aprovação por link e webhook do Billing | Use as rotas explícitas do Bloco 1B. Billing valida o token do link ou a assinatura do webhook. |
| `/internal/…` | Comunicação HTTP privada, protegida pela rede; sem autenticação HTTP entre serviços. |

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
