from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", text)
            if sentence.strip()
        ]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        parts = current_text.split(separator)
        pieces = [
            part + (separator if index < len(parts) - 1 else "")
            for index, part in enumerate(parts)
            if part
        ]
        chunks: list[str] = []
        pending = ""

        for piece in pieces:
            if len(piece) > self.chunk_size:
                if pending.strip():
                    chunks.append(pending.strip())
                chunks.extend(self._split(piece, remaining_separators[1:]))
                pending = ""
            elif len(pending) + len(piece) <= self.chunk_size:
                pending += piece
            else:
                if pending.strip():
                    chunks.append(pending.strip())
                pending = piece

        if pending.strip():
            chunks.append(pending.strip())
        return chunks


class DocumentStructureChunker:
    """Split policy documents at headings and smaller titled subsections.

    The crawler output contains one Markdown title followed by plain-text section
    titles such as ``2. ...``, ``4.1 ...``, ``e. ...`` and ``Bước 1:``.  Each
    returned chunk includes its document title and current parent section, so a
    short subsection keeps enough context to be useful during retrieval.
    """

    MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)([.)])?\s+(.+?)\s*$")
    LETTERED_HEADING = re.compile(r"^([A-Za-z])[.)]\s+(.+?)\s*$")
    STEP_HEADING = re.compile(r"^(Bước\s+\d+)\s*:\s*$", re.IGNORECASE)

    def __init__(self, max_chunk_size: int = 900) -> None:
        self.max_chunk_size = max(100, max_chunk_size)

    @classmethod
    def _heading(cls, line: str) -> tuple[int, str] | None:
        stripped = line.strip()
        if not stripped:
            return None

        markdown = cls.MARKDOWN_HEADING.match(stripped)
        if markdown:
            return len(markdown.group(1)), markdown.group(2).strip()

        numbered = cls.NUMBERED_HEADING.match(stripped)
        if numbered:
            number, delimiter, title = numbered.groups()
            # A numbered list item is normally a full sentence. Section titles in
            # this corpus are short and either upper-case or have no final period.
            is_section_number = delimiter is not None or "." in number
            if is_section_number and len(stripped) <= 120 and not title.endswith("."):
                return number.count(".") + 2, stripped

        lettered = cls.LETTERED_HEADING.match(stripped)
        if lettered and len(stripped) <= 100:
            return 4, stripped

        step = cls.STEP_HEADING.match(stripped)
        if step:
            return 5, stripped

        if len(stripped) <= 100 and stripped.isupper() and any(char.isalpha() for char in stripped):
            return 2, stripped

        return None

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        hierarchy: dict[int, str] = {}
        chunks: list[str] = []
        body_lines: list[str] = []

        def flush() -> None:
            body = "\n".join(body_lines).strip()
            if not body:
                return
            headings = [hierarchy[level] for level in sorted(hierarchy)]
            prefix = "\n> ".join(headings)
            section = f"> {prefix}\n\n{body}" if prefix else body
            chunks.extend(self._split_oversized(section, headings))
            body_lines.clear()

        for raw_line in text.splitlines():
            heading = self._heading(raw_line)
            if heading is None:
                body_lines.append(raw_line)
                continue

            flush()
            level, title = heading
            hierarchy = {key: value for key, value in hierarchy.items() if key < level}
            hierarchy[level] = title

        flush()

        # A document containing only headings should still be represented.
        if not chunks and hierarchy:
            chunks.append("\n> ".join(hierarchy[level] for level in sorted(hierarchy)))
        return chunks

    def _split_oversized(self, section: str, headings: list[str]) -> list[str]:
        if len(section) <= self.max_chunk_size:
            return [section]

        prefix = "\n> ".join(headings)
        prefix = f"> {prefix}\n\n" if prefix else ""
        available = max(100, self.max_chunk_size - len(prefix))
        pieces = RecursiveChunker(chunk_size=available).chunk(
            section.removeprefix(prefix)
        )
        return [f"{prefix}{piece}".strip() for piece in pieces if piece.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=max(1, chunk_size), overlap=0),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(map(len, chunks)) / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
