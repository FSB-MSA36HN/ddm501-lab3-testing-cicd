"""HTTP integration including lifecycle, schema failures and scoring outages."""
from unittest.mock import Mock

import pytest

import app.main as module


def test_metadata_and_health(test_client):
    assert test_client.get("/health").json() == {"status": "healthy", "model_loaded": True}
    root = test_client.get("/").json()
    assert root["name"] and root["version"] and root["docs"] == "/docs"
    assert test_client.get("/model/info").json()["is_loaded"] is True
    assert test_client.get("/docs").status_code == 200


def test_prediction(test_client, sample_prediction_request):
    response = test_client.post("/predict", json=sample_prediction_request)
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "196" and body["movie_id"] == "242"
    assert 1 <= body["predicted_rating"] <= 5
    assert body["model_version"] == "1.0.0"


def test_batch_matches_single(test_client, sample_batch_request):
    response = test_client.post("/predict/batch", json=sample_batch_request)
    assert response.status_code == 200
    assert response.json()["total_count"] == 3
    assert response.json()["predictions"] == [
        test_client.post("/predict", json=p).json() for p in sample_batch_request["predictions"]
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"movie_id": "1"},
        {"user_id": "1"},
        {"user_id": " ", "movie_id": "2"},
        {"user_id": "x" * 10000, "movie_id": "2"},
        {"user_id": 1, "movie_id": "2"},
    ],
)
def test_reject_invalid_payload(test_client, payload):
    assert test_client.post("/predict", json=payload).status_code == 422


@pytest.mark.parametrize(
    "predictions",
    [[], [{"user_id": "1", "movie_id": "2"}] * 101, [{"user_id": "1", "movie_id": " "}]],
)
def test_reject_invalid_batch(test_client, predictions):
    assert test_client.post("/predict/batch", json={"predictions": predictions}).status_code == 422


def test_http_errors(test_client):
    assert (
        test_client.post(
            "/predict", content="invalid json", headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )
    assert test_client.get("/unknown").status_code == 404
    assert test_client.get("/predict").status_code == 405


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/predict", {"user_id": "1", "movie_id": "2"}),
        ("/predict/batch", {"predictions": [{"user_id": "1", "movie_id": "2"}]}),
    ],
)
def test_unavailable_and_failed_model(test_client, monkeypatch, path, payload):
    monkeypatch.setattr(module, "model", None)
    assert test_client.get("/health").json()["model_loaded"] is False
    assert test_client.post(path, json=payload).status_code == 503
    faulty = Mock(is_loaded=lambda: True, predict=Mock(side_effect=RuntimeError("internal secret")))
    monkeypatch.setattr(module, "model", faulty)
    response = test_client.post(path, json=payload)
    assert response.status_code == 500
    assert "internal secret" not in response.text


@pytest.mark.asyncio
async def test_startup_failure_clears_old_model(monkeypatch):
    previous = module.model
    monkeypatch.setattr(module, "MovieRatingModel", Mock(side_effect=FileNotFoundError("missing")))
    await module.startup_event()
    assert module.model is None
    module.model = previous
