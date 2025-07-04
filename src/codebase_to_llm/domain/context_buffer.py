from typing import Callable, final


from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.domain.result import Err, Ok, Result


@dataclass
class File:
    path: Path
    content: str

    @classmethod
    def try_from_path(cls, path: Path) -> Result["File", str]:
        try:
            with open(path, "r") as file:
                content = file.read()
            return Ok(File(path, content))
        except Exception as e:
            return Err(str(e))


@dataclass
class Snippet:
    path: Path
    start: int
    end: int
    content: str

    @classmethod
    def try_create_from_path(
        cls, path: Path, start: int, end: int, content: str
    ) -> Result["Snippet", str]:
        try:
            with open(path, "r") as file:
                lines = file.readlines()
                # Only keep the lines between start and end
                snippet_content = "".join(lines[start - 1 : end])
            return Ok(Snippet(path, start, end, snippet_content))
        except Exception as e:
            return Err(str(e))


@dataclass
class ExternalSource:
    url: str
    content: str
    is_youtube_transcript: bool

    @classmethod
    def try_from_url(
        cls, url: str, get_text_from_url: Callable[[str], Result[str, str]]
    ) -> Result["ExternalSource", str]:
        result = get_text_from_url(url)
        if result.is_err():
            return Err(result.err() or "Unknown error")
        text = result.ok() or ""
        is_youtube_transcript = url.startswith(
            "https://www.youtube.com/"
        ) or url.startswith("https://youtu.be/")
        return Ok(ExternalSource(url, text, is_youtube_transcript))


@final
class ContextBuffer:
    """Immutable value object representing a context buffer."""

    __slots__ = ("_files", "_snippets", "_external_sources")

    def __init__(
        self,
        files: list[File],
        snippets: list[Snippet],
        external_sources: list[ExternalSource],
    ) -> None:
        self._files = files
        self._snippets = snippets
        self._external_sources = external_sources

    def add_file(self, file: File) -> Result[None, str]:
        list_of_file_path = [file_.path for file_ in self._files]
        if file.path in list_of_file_path:
            return Err("File already in the context buffer")
        self._files.append(file)
        return Ok(None)

    def remove_file(self, file: File) -> Result[None, str]:
        if file in self._files:
            self._files.remove(file)
        return Ok(None)

    def add_snippet(self, snippet: Snippet) -> Result[None, str]:
        if snippet in self._snippets:
            return Err("Snippet already in the context buffer")
        self._snippets.append(snippet)
        return Ok(None)

    def remove_snippet(
        self, path: Path, start: int, end: int
    ) -> Result["ContextBuffer", str]:
        for snippet_ in self._snippets:
            if (
                snippet_.path.resolve() == path.resolve()
                and snippet_.start == start
                and snippet_.end == end
            ):
                new_snippets = self._snippets.copy()
                new_snippets.remove(snippet_)
                return Ok(
                    ContextBuffer(self._files, new_snippets, self._external_sources)
                )
        return Err("Snippet not found in the context buffer")

    def add_external_source(self, external_source: ExternalSource) -> Result[None, str]:
        if external_source.url in [es.url for es in self._external_sources]:
            return Err("External source already in the context buffer")
        self._external_sources.append(external_source)
        return Ok(None)

    def remove_external_source(self, url: str) -> Result[None, str]:
        self._external_sources = [
            source for source in self._external_sources if source.url != url
        ]
        return Ok(None)

    def get_files(self) -> list[File]:
        return self._files

    def get_snippets(self) -> list[Snippet]:
        return self._snippets

    def get_external_sources(self) -> list[ExternalSource]:
        return self._external_sources
