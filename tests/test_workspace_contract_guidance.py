"""Deterministic coverage for workspace contract wording cleanup."""

import pytest

from home_ai_cluster import workspace_aware_code


def test_contract_keeps_explanations_inside_final_json_content():
    assert (
        "If the operator asks for an explanation, put that explanation only in the "
        '"content" field of a final JSON response.' in workspace_aware_code._CONTRACT
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
