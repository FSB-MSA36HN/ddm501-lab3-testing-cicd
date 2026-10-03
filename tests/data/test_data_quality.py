"""Validate the entire committed training dataset, not only hand-written fixtures."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def ratings():
    return pd.read_csv(
        Path(__file__).resolve().parents[2] / "data/u.data",
        sep="\t",
        names=["user_id", "movie_id", "rating", "timestamp"],
    )


def test_schema_and_completeness(ratings):
    assert ratings.shape == (100000, 4)
    assert not ratings.isna().any().any()
    assert all(pd.api.types.is_integer_dtype(ratings[col]) for col in ratings)
    assert (ratings[["user_id", "movie_id", "timestamp"]] > 0).all().all()


def test_rating_range_and_distribution(ratings):
    assert ratings.rating.between(1, 5).all()
    assert set(ratings.rating) == {1, 2, 3, 4, 5}
    assert 2 <= ratings.rating.mean() <= 4.5
    assert np.isfinite(ratings.rating.std()) and ratings.rating.std() > 0.5


def test_entities_and_unique_pairs(ratings):
    assert ratings.user_id.nunique() == 943
    assert ratings.movie_id.nunique() == 1682
    assert not ratings.duplicated(["user_id", "movie_id"]).any()
    assert ratings.groupby("user_id").size().min() >= 20
