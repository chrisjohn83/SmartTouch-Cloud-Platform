"""Export one OpenAPI YAML document per SmartTouch API v2 surface."""

from copy import deepcopy
from pathlib import Path
import sys

import yaml

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_ROOT.parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app  # noqa: E402


SOURCE_OUTPUT = REPOSITORY_ROOT / "docs" / "openapi" / "v2"
ASSET_OUTPUT = REPOSITORY_ROOT / "docs" / "assets" / "openapi"

APIS = {
    "device-api.yaml": {
        "asset_filename": "device-api-v2.yaml",
        "title": "SmartTouch Device API v2",
        "description": "Register, list, inspect, update, and deregister SmartTouch devices.",
        "path_prefix": "/v2/devices",
    },
    "deployment-api.yaml": {
        "asset_filename": "deployment-api-v2.yaml",
        "title": "SmartTouch Deployment API v2",
        "description": "Deploy services, manage revisions, roll back releases, and control canaries.",
        "path_prefix": "/v2/services",
    },
    "audit-log-api.yaml": {
        "asset_filename": "audit-log-api-v2.yaml",
        "title": "SmartTouch Audit Log API v2",
        "description": "Query immutable SmartTouch device and deployment audit events.",
        "path_prefix": "/v2/audit/events",
    },
}


def collect_schema_references(value: object) -> set[str]:
    references: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str) and item.startswith("#/components/schemas/"):
                references.add(item.rsplit("/", 1)[-1])
            else:
                references.update(collect_schema_references(item))
    elif isinstance(value, list):
        for item in value:
            references.update(collect_schema_references(item))
    return references


def remove_unused_schemas(spec: dict) -> None:
    all_schemas = spec.get("components", {}).get("schemas", {})
    referenced = collect_schema_references(spec.get("paths", {}))
    pending = list(referenced)
    while pending:
        name = pending.pop()
        for nested in collect_schema_references(all_schemas.get(name, {})):
            if nested not in referenced:
                referenced.add(nested)
                pending.append(nested)
    spec["components"]["schemas"] = {
        name: schema for name, schema in all_schemas.items() if name in referenced
    }


def build_spec(title: str, description: str, path_prefix: str, asset_filename: str) -> dict:
    combined = app.openapi()
    spec = deepcopy(combined)
    spec["info"] = {
        **spec["info"],
        "title": title,
        "description": description,
        "version": "2.0.0",
        "license": {
            "name": "Proprietary",
            "url": "https://docs.smarttouch.io/legal/license",
        },
    }
    spec["servers"] = [
        {"url": "http://127.0.0.1:8090", "description": "Local reference service"},
        {"url": "https://api.smarttouch.io", "description": "Production placeholder"},
    ]
    spec["paths"] = {
        path: value for path, value in spec["paths"].items() if path.startswith(path_prefix)
    }
    remove_unused_schemas(spec)
    return spec


def main() -> None:
    for filename, settings in APIS.items():
        asset_filename = settings["asset_filename"]
        content = yaml.safe_dump(
            build_spec(**settings),
            sort_keys=False,
            allow_unicode=True,
            width=110,
        )
        SOURCE_OUTPUT.mkdir(parents=True, exist_ok=True)
        ASSET_OUTPUT.mkdir(parents=True, exist_ok=True)
        (SOURCE_OUTPUT / filename).write_text(content, encoding="utf-8", newline="\n")
        (ASSET_OUTPUT / asset_filename).write_text(content, encoding="utf-8", newline="\n")
        print(f"Exported {filename}")


if __name__ == "__main__":
    main()
