# Autenticação e entrada HTTP · Fase 4

Auth fornece as Lambdas de login e autorização. Em `develop` (`e495d58`), o desenho executável ainda corresponde à entrada do monólito da Fase 3. O Cloud da Fase 4 define VPC, EKS e ECR. A saída privada para cada microsserviço precisa ser alinhada entre os repositórios.

## Componentes verificados

| Componente | Responsabilidade |
| --- | --- |
| `src/auth_login` | Login acadêmico por CPF, consulta de cliente ativo, identidade local, claims RBAC e emissão JWT. |
| `src/authorizer` | Validação do token e montagem de contexto de autorização para o API Gateway. |
| `src/shared` | JWT, correlation ID, respostas HTTP, acesso a configuração e PostgreSQL via psycopg. |
| `db/migrations` | Schema e sementes RBAC. |
| `infra/` | Lambdas, layer, secret JWT, CloudWatch, HTTP API, authorizer e integração privada da Fase 3 via VPC Link. |

## Encaminhamento e fronteiras da Fase 4

Mapear as rotas públicas e administrativas para OS, Billing e Inventory. O acesso privado precisa encaminhar cada rota ao destino certo e retirar headers de identidade enviados pelo cliente antes de injetar o contexto de origem confiável. Os endpoints `/internal/**` pertencem à rede entre serviços. A rota pública de webhook do Billing aplica a assinatura HMAC do Mercado Pago. A jornada de aprovação pública do Billing usa autorização temporária específica.

O login atual usa acesso direto a `cliente` e ao RBAC por PostgreSQL. A entrega precisa definir a fonte de cadastro e a persistência de Auth. Se o cadastro ativo passar a ser exclusivamente da OS, alinhar o lookup interno e a identidade da chamada antes de comprovar o isolamento entre bancos. O contrato documentado no pacote da Saga e uma rota efetivamente disponível são evidências distintas.

## Evidências

A documentação de HTTP e a collection do Auth descrevem a entrada publicada. O CI da revisão consultada executou a validação da aplicação e da infraestrutura. O aceite da Fase 4 deve mostrar login, rota autorizada e rota recusada, roteamento por serviço e bloqueio de acesso externo às rotas internas.

[OpenAPI](openapi.yaml) · [Collection Postman](postman/numberone-auth.postman_collection.json) · [Fluxo de autenticação](diagrams/auth-flow.md) · [Terraform da entrada](../infra/main.tf) · [CI](https://github.com/PosTech15SOAT/numberone-app-auth/actions/runs/35037455445)
