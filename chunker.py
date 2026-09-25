"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def fixed_size_split(
    documents: list[Document],
    chunk_size: int = 300,
    overlap: int = 40,
) -> list[Chunk]:
    """
    Fixed-size character window chunker that snaps both ends to sentence boundaries.

    Works like fallback_split but instead of cutting at exact character counts,
    snaps each chunk's end to the nearest '.', '!', or '?' (searching backward
    first so we don't overshoot chunk_size, then forward if the window contains
    no punctuation), and snaps each subsequent chunk's start forward to the
    beginning of the next complete sentence after the overlap point.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    def snap_end(text: str, start: int, target: int) -> int:
        # Backward search bounded by start so we never land before the chunk start.
        for i in range(min(target, len(text) - 1), start - 1, -1):
            if text[i] in ".!?":
                return i + 1
        # No punctuation in the window — search forward from target.
        for i in range(target, len(text)):
            if text[i] in ".!?":
                return i + 1
        return len(text)

    def snap_start(text: str, pos: int) -> int:
        # If pos is already right after sentence-ending punctuation, just skip whitespace.
        if pos <= 0:
            return 0
        j = pos - 1
        while j >= 0 and text[j].isspace():
            j -= 1
        if j < 0 or text[j] in ".!?":
            i = pos
            while i < len(text) and text[i].isspace():
                i += 1
            return i
        # Mid-sentence: advance to the character after the next sentence-ender.
        for k in range(pos, len(text)):
            if text[k] in ".!?":
                nxt = k + 1
                while nxt < len(text) and text[nxt].isspace():
                    nxt += 1
                return nxt
        return pos  # No further boundary — use pos as-is.

    chunks: list[Chunk] = []
    for doc in documents:
        text = doc.text
        if not text.strip():
            continue
        start = 0
        index = 0
        while start < len(text):
            end = snap_end(text, start, start + chunk_size)
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fixed_size_split",
                    )
                )
                index += 1
            if end >= len(text):
                break
            nxt = snap_start(text, max(0, end - overlap))
            # Always advance past the current start to prevent infinite loops.
            start = nxt if nxt > start else end

    return chunks


def paragraph_split(
    documents: list[Document],
    min_para_len: int = 40,
    overlap: int = 40,
) -> list[Chunk]:
    """
    Paragraph-aware chunker.

    Splits each document on blank lines, merges paragraphs shorter than
    *min_para_len* into their neighbour, then prepends *overlap* trailing
    characters from the previous chunk so details near a paragraph boundary
    stay retrievable from either side.
    """
    import re

    chunks: list[Chunk] = []
    for doc in documents:
        raw = re.split(r"\n{2,}", doc.text)
        paras = [p.strip() for p in raw if p.strip()]

        # Merge short paragraphs forward; if the last is still short, merge backward.
        merged: list[str] = []
        i = 0
        while i < len(paras):
            para = paras[i]
            if len(para) < min_para_len and i + 1 < len(paras):
                merged.append(para + "\n\n" + paras[i + 1])
                i += 2
            else:
                merged.append(para)
                i += 1
        if len(merged) > 1 and len(merged[-1]) < min_para_len:
            tail = merged.pop()
            merged[-1] += "\n\n" + tail

        # Emit chunks, prepending a short tail from the raw previous paragraph.
        for idx, text in enumerate(merged):
            if idx > 0:
                prev_text = merged[idx - 1]
                # Walk back to the start of the last complete sentence.
                match = re.search(r'.*[.!?]\s+', prev_text, re.DOTALL)
                raw_tail = prev_text[match.end():] if match else prev_text
                prev_tail = raw_tail.strip()
                text = (prev_tail + "\n\n" + text) if prev_tail else text
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=idx,
                    produced_by="chunker.py::paragraph_split",
                )
            )

    return chunks


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents into chunks. ⚠️ REPLACE THE BODY OF THIS IN MILESTONE 3.

    Right now it just calls the fallback. That is the plain, generic behaviour
    the brief is talking about.

    When you write your own strategy, set `produced_by` to
    "chunker.py::split_documents" so your README's Sample Chunks section names
    the right function. `app.py chunks` prints that string for you.

    Things worth thinking about before you write any code:
      - Are your documents short posts or long guides?
      - Is the useful information in one sentence, or spread over a paragraph?
      - Would splitting on paragraph breaks keep more thoughts intact than
        splitting on a character count?
    """
    return fixed_size_split(documents)


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
