"""Resolução da identidade confiável da aplicação."""

from collections.abc import Mapping

from organiza.exceptions import ValidationError

LOCAL_OWNER_ID = "local-user"


def resolve_owner_id(auth_mode: str, claims: Mapping[str, object] | None = None) -> str:
    if auth_mode == "none":
        return LOCAL_OWNER_ID
    if auth_mode != "oidc":
        raise ValidationError("Modo de autenticação inválido.")
    subject = claims.get("sub") if claims else None
    if not isinstance(subject, str) or not subject.strip():
        raise ValidationError("A identidade OIDC não forneceu um identificador seguro.")
    return subject.strip()
