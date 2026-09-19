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
        if not text.strip():
            return []
        
        parts = re.split(r'(\. |\! |\? |\.\n)', text)
        sentences = []
        for i in range(0, len(parts), 2):
            part = parts[i]
            delim = parts[i+1] if i+1 < len(parts) else ""
            sent = (part + delim).strip()
            if sent:
                sentences.append(sent)
                
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunks.append(" ".join(sentences[i:i+self.max_sentences_per_chunk]))
        return chunks


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
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
            
        if not remaining_separators:
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            
        sep = remaining_separators[0]
        next_separators = remaining_separators[1:]
        
        if sep == "":
            parts = list(current_text)
        else:
            parts = current_text.split(sep)
            
        chunks = []
        current_chunk_parts = []
        current_len = 0
        sep_len = len(sep)
        
        for part in parts:
            part_len = len(part)
            if current_len + part_len + (sep_len if current_len > 0 else 0) <= self.chunk_size:
                current_chunk_parts.append(part)
                current_len += part_len + (sep_len if current_len > 0 else 0)
            else:
                if current_chunk_parts:
                    chunks.append(sep.join(current_chunk_parts))
                    current_chunk_parts = []
                    current_len = 0
                
                if part_len > self.chunk_size:
                    sub_chunks = self._split(part, next_separators)
                    chunks.extend(sub_chunks)
                else:
                    current_chunk_parts = [part]
                    current_len = part_len
                    
        return chunks


class HeadingChunker:
    """
    Split text by Markdown headings (#, ##, ###) or section titles (e.g. lines ending with ':').
    If a section exceeds max_chunk_size, recursively split it and prepend the heading
    to preserve context for sub-chunks.
    """

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.recursive_chunker = RecursiveChunker(chunk_size=max_chunk_size)

    def _is_heading(self, line: str) -> bool:
        s = line.strip()
        if not s:
            return False
        # Markdown headings (# Heading)
        if re.match(r"^#{1,6}\s+", s):
            return True
        # Section titles: e.g. "1. ...", "I. ...", "Điều 1...", or short line ending with ":"
        if re.match(r"^(?:[0-9IVXLCDM]+\.|Điều\s+\d+|Mục\s+\d+)\s+", s):
            return True
        if s.endswith(":") and len(s) < 80 and not s.startswith("-") and not s.startswith("–"):
            return True
        return False

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        lines = text.split("\n")
        sections: list[tuple[str, list[str]]] = []
        current_heading = ""
        current_lines: list[str] = []

        for line in lines:
            if self._is_heading(line):
                if current_lines:
                    sections.append((current_heading, current_lines))
                    current_lines = []
                current_heading = line.strip()
                current_lines.append(line)
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_heading, current_lines))

        chunks: list[str] = []
        for heading, s_lines in sections:
            section_text = "\n".join(s_lines).strip()
            if not section_text:
                continue

            if len(section_text) <= self.max_chunk_size:
                chunks.append(section_text)
            else:
                sub_chunks = self.recursive_chunker.chunk(section_text)
                for sc in sub_chunks:
                    sc = sc.strip()
                    if not sc:
                        continue
                    # Attach heading to sub-chunk if not already present
                    if heading and not sc.startswith(heading):
                        chunks.append(f"{heading}\n{sc}")
                    else:
                        chunks.append(sc)

        return chunks if chunks else [text.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(sum(x*x for x in vec_a))
    mag_b = math.sqrt(sum(x*x for x in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=0)
        sentence = SentenceChunker(max_sentences_per_chunk=3)
        recursive = RecursiveChunker(chunk_size=chunk_size)
        
        fixed_chunks = fixed.chunk(text)
        sentence_chunks = sentence.chunk(text)
        recursive_chunks = recursive.chunk(text)
        
        return {
            "fixed_size": {
                "count": len(fixed_chunks),
                "avg_length": sum(len(c) for c in fixed_chunks) / max(1, len(fixed_chunks)),
                "chunks": fixed_chunks
            },
            "by_sentences": {
                "count": len(sentence_chunks),
                "avg_length": sum(len(c) for c in sentence_chunks) / max(1, len(sentence_chunks)),
                "chunks": sentence_chunks
            },
            "recursive": {
                "count": len(recursive_chunks),
                "avg_length": sum(len(c) for c in recursive_chunks) / max(1, len(recursive_chunks)),
                "chunks": recursive_chunks
            }
        }
