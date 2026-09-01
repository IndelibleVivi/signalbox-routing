#!/usr/bin/env python3
"""Validate cataloged Signalbox instances against Draft 2020-12 schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

if __package__:
    from .repository_paths import (
        RepositoryPathError,
        resolve_repository_glob,
        resolve_repository_path,
    )
else:
    from repository_paths import (  # type: ignore[no-redef]
        RepositoryPathError,
        resolve_repository_glob,
        resolve_repository_path,
    )


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_pointer(document: Any, pointer: str) -> list[Any]:
    """Resolve the catalog's small JSON Pointer subset, including `*` expansion."""

    values = [document]
    for raw_token in pointer.lstrip("/").split("/") if pointer else []:
        token = raw_token.replace("~1", "/").replace("~0", "~")
        next_values: list[Any] = []
        for value in values:
            if token == "*":
                if isinstance(value, list):
                    next_values.extend(value)
                elif isinstance(value, dict):
                    next_values.extend(value.values())
                else:
                    raise ValueError("wildcard cannot expand a scalar")
            elif isinstance(value, dict) and token in value:
                next_values.append(value[token])
            elif isinstance(value, list) and token.isdigit() and int(token) < len(value):
                next_values.append(value[int(token)])
            else:
                raise ValueError(f"pointer token does not resolve: {token}")
        values = next_values
    return values


def iter_instances(root: Path, selector: dict[str, str]) -> list[tuple[str, Any]]:
    if "glob" in selector:
        paths = resolve_repository_glob(root, selector["glob"])
        return [(str(path.relative_to(root)), load_json(path)) for path in paths]

    path = resolve_repository_path(root, selector["path"], expected_kind="file")
    document = load_json(path)
    pointer = selector.get("pointer")
    if pointer is None:
        return [(selector["path"], document)]
    values = resolve_pointer(document, pointer)
    if not values:
        raise ValueError(f"pointer has no instances: {pointer}")
    return [
        (f"{selector['path']}#{pointer}[{index}]", value)
        for index, value in enumerate(values)
    ]


def validate_cataloged_instances(root: Path = ROOT) -> tuple[list[str], int]:
    errors: list[str] = []
    validated = 0
    try:
        catalog_schema_path = resolve_repository_path(
            root, "schemas/catalog.schema.json", expected_kind="file"
        )
        catalog_path = resolve_repository_path(
            root, "contracts/catalog.json", expected_kind="file"
        )
        catalog_schema = load_json(catalog_schema_path)
        Draft202012Validator.check_schema(catalog_schema)
        catalog = load_json(catalog_path)
    except (OSError, json.JSONDecodeError, RepositoryPathError, SchemaError) as exc:
        return [f"schema validation: catalog load failed: {exc}"], 0

    catalog_validator = Draft202012Validator(
        catalog_schema, format_checker=FormatChecker()
    )
    catalog_errors = sorted(
        catalog_validator.iter_errors(catalog),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if catalog_errors:
        return [
            "schema validation: catalog"
            + (
                " at /" + "/".join(str(part) for part in error.absolute_path)
                if error.absolute_path
                else ""
            )
            + f": {error.message}"
            for error in catalog_errors
        ], 0

    for entry in catalog.get("entries", []):
        schema_id = entry.get("schema_id", "<missing-schema-id>")
        try:
            schema_path = resolve_repository_path(
                root, entry["schema_path"], expected_kind="file"
            )
            schema = load_json(schema_path)
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(
                schema, format_checker=FormatChecker()
            )
        except (
            KeyError,
            OSError,
            json.JSONDecodeError,
            RepositoryPathError,
            SchemaError,
        ) as exc:
            errors.append(f"schema validation: {schema_id} schema invalid: {exc}")
            continue

        for selector in entry.get("instances", []):
            try:
                instances = iter_instances(root, selector)
            except (
                KeyError,
                OSError,
                json.JSONDecodeError,
                RepositoryPathError,
                ValueError,
            ) as exc:
                errors.append(f"schema validation: {schema_id} selector failed: {exc}")
                continue
            for label, instance in instances:
                if "pointer" not in selector and isinstance(instance, dict):
                    instance_schema = instance.get("schema")
                    if instance_schema != schema_id:
                        errors.append(
                            f"schema validation: {label} declares {instance_schema}, "
                            f"catalog expects {schema_id}"
                        )
                for error in sorted(
                    validator.iter_errors(instance),
                    key=lambda item: tuple(str(part) for part in item.absolute_path),
                ):
                    location = "/".join(str(part) for part in error.absolute_path)
                    suffix = f" at /{location}" if location else ""
                    errors.append(
                        f"schema validation: {label}{suffix}: {error.message}"
                    )
                validated += 1
    return errors, validated


def main() -> int:
    errors, validated = validate_cataloged_instances(ROOT)
    if errors:
        print("signalbox JSON Schema validation: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"signalbox JSON Schema validation: PASS ({validated} instances)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
