INSERT INTO auth_perfil (nome, descricao)
VALUES
    ('CLIENTE', 'Cliente autenticado por CPF'),
    ('ADMIN', 'Operador administrativo da oficina')
ON CONFLICT (nome) DO NOTHING;

INSERT INTO auth_permissao (chave, descricao)
VALUES
    ('ordem-servico:read', 'Consultar ordens de servico'),
    ('ordem-servico:create', 'Abrir ordens de servico'),
    ('ordem-servico:update', 'Atualizar ordens de servico'),
    ('cliente:read', 'Consultar dados de cliente'),
    ('cliente:update', 'Atualizar dados de cliente'),
    ('estoque:read', 'Consultar estoque'),
    ('estoque:update', 'Atualizar estoque')
ON CONFLICT (chave) DO NOTHING;

INSERT INTO auth_perfil_permissao (perfil_id, permissao_id)
SELECT p.id, pe.id
  FROM auth_perfil p
 CROSS JOIN auth_permissao pe
 WHERE p.nome = 'ADMIN'
ON CONFLICT (perfil_id, permissao_id) DO NOTHING;

INSERT INTO auth_perfil_permissao (perfil_id, permissao_id)
SELECT p.id, pe.id
  FROM auth_perfil p
  JOIN auth_permissao pe ON pe.chave IN ('ordem-servico:read', 'cliente:read')
 WHERE p.nome = 'CLIENTE'
ON CONFLICT (perfil_id, permissao_id) DO NOTHING;
