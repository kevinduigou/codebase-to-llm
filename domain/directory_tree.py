from __future__ import annotations

import os
from pathlib import Path
from typing import Final, Iterable, List, Set

from .result import Err, Ok, Result

_DEFAULT_IGNORES: Final[Set[str]] = {
    ".git",
    ".venv",
    "venv",
    ".mypy_cache",
    "__pycache__",
}


def default_ignore_tokens() -> Set[str]:
    """Return a mutable copy of the built‑in ignore tokens."""
    return set(_DEFAULT_IGNORES)


def _gitignore_paths(root: Path) -> Set[str]:
    gitignore_file = root / ".gitignore"
    if not gitignore_file.exists():
        return set()

    # Reading .gitignore without exceptions
    # (Assume UTF‑8 and ignore undecodable bytes)
    patterns: Set[str] = set()
    for line in gitignore_file.read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.add(stripped)
    return patterns


def get_ignore_tokens(root: Path, base_tokens: Iterable[str] | None = None) -> Set[str]:
    """Return the ignore tokens combining the provided list and `.gitignore`."""
    tokens = set(base_tokens or _DEFAULT_IGNORES)
    tokens.update(_gitignore_paths(root))
    return tokens


def should_ignore(path: Path, ignore_tokens: Iterable[str]) -> bool:
    """Return True if the path should be ignored according to the ignore tokens."""
    for token in ignore_tokens:
        if token and token in path.parts:
            return True
    # Ignore .pyc files
    if path.is_file() and path.name.endswith(".pyc"):
        return True
    return False


def _ascii_tree(root: Path, ignore_tokens: Iterable[str]) -> str:
    """Return an ASCII‑art directory tree similar to the `tree` command."""

    lines: List[str] = []
    prefix_stack: List[str] = []

    def _walk(current: Path, level: int) -> None:  # noqa: ANN001
        entries: List[Path] = sorted(
            p for p in current.iterdir() if not should_ignore(p, ignore_tokens)
        )
        for index, entry in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            lines.append("".join(prefix_stack) + connector + entry.name)
            if entry.is_dir():
                prefix_stack.append("    " if index == len(entries) - 1 else "│   ")
                _walk(entry, level + 1)
                prefix_stack.pop()

    lines.append(root.name)
    _walk(root, 0)
    return os.linesep.join(lines)


# The port‑friendly façade


def build_tree(root: Path, ignore_tokens: Iterable[str] | None = None) -> Result[str, str]:
    if not root.exists():
        return Err(f"Directory not found: {root}")
    tokens = get_ignore_tokens(root, ignore_tokens)
    tree_repr = _ascii_tree(root, tokens)
    return Ok(tree_repr)
