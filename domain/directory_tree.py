from __future__ import annotations

import os
from pathlib import Path
from typing import Final, Iterable, List, Set
import re
import fnmatch
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


def get_ignore_tokens(root: Path, base_tokens: Iterable[str] | None = None) -> Set[Pattern]:
    """Convert glob-style ignore tokens and .gitignore entries into compiled regex patterns."""
    raw_tokens = set(base_tokens or _DEFAULT_IGNORES)
    raw_tokens.update(_gitignore_paths(root))

    regex_patterns = {re.compile(fnmatch.translate(token)) for token in raw_tokens}
    return regex_patterns


def should_ignore(path: Path, ignore_patterns: Iterable[str]) -> bool:
    """Return True if the path matches any of the ignore regex patterns."""
    normalized_path = str(path.as_posix())
    for pattern in ignore_patterns:
        if pattern.search(normalized_path):
            return True
    # Also ignore .pyc files
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
