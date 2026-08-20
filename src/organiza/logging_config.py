"""Logging centralizado, sem dados sensíveis."""

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
