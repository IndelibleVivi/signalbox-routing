"""Hermetic resolution for repository-owned authority paths."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Literal


ExpectedKind = Literal["any", "file", "directory"]
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


class RepositoryPathError(ValueError):
    """Raised when an authority path is not contained by the repository."""


def _require_inside(root: Path, candidate: Path, raw: str) -> Path:
    root_resolved = root.resolve()
    resolved = candidate.resolve(strict=False)
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise RepositoryPathError(f"path escapes repository: {raw}")
    return resolved


def resolve_repository_path(
    root: Path,
    raw: object,
    *,
    base: Path | None = None,
    expected_kind: ExpectedKind = "any",
    allow_parent: bool = False,
) -> Path:
    """Resolve one path only when its normalized target remains inside ``root``."""

    if not isinstance(raw, str) or not raw:
        raise RepositoryPathError("path must be a non-empty repository-relative string")
    if "\\" in raw:
        raise RepositoryPathError(f"path must use repository-relative POSIX syntax: {raw}")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or WINDOWS_ABSOLUTE.match(raw):
        raise RepositoryPathError(f"path must be repository-relative: {raw}")
    if not allow_parent and ".." in relative.parts:
        raise RepositoryPathError(f"parent traversal is forbidden: {raw}")

    root_resolved = root.resolve()
    base_path = base.resolve() if base is not None else root_resolved
    _require_inside(root_resolved, base_path, str(base_path))
    resolved = _require_inside(root_resolved, base_path / Path(*relative.parts), raw)
    if expected_kind == "file" and not resolved.is_file():
        raise RepositoryPathError(f"repository file does not resolve: {raw}")
    if expected_kind == "directory" and not resolved.is_dir():
        raise RepositoryPathError(f"repository directory does not resolve: {raw}")
    if expected_kind == "any" and not resolved.exists():
        raise RepositoryPathError(f"repository path does not resolve: {raw}")
    return resolved


def resolve_repository_glob(root: Path, raw: object) -> list[Path]:
    """Expand one repository-relative glob without allowing path escape."""

    if not isinstance(raw, str) or not raw:
        raise RepositoryPathError("glob must be a non-empty repository-relative string")
    if "\\" in raw:
        raise RepositoryPathError(f"glob must use repository-relative POSIX syntax: {raw}")
    pattern = PurePosixPath(raw)
    if pattern.is_absolute() or WINDOWS_ABSOLUTE.match(raw) or ".." in pattern.parts:
        raise RepositoryPathError(f"glob must be repository-relative: {raw}")
    matches = sorted(root.glob(raw))
    if not matches:
        raise RepositoryPathError(f"glob has no repository files: {raw}")
    files = [
        _require_inside(root, candidate, raw)
        for candidate in matches
        if candidate.is_file()
    ]
    if not files:
        raise RepositoryPathError(f"glob has no repository files: {raw}")
    return files
