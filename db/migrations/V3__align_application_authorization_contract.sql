UPDATE auth_perfil
   SET nome = 'CUSTOMER',
       descricao = 'Cliente autenticado por CPF'
 WHERE nome = 'CLIENTE';

INSERT INTO auth_permissao (chave, descricao)
VALUES
    ('SERVICE_ORDER_TRACK_OWN', 'Acompanhar as proprias ordens de servico'),
    ('BUDGET_RESPOND_OWN', 'Aprovar ou rejeitar o proprio orcamento')
ON CONFLICT (chave) DO NOTHING;

INSERT INTO auth_perfil_permissao (perfil_id, permissao_id)
SELECT perfil.id, permissao.id
  FROM auth_perfil perfil
 CROSS JOIN auth_permissao permissao
 WHERE perfil.nome = 'CUSTOMER'
   AND permissao.chave IN ('SERVICE_ORDER_TRACK_OWN', 'BUDGET_RESPOND_OWN')
ON CONFLICT (perfil_id, permissao_id) DO NOTHING;
