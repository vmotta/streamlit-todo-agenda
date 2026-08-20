"""Exceções de domínio exibíveis de forma segura na interface."""


class OrganizaError(Exception):
    """Erro base esperado da aplicação."""


class ValidationError(OrganizaError):
    """Entrada incompatível com as regras de negócio."""


class NotFoundError(OrganizaError):
    """Entidade inexistente ou pertencente a outro usuário."""


class PersistenceError(OrganizaError):
    """Falha ao persistir uma operação."""
