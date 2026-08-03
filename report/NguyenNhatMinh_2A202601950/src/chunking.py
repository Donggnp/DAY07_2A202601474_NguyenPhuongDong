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
        if not text:
            return []

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        limit = self.max_sentences_per_chunk
        return [" ".join(sentences[index : index + limit]) for index in range(0, len(sentences), limit)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        pieces = self._split(text, self.separators)
        return [piece.strip() for piece in pieces if piece.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: already short enough.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: no separators left (or empty separator) -> fixed-size cut.
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator, *rest = remaining_separators

        # Separator not present here -> try the next one on the same text.
        if separator not in current_text:
            return self._split(current_text, rest)

        parts = current_text.split(separator)
        chunks: list[str] = []
        current = ""
        for part in parts:
            candidate = f"{current}{separator}{part}" if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current)

            if len(part) <= self.chunk_size:
                current = part
            else:
                # Part itself is still too long: recurse with the next separator.
                chunks.extend(self._split(part, rest))
                current = ""

        if current:
            chunks.append(current)
        return chunks


class HeadingChunker:
    """
    Custom strategy for policy documents structured with Markdown headings (## ...).

    Rationale: each K4 policy document (returns, payment, shipping, privacy, seller
    rules) is authored as a list of self-contained sections under a heading — the
    heading itself IS the semantic unit boundary, so splitting there (instead of by
    a fixed character count) keeps each chunk on a single topic. Sections longer than
    max_chunk_size are handed to RecursiveChunker, and the original heading is
    re-prefixed onto every resulting sub-chunk so it doesn't lose its context.
    """

    HEADING_PATTERN = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)

    def __init__(self, max_chunk_size: int = 400) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        matches = list(self.HEADING_PATTERN.finditer(text))
        if not matches:
            # No heading structure found: fall back to recursive splitting.
            return RecursiveChunker(chunk_size=self.max_chunk_size).chunk(text)

        sections: list[str] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(preamble)
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[match.start() : end].strip()
            if section:
                sections.append(section)

        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue

            lines = section.split("\n", 1)
            heading = lines[0] if lines[0].startswith("#") else ""
            for sub_chunk in RecursiveChunker(chunk_size=self.max_chunk_size).chunk(section):
                if heading and not sub_chunk.startswith(heading):
                    chunks.append(f"{heading}\n{sub_chunk}")
                else:
                    chunks.append(sub_chunk)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            avg_length = sum(len(c) for c in chunks) / len(chunks) if chunks else 0.0
            result[name] = {
                "count": len(chunks),
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return result
