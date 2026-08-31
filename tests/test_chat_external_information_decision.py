import json

import pytest
from pydantic import ValidationError

from home_ai_cluster.chat_external_information_decision import (
    DECISION_LABELS,
    DECISION_POLICY,
    ChatExternalInformationDecisionRequest,
)


def test_decision_projects_one_fixed_local_classify_request() -> None:
    question = "  What does \u00e9 mean?\n"

    request = ChatExternalInformationDecisionRequest(
        question=question
    ).classify_request()

    assert request.labels == ["ordinary", "external"]
    assert request.labels == DECISION_LABELS
    assert request.constraints.local_only is True
    assert (
        request.text == f"{DECISION_POLICY}{json.dumps(question, ensure_ascii=False)}"
    )
    assert request.text.startswith(DECISION_POLICY)
    assert json.loads(request.text.removeprefix(DECISION_POLICY)) == question


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "question", "labels": ["other"]},
        {"question": "question", "constraints": {"local_only": False}},
        {"question": "question", "plugin": "plugin"},
        {"question": "question", "provider": "provider"},
        {"question": "question", "runtime": "runtime"},
        {"question": "question", "node": "node"},
        {"question": "question", "credential_hint": "secret"},
        {"question": "question", "extra": True},
        {},
        {"question": "   "},
    ],
)
def test_decision_rejects_any_shape_other_than_one_question(payload: object) -> None:
    with pytest.raises(ValidationError):
        ChatExternalInformationDecisionRequest.model_validate(payload)


def test_decision_accepts_exactly_4096_utf8_bytes() -> None:
    question = "\u00e9" * 2_048

    assert (
        ChatExternalInformationDecisionRequest(question=question).question == question
    )


@pytest.mark.parametrize("question", ["a" * 4_097, "\u00e9" * 2_049])
def test_decision_rejects_questions_over_4096_utf8_bytes(question: str) -> None:
    with pytest.raises(ValidationError):
        ChatExternalInformationDecisionRequest(question=question)
