from typing import Any
from uuid import UUID

CUSTOMER = "CUSTOMER"
ADMIN = "ADMIN"
ADMIN_ACCESS = "ADMIN_ACCESS"
TRACK_OWN = "SERVICE_ORDER_TRACK_OWN"
TRACKING_ROUTES = frozenset({
    "GET /api/public/ordens-servico/{id}/acompanhamento",
    "GET /api/public/veiculos/{vehicleId}/historico-manutencoes",
})


def customer_id(identity: dict[str, Any]) -> str | None:
    value = identity["cliente_id"]
    return str(value) if value is not None else None


def canonical_uuid(value: Any) -> bool:
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        return False
