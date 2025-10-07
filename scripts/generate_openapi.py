from __future__ import annotations

import importlib
from pathlib import Path
from typing import Iterable

import yaml


SERVICES: dict[str, str] = {
    "account_service": "services.account_service.presentation.main:app",
    "transaction_service": "services.transaction_service.presentation.main:app",
    "auth_service": "services.auth_service.presentation.main:app",
    "audit_service": "services.audit_service.presentation.main:app",
    "monitoring_service": "services.monitoring_service.presentation.main:app",
}


def load_app(path: str):
    module_path, app_name = path.split(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, app_name)


def dump_openapi(app, destination: Path) -> None:
    openapi_schema = app.openapi()
    destination.write_text(
        yaml.safe_dump(openapi_schema, sort_keys=False, allow_unicode=True) + "\n",
        encoding="utf-8",
    )


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def generate_specs(services: Iterable[tuple[str, str]]) -> None:
    for service_name, app_path in services:
        app = load_app(app_path)
        output_path = Path("services") / service_name / "openapi.yaml"
        ensure_directory(output_path)
        dump_openapi(app, output_path)
        print(f"Generated OpenAPI spec for {service_name} at {output_path}")


if __name__ == "__main__":
    generate_specs(SERVICES.items())
