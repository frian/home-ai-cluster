"""Consistency checks for RFC status, decision, and selected-index metadata."""

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
RFC_DIRECTORY = REPOSITORY_ROOT / "RFC"
RFC_README = RFC_DIRECTORY / "README.md"
ALLOWED_STATUSES = {"Draft", "Accepted", "Rejected", "Superseded"}
STATUS_PATTERN = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
DECISION_PATTERN = re.compile(r"^## Decision$", re.MULTILINE)
RFC_LINK_PATTERN = re.compile(r"\[[^]]+\]\((RFC-\d{4}-[^)]+\.md)\)")


def _status_for(rfc_path: Path) -> str:
    statuses = STATUS_PATTERN.findall(rfc_path.read_text(encoding="utf-8"))
    assert len(statuses) == 1, f"{rfc_path.name} must have exactly one Status field"
    assert statuses[0] in ALLOWED_STATUSES, f"{rfc_path.name} has an invalid status"
    return statuses[0]


def _section_content(document: str, heading: str) -> str:
    start = document.index(heading) + len(heading)
    remainder = document[start:]
    next_heading = re.search(r"^## ", remainder, re.MULTILINE)
    return remainder[: next_heading.start() if next_heading else None]


def test_rfc_status_and_final_decision_are_consistent() -> None:
    for rfc_path in sorted(RFC_DIRECTORY.glob("RFC-*.md")):
        document = rfc_path.read_text(encoding="utf-8")
        status = _status_for(rfc_path)
        decisions = list(DECISION_PATTERN.finditer(document))

        assert decisions, f"{rfc_path.name} must have a ## Decision section"
        final_decision = document[decisions[-1].end() :].strip()
        assert not (
            status in {"Accepted", "Rejected", "Superseded"}
            and final_decision == "Pending."
        ), f"{rfc_path.name} has a stale final Pending decision"


def test_selected_index_links_match_their_rfc_statuses() -> None:
    document = RFC_README.read_text(encoding="utf-8")
    selected_accepted = _section_content(document, "## Selected accepted RFCs")
    rejected = _section_content(document, "## Rejected RFCs")

    for section, expected_status in (
        (selected_accepted, "Accepted"),
        (rejected, "Rejected"),
    ):
        for link in RFC_LINK_PATTERN.findall(section):
            rfc_path = RFC_DIRECTORY / link
            assert rfc_path.is_file(), f"indexed RFC does not exist: {link}"
            assert _status_for(rfc_path) == expected_status
