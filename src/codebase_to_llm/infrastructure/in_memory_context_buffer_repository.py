from __future__ import annotations

from pathlib import Path
from typing import Final
from typing_extensions import final

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.context_buffer import (
    ContextBuffer,
    ExternalSource,
    File,
    Snippet,
)
from codebase_to_llm.domain.result import Err, Result, Ok


@final
class InMemoryContextBufferRepository(ContextBufferPort):
    """In-memory repository for managing context buffer state."""

    __slots__ = ("_files", "_snippets", "_external_sources")

    def __init__(self) -> None:
        self._context_buffer = ContextBuffer(
            files=[],
            snippets=[],
            external_sources=[],
        )

    def add_file(self, file: File) -> Result[None, str]:
        """Add a file to the context buffer if not already present."""
        new_list_of_files = [file for file in self._context_buffer.get_files()]
        if file.path not in [file_.path for file_ in new_list_of_files]:
            new_list_of_files.append(file)
        self._context_buffer = ContextBuffer(
            files=new_list_of_files,
            snippets=self._context_buffer.get_snippets(),
            external_sources=self._context_buffer.get_external_sources(),
        )
        return Ok(None)

    def remove_file(self, path: Path) -> Result[None, str]:
        """Remove a file from the context buffer."""
        new_list_offiles = [
            file for file in self._context_buffer.get_files() if file.path != path
        ]
        self._context_buffer = ContextBuffer(
            files=new_list_offiles,
            snippets=self._context_buffer.get_snippets(),
            external_sources=self._context_buffer.get_external_sources(),
        )
        return Ok(None)

    def add_snippet(self, snippet: Snippet) -> Result[None, str]:
        """Add a text snippet to the context buffer."""
        new_list_of_snippets = self._context_buffer.get_snippets()
        new_list_of_snippets.append(snippet)
        self._context_buffer = ContextBuffer(
            files=self._context_buffer.get_files(),
            snippets=new_list_of_snippets,
            external_sources=self._context_buffer.get_external_sources(),
        )
        return Ok(None)

    def remove_snippet(self, path: Path, start: int, end: int) -> Result[None, str]:
        """Remove a text snippet from the context buffer."""
        removed_snippet_result = self._context_buffer.remove_snippet(path, start, end)
        if removed_snippet_result.is_err():
            return Err(removed_snippet_result.err() or "Unknown error")
        new_buffer = removed_snippet_result.ok()
        if new_buffer is None:
            return Err("Failed to remove snippet")
        self._context_buffer = new_buffer
        return Ok(None)

    def add_external_source(self, url: str, text: str) -> Result[None, str]:
        """Add an external source to the context buffer."""
        new_list_of_external_sources = [
            es for es in self._context_buffer.get_external_sources() if es.url != url
        ]
        new_list_of_external_sources.append(ExternalSource(url, text))
        self._context_buffer = ContextBuffer(
            files=self._context_buffer.get_files(),
            snippets=self._context_buffer.get_snippets(),
            external_sources=new_list_of_external_sources,
        )
        return Ok(None)

    def remove_external_source(self, url: str) -> Result[None, str]:
        """Remove an external source by URL from the context buffer."""
        new_list_of_external_sources = [
            external_source
            for external_source in self._context_buffer.get_external_sources()
            if external_source.url != url
        ]
        self._context_buffer = ContextBuffer(
            files=self._context_buffer.get_files(),
            snippets=self._context_buffer.get_snippets(),
            external_sources=new_list_of_external_sources,
        )
        return Ok(None)

    def get_files(self) -> list[File]:
        """Get all files in the context buffer."""
        return self._context_buffer.get_files()

    def get_snippets(self) -> list[Snippet]:
        """Get all snippets in the context buffer."""
        return self._context_buffer.get_snippets()

    def get_external_sources(self) -> list[ExternalSource]:
        """Get all external sources in the context buffer."""
        return self._context_buffer.get_external_sources()

    def get_context_buffer(self) -> ContextBuffer:
        """Get the current context buffer as a domain object."""
        # Note: ContextBuffer expects File, Snippet, ExternalSource types
        # Based on usage patterns, these appear to map to Path, Snippet, ExternalSource
        return self._context_buffer

    def clear(self) -> Result[None, str]:
        """Clear all items from the context buffer."""
        self._context_buffer = ContextBuffer(
            files=[],
            snippets=[],
            external_sources=[],
        )
        return Ok(None)

    def is_empty(self) -> bool:
        """Check if the context buffer is empty."""
        return not (
            self._context_buffer.get_files()
            or self._context_buffer.get_snippets()
            or self._context_buffer.get_external_sources()
        )

    def count_items(self) -> int:
        """Get the total number of items in the context buffer."""
        return (
            len(self._context_buffer.get_files())
            + len(self._context_buffer.get_snippets())
            + len(self._context_buffer.get_external_sources())
        )
