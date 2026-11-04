
"""Authentification par clé API."""

import secrets

from fastapi import Header, HTTPException

from maintai.config import get_settings


def require_api_key(
    x_api_key: str | None = Header(default=None)
) -> None:

    expected = get_settings().api_key

    if not expected:
        raise HTTPException(
            status_code=500,
            detail="Clé API non configurée"
        )

    if x_api_key is None or not secrets.compare_digest(
        x_api_key, expected
    ):
        raise HTTPException(
            status_code=401,
            detail="Clé API absente ou invalide"
        )
