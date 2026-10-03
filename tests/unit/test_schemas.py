"""Validate identical contracts for single and batch requests."""
import pytest
from pydantic import ValidationError

from app.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    ErrorResponse,
    HealthResponse,
    PredictionItem,
    PredictionRequest,
    PredictionResponse,
)


@pytest.mark.parametrize("schema", [PredictionRequest, PredictionItem])
def test_strip_ids(schema):
    assert schema(user_id=" 196 ", movie_id="242 ").model_dump() == {
        "user_id": "196",
        "movie_id": "242",
    }


@pytest.mark.parametrize("schema", [PredictionRequest, PredictionItem])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"user_id": "1"},
        {"movie_id": "2"},
        {"user_id": "", "movie_id": "2"},
        {"user_id": " ", "movie_id": "2"},
        {"user_id": "1", "movie_id": " "},
        {"user_id": None, "movie_id": "2"},
        {"user_id": 1, "movie_id": "2"},
        {"user_id": "x" * 51, "movie_id": "2"},
    ],
)
def test_invalid_request(schema, payload):
    with pytest.raises(ValidationError):
        schema(**payload)


@pytest.mark.parametrize("rating", [1.0, 3.5, 5.0])
def test_response_bounds(rating):
    response = PredictionResponse(
        user_id="1", movie_id="2", predicted_rating=rating, model_version="1.0.0"
    )
    assert response.predicted_rating == rating
    assert BatchPredictionResponse(predictions=[response], total_count=1).total_count == 1


@pytest.mark.parametrize("rating", [0.99, 5.01, float("nan"), float("inf")])
def test_response_invalid_rating(rating):
    with pytest.raises(ValidationError):
        PredictionResponse(
            user_id="1", movie_id="2", predicted_rating=rating, model_version="1.0.0"
        )


@pytest.mark.parametrize("count", [0, 101])
def test_batch_limits(count):
    with pytest.raises(ValidationError):
        BatchPredictionRequest(predictions=[{"user_id": "1", "movie_id": "2"}] * count)


def test_max_batch_and_health():
    assert (
        len(
            BatchPredictionRequest(
                predictions=[{"user_id": "1", "movie_id": "2"}] * 100
            ).predictions
        )
        == 100
    )
    assert HealthResponse(status="healthy", model_loaded=True).model_loaded is True
    assert ErrorResponse(detail="failure").error_code == "UNKNOWN_ERROR"
