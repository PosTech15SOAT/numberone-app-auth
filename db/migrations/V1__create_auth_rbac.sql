CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS auth_usuario (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    cliente_id uuid NOT NULL,
    cpf varchar(11) NOT NULL,
    nome varchar(120) NOT NULL,
    email varchar(160),
    ativo boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone,
    CONSTRAINT auth_usuario_pkey PRIMARY KEY (id),
    CONSTRAINT auth_usuario_cpf_key UNIQUE (cpf),
    CONSTRAINT auth_usuario_cliente_key UNIQUE (cliente_id),
    CONSTRAINT auth_usuario_cliente_fk FOREIGN KEY (cliente_id) REFERENCES cliente(id),
    CONSTRAINT auth_usuario_cpf_digits_chk CHECK (cpf ~ '^[0-9]{11}$')
);

CREATE TABLE IF NOT EXISTS auth_perfil (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    nome varchar(80) NOT NULL,
    descricao varchar(255),
    ativo boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone,
    CONSTRAINT auth_perfil_pkey PRIMARY KEY (id),
    CONSTRAINT auth_perfil_nome_key UNIQUE (nome)
);

CREATE TABLE IF NOT EXISTS auth_permissao (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    chave varchar(120) NOT NULL,
    descricao varchar(255),
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT auth_permissao_pkey PRIMARY KEY (id),
    CONSTRAINT auth_permissao_chave_key UNIQUE (chave)
);

CREATE TABLE IF NOT EXISTS auth_usuario_perfil (
    usuario_id uuid NOT NULL,
    perfil_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT auth_usuario_perfil_pkey PRIMARY KEY (usuario_id, perfil_id),
    CONSTRAINT auth_usuario_perfil_usuario_fk
        FOREIGN KEY (usuario_id) REFERENCES auth_usuario(id) ON DELETE CASCADE,
    CONSTRAINT auth_usuario_perfil_perfil_fk
        FOREIGN KEY (perfil_id) REFERENCES auth_perfil(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS auth_perfil_permissao (
    perfil_id uuid NOT NULL,
    permissao_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT auth_perfil_permissao_pkey PRIMARY KEY (perfil_id, permissao_id),
    CONSTRAINT auth_perfil_permissao_perfil_fk
        FOREIGN KEY (perfil_id) REFERENCES auth_perfil(id) ON DELETE CASCADE,
    CONSTRAINT auth_perfil_permissao_permissao_fk
        FOREIGN KEY (permissao_id) REFERENCES auth_permissao(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_usuario_cliente_id ON auth_usuario(cliente_id);
CREATE INDEX IF NOT EXISTS idx_auth_usuario_ativo ON auth_usuario(ativo);
CREATE INDEX IF NOT EXISTS idx_auth_usuario_perfil_perfil_id ON auth_usuario_perfil(perfil_id);
CREATE INDEX IF NOT EXISTS idx_auth_perfil_permissao_permissao_id
    ON auth_perfil_permissao(permissao_id);
