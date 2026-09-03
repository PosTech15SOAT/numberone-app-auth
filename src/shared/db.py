from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.shared.config import db_settings


def connect() -> psycopg.Connection:
    settings = db_settings()
    return psycopg.connect(
        host=settings["host"],
        port=settings.get("port", 5432),
        dbname=settings["dbname"],
        user=settings["username"],
        password=settings["password"],
        sslmode=settings.get("sslmode", "require"),
        row_factory=dict_row,
        connect_timeout=5,
    )


def find_active_customer_by_cpf(cpf: str) -> dict[str, Any] | None:
    query = """
        select id, nome, documento, email, ativo
          from cliente
         where regexp_replace(documento, '\\D', '', 'g') = %s
           and tipo_documento = 'PESSOA_FISICA'
         limit 1
    """

    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (cpf,))
            return cursor.fetchone()


def find_or_create_auth_user(customer: dict[str, Any], cpf: str) -> dict[str, Any]:
    upsert_user = """
        insert into auth_usuario (cliente_id, cpf, nome, email, ativo)
        values (%s, %s, %s, %s, true)
        on conflict (cpf)
        do update set
            cliente_id = excluded.cliente_id,
            nome = excluded.nome,
            email = excluded.email,
            updated_at = now()
        returning id, cliente_id, cpf, nome, email, ativo
    """

    assign_default_role = """
        insert into auth_usuario_perfil (usuario_id, perfil_id)
        select %s, p.id
          from auth_perfil p
         where p.nome = 'CUSTOMER'
        on conflict (usuario_id, perfil_id) do nothing
    """

    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                upsert_user,
                (
                    customer["id"],
                    cpf,
                    customer["nome"],
                    customer["email"],
                ),
            )
            auth_user = cursor.fetchone()
            cursor.execute(assign_default_role, (auth_user["id"],))
            return auth_user


def find_rbac_claims(user_id: str) -> dict[str, list[str]]:
    query = """
        select
            coalesce(array_agg(distinct p.nome) filter (where p.nome is not null), '{}') as roles,
            coalesce(
                array_agg(distinct pe.chave) filter (where pe.chave is not null),
                '{}'
            ) as permissions
          from auth_usuario u
          left join auth_usuario_perfil up on up.usuario_id = u.id
          left join auth_perfil p on p.id = up.perfil_id and p.ativo = true
          left join auth_perfil_permissao pp on pp.perfil_id = p.id
          left join auth_permissao pe on pe.id = pp.permissao_id
         where u.id = %s
         group by u.id
    """

    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()

    if not result:
        return {"roles": [], "permissions": []}

    return {
        "roles": list(result["roles"]),
        "permissions": list(result["permissions"]),
    }
