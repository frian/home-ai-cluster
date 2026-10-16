"""Bounded, offline preparation of untrusted HTML document passages."""

from __future__ import annotations

import re
from html.parser import HTMLParser

MAX_HTML_BYTES = 262_144
MAX_EXTRACTED_TEXT_BYTES = 65_536
MAX_PASSAGE_BYTES = 2_048

_BLOCK_TAGS = frozenset(
    {
        "article",
        "blockquote",
        "dd",
        "div",
        "dt",
        "li",
        "main",
        "p",
        "pre",
        "section",
        "td",
        "th",
    }
)
_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
_IGNORED_TAGS = frozenset(
    {"aside", "footer", "head", "nav", "noscript", "script", "style", "template"}
)
_WORD_RE = re.compile(r"\w+", re.UNICODE)
_SENTENCE_BREAK_RE = re.compile(r"[.!?](?:\s|$)")


def select_passages(html: str, question: str) -> str | None:
    """Return deterministic, QUESTION-relevant passages within the evidence budget.

    ``None`` is a no-result outcome.  This function neither constructs evidence
    nor treats any extracted document text as instruction authority.
    """
    if not isinstance(html, str) or not isinstance(question, str):
        return None
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        return None

    question_words = _words(question)
    if not question_words:
        return None

    try:
        parser = _DocumentTextParser()
        parser.feed(html)
        parser.close()
        passages = _split_passages(parser.passages)
    except (ValueError, UnicodeError):
        return None

    scored = [
        (len(question_words.intersection(_words(passage))), index, passage)
        for index, passage in enumerate(passages)
    ]
    relevant = [item for item in scored if item[0] > 0]
    if not relevant:
        return None

    # Score determines eligibility; original document order determines output.
    ranked = sorted(relevant, key=lambda item: (-item[0], item[1]))
    chosen: list[tuple[int, str]] = []
    used = 0
    for _, index, passage in ranked:
        separator = 2 if chosen else 0
        size = len(passage.encode("utf-8"))
        if used + separator + size <= MAX_PASSAGE_BYTES:
            chosen.append((index, passage))
            used += separator + size

    if not chosen:
        return None
    return "\n\n".join(passage for _, passage in sorted(chosen))


class _DocumentTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.passages: list[str] = []
        self._ignored_depth = 0
        self._heading_depth = 0
        self._parts: list[str] = []
        self._current_heading: str | None = None
        self._extracted_bytes = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag = tag.lower()
        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in _HEADING_TAGS:
            self._flush()
            self._heading_depth += 1
            return
        if tag in _BLOCK_TAGS:
            if self._heading_depth:
                self._heading_depth = 0
                self._flush(heading=True)
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _IGNORED_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in _HEADING_TAGS and self._heading_depth:
            self._heading_depth -= 1
            self._flush(heading=True)
            return
        if tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self._parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush(heading=bool(self._heading_depth))

    def _flush(self, *, heading: bool = False) -> None:
        text = _normalize(" ".join(self._parts))
        self._parts.clear()
        if not text:
            return
        self._extracted_bytes += len(text.encode("utf-8"))
        if self._extracted_bytes > MAX_EXTRACTED_TEXT_BYTES:
            raise ValueError("extracted text exceeds the bounded limit")
        if heading:
            self._current_heading = text
            return
        if self._current_heading:
            text = f"{self._current_heading}\n{text}"
        self.passages.append(text)


def _split_passages(passages: list[str]) -> list[str]:
    return [chunk for passage in passages for chunk in _split_passage(passage)]


def _split_passage(passage: str) -> list[str]:
    if len(passage.encode("utf-8")) <= MAX_PASSAGE_BYTES:
        return [passage]

    chunks: list[str] = []
    remaining = passage
    while remaining:
        prefix = _utf8_prefix(remaining, MAX_PASSAGE_BYTES)
        if len(prefix) == len(remaining):
            chunks.append(prefix)
            break
        boundary = _preferred_boundary(prefix)
        chunk = prefix[:boundary].rstrip()
        if not chunk:
            chunk = prefix
            boundary = len(prefix)
        chunks.append(chunk)
        remaining = remaining[boundary:].lstrip()
    return chunks


def _utf8_prefix(value: str, limit: int) -> str:
    used = 0
    result: list[str] = []
    for character in value:
        size = len(character.encode("utf-8"))
        if used + size > limit:
            break
        result.append(character)
        used += size
    return "".join(result)


def _preferred_boundary(prefix: str) -> int:
    sentence_breaks = list(_SENTENCE_BREAK_RE.finditer(prefix))
    if sentence_breaks:
        return sentence_breaks[-1].end()
    whitespace = prefix.rstrip().rfind(" ")
    return whitespace + 1 if whitespace >= 0 else len(prefix)


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _words(value: str) -> set[str]:
    return {word.casefold() for word in _WORD_RE.findall(value)}
