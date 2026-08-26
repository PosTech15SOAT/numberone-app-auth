# ADR-004 - Acesso das Lambdas ao RDS e Secrets Manager

## Status

Accepted

## Contexto

A Lambda de autenticacao precisa consultar clientes e RBAC no PostgreSQL/RDS. As credenciais e o segredo JWT nao devem ficar versionados no repositorio.

## Decisao

Usar AWS Secrets Manager para:

- credenciais do banco;
- segredo JWT.

Quando o RDS estiver privado, executar a Lambda de autenticacao em subnets privadas com Security Group autorizado no RDS.

## Consequencias

- Segredos ficam fora do codigo e das variaveis abertas.
- A Lambda precisa de IAM policy `secretsmanager:GetSecretValue`.
- A execucao em VPC exige configuracao de subnets, security groups e permissao `AWSLambdaVPCAccessExecutionRole`.
- A conexao direta com RDS e aceitavel para o escopo do Tech Challenge; evolucao futura recomendada: RDS Proxy.
