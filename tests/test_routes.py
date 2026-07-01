from fastapi.testclient import TestClient

from home_ai_cluster.main import create_app


def test_chat_endpoint_returns_cluster_result_json() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "content": "Hello",
        "adapter": "in-memory",
        "model": None,
    }


def test_chat_endpoint_uses_last_user_message() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat",
        json={
            "messages": [
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "Middle"},
                {"role": "user", "content": "Second"},
            ],
            "capability": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Second"


def test_chat_endpoint_rejects_unsupported_capability() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "embeddings",
        },
    )

    assert response.status_code == 404
    assert "embeddings" in response.json()["detail"]
