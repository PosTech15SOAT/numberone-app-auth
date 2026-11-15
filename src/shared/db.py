from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.shared.config import db_settings


def connect() -> psycopg.Connection:
    settings = db_settings()
    return psycopg.connect(
        host=settings["host"],
        port=settings["port"],
        dbname=settings["dbname"],
        user=settings["username"],
        password=settings["password"],
        sslmode=settings["sslmode"],
        row_factory=dict_row,
        connect_timeout=3,
        options="-c statement_timeout=2000",
    )


def find_login_identity(cpf: str, role: str) -> dict[str, Any] | None:
    return _find_identity("u.cpf = %s and u.perfil = %s", (cpf, role))


def find_token_identity(subject: str) -> dict[str, Any] | None:
    return _find_identity("u.id = %s", (subject,))


def _find_identity(predicate: str, params: tuple[str, ...]) -> dict[str, Any] | None:
    # The predicates above are fixed SQL. All caller data is bound as parameters.
    query = f"""
        select u.id, u.cliente_id, u.cpf, u.senha_hash, u.perfil,
               array(select pp.permissao from auth_perfil_permissao pp
                      where pp.perfil = u.perfil order by pp.permissao) as permissions
          from auth_usuario u
         where u.ativo and {predicate}
    """
    with connect() as conn:
        return conn.execute(query, params).fetchone()
