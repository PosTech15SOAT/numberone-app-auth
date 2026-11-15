"""Run as an Auth database maintainer after verifying the person's identity."""

import argparse
from getpass import getpass

from src.shared.cpf import is_valid_cpf, only_digits
from src.shared.db import connect
from src.shared.identity import ADMIN, CUSTOMER, canonical_uuid
from src.shared.os_identity import matches_active_customer
from src.shared.password import hash_password


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["CUSTOMER", "OPERATOR"], required=True)
    parser.add_argument("--customer-id", help="Canonical UUID from OS for CUSTOMER")
    args = parser.parse_args()
    if args.type == CUSTOMER and not canonical_uuid(args.customer_id):
        parser.error("For CUSTOMER, --customer-id must be the canonical OS UUID.")
    if args.type == "OPERATOR" and args.customer_id is not None:
        parser.error("--customer-id is only for CUSTOMER.")

    cpf = only_digits(getpass("CPF verificado: "))
    if not (cpf.isascii() and is_valid_cpf(cpf)):
        parser.error("CPF invalido.")
    if args.customer_id and not matches_active_customer(args.customer_id, cpf):
        parser.error("A OS nao confirmou um cliente ativo com este UUID e CPF.")

    password = getpass("Senha de acesso: ")
    if password != getpass("Repita a senha: "):
        parser.error("As senhas diferem.")
    try:
        stored_hash = hash_password(password)
    except ValueError as exception:
        parser.error(str(exception))

    role = ADMIN if args.type == "OPERATOR" else CUSTOMER
    with connect() as conn:
        row = conn.execute(
            """
            insert into auth_usuario (cpf, perfil, cliente_id, senha_hash)
            values (%s, %s, %s, %s)
            on conflict do nothing
            returning id
            """,
            (cpf, role, args.customer_id, stored_hash),
        ).fetchone()
        if not row:
            parser.error("Ja existe uma identidade para este CPF e perfil, ou UUID de cliente.")
        print(f"Identidade criada: {row['id']}")


if __name__ == "__main__":
    main()
