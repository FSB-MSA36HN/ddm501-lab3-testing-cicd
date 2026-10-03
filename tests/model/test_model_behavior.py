"""Real SVD invariance, cold-start, learned-direction and held-out quality gates."""
import json
from pathlib import Path

import numpy as np
import pytest


def test_repeat_and_order_invariance(trained_model):
    pairs = [("196", "242"), ("186", "302"), ("196", "242")]
    first = trained_model.predict_batch(pairs)
    assert first == trained_model.predict_batch(pairs)
    assert first == trained_model.predict_batch(pairs[::-1])[::-1]
    assert first[0] == first[2]
    assert trained_model.predict(" 196 ", "242 ") == first[0]


@pytest.mark.parametrize("user,movie", [("196", "242"), ("186", "302"), ("22", "377")])
def test_known_pairs(trained_model, user, movie):
    actual = {("196", "242"): 3, ("186", "302"): 3, ("22", "377"): 1}
    assert abs(trained_model.predict(user, movie) - actual[user, movie]) < 1.5


@pytest.mark.parametrize(
    "user,movie", [("new_user", "242"), ("196", "new_movie"), ("new_user", "new_movie")]
)
def test_cold_start(trained_model, user, movie):
    assert 1 <= trained_model.predict(user, movie) <= 5


def test_unknown_both_uses_global_mean(trained_model):
    expected = round(trained_model.model.trainset.global_mean, 2)
    assert trained_model.predict("new_user", "new_movie") == expected


def test_directional_movie_preference(trained_model):
    # For an unseen user SVD uses the global mean plus the learned movie bias.
    # Compare groups, avoiding an unjustified monotonic claim about arbitrary IDs.
    svd = trained_model.model
    indices = np.argsort(svd.bi)
    low, high = indices[:30], indices[-30:]
    train = svd.trainset
    low_scores = [trained_model.predict("new_user", train.to_raw_iid(int(i))) for i in low]
    high_scores = [trained_model.predict("new_user", train.to_raw_iid(int(i))) for i in high]
    assert np.mean(high_scores) > np.mean(low_scores) + 0.5


def test_out_of_fold_performance_gate():
    metrics = json.loads((Path(__file__).resolve().parents[2] / "models/metrics.json").read_text())
    assert metrics["rows"] == 100000 and metrics["folds"] == 5
    assert metrics["rmse"] < 1.0 and metrics["mae"] < 0.8
