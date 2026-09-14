"""Deterministic coverage for workspace contract wording cleanup."""

import pytest

from home_ai_cluster import workspace_aware_code


def test_contract_requires_bare_json_without_success_claims():
    assert "NO PROSE BEFORE OR AFTER THE JSON" in workspace_aware_code._CONTRACT
    assert "NO EXPLANATION" in workspace_aware_code._CONTRACT
    assert "DO NOT claim that a file was read, written, created, or listed" in (
        workspace_aware_code._CONTRACT
    )


@pytest.mark.parametrize(
    "content",
    [
        "Changed subtraction to addition.",
        '```json\n{"kind":"final","content":"done"}\n```',
    ],
)
def test_wording_cleanup_does_not_relax_closed_response_grammar(content):
    with pytest.raises((TypeError, ValueError)):
        workspace_aware_code._parse_response(content)
