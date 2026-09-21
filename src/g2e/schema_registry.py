from __future__ import annotations

from typing import Any

from .schemas import SCHEMA_REGISTRY


def schema_catalog() -> dict[str, dict[str, Any]]:
    return {
        name: model.model_json_schema()
        for name, model in sorted(SCHEMA_REGISTRY.items())
    }


def schema_model(kind: str):
    try:
        return SCHEMA_REGISTRY[kind]
    except KeyError:
        raise KeyError(f"unknown G2E schema kind: {kind}") from None


def validate_authoritative(kind: str, payload: Any):
    return schema_model(kind).parse_authoritative(payload)
