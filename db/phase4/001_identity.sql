-- Apply as the schema owner in numberone_auth, never in the OS database.
BEGIN;

CREATE TABLE IF NOT EXISTS auth_perfil (
    nome text PRIMARY KEY CHECK (nome IN ('CUSTOMER', 'ADMIN'))
);

CREATE TABLE IF NOT EXISTS auth_perfil_permissao (
    perfil text NOT NULL REFERENCES auth_perfil(nome),
    permissao text NOT NULL CHECK (permissao ~ '^[A-Za-z][A-Za-z0-9_:.-]{0,119}$'),
    PRIMARY KEY (perfil, permissao)
);

CREATE TABLE IF NOT EXISTS auth_usuario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    perfil text NOT NULL REFERENCES auth_perfil(nome),
    cliente_id uuid UNIQUE,
    cpf text NOT NULL CHECK (cpf ~ '^[0-9]{11}$'),
    senha_hash text NOT NULL CHECK (senha_hash ~ '^[0-9a-f]{32}:[0-9a-f]{64}$'),
    ativo boolean NOT NULL DEFAULT true,
    CONSTRAINT auth_identidade_por_perfil UNIQUE (perfil, cpf),
    CONSTRAINT auth_cliente_obrigatorio CHECK ((perfil = 'CUSTOMER') = (cliente_id IS NOT NULL))
);

INSERT INTO auth_perfil (nome) VALUES ('CUSTOMER'), ('ADMIN') ON CONFLICT DO NOTHING;

INSERT INTO auth_perfil_permissao (perfil, permissao) VALUES
    ('ADMIN', 'ADMIN_ACCESS'),
    ('ADMIN', 'ordem-servico:read'),
    ('ADMIN', 'ordem-servico:create'),
    ('ADMIN', 'ordem-servico:update'),
    ('ADMIN', 'cliente:read'),
    ('ADMIN', 'cliente:update'),
    ('ADMIN', 'estoque:read'),
    ('ADMIN', 'estoque:update'),
    ('CUSTOMER', 'ordem-servico:read'),
    ('CUSTOMER', 'cliente:read'),
    ('CUSTOMER', 'SERVICE_ORDER_TRACK_OWN'),
    ('CUSTOMER', 'BUDGET_RESPOND_OWN')
ON CONFLICT DO NOTHING;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO numberone_auth_runtime;
GRANT SELECT ON auth_usuario, auth_perfil_permissao TO numberone_auth_runtime;

COMMIT;
