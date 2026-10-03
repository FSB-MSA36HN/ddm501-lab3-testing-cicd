"""Wrapper contracts, artifact failures and deterministic prediction boundaries."""
import pickle
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import app.model as module
from app.model import MovieRatingModel


def test_loaded_model(trained_model):
    assert trained_model.is_loaded() is True
    assert trained_model.model is not None
    assert isinstance(trained_model.predict("196", "242"), float)


@pytest.mark.parametrize("value,expected", [(-10.0, 1.0), (9.0, 5.0), (3.456, 3.46)])
def test_rounding_and_clipping(trained_model, monkeypatch, value, expected):
    monkeypatch.setattr(
        trained_model, "model", Mock(predict=lambda *args: SimpleNamespace(est=value))
    )
    assert trained_model.predict("196", "242") == expected


def test_batch_preserves_order(trained_model):
    pairs = [("196", "242"), ("186", "302"), ("22", "377")]
    results = trained_model.predict_batch(pairs)
    assert isinstance(results, list)
    assert results == [trained_model.predict(*pair) for pair in pairs]
    assert all(isinstance(x, float) and 1 <= x <= 5 for x in results)
    assert trained_model.predict_batch([]) == []


@pytest.mark.parametrize("method,args", [("predict", ("1", "2")), ("predict_batch", ([],))])
def test_unloaded_model_fails(trained_model, monkeypatch, method, args):
    monkeypatch.setattr(trained_model, "model", None)
    assert trained_model.is_loaded() is False
    with pytest.raises(RuntimeError, match="not loaded"):
        getattr(trained_model, method)(*args)


@pytest.mark.parametrize("user,movie", [(None, "2"), ("", "2"), ("1", " "), (1, "2")])
def test_invalid_ids_fail(trained_model, user, movie):
    with pytest.raises(ValueError):
        trained_model.predict(user, movie)


def test_missing_artifact(tmp_path):
    with pytest.raises(FileNotFoundError):
        MovieRatingModel(str(tmp_path / "missing.pkl"))


def test_corrupt_artifact(tmp_path):
    path = tmp_path / "bad.pkl"
    path.write_bytes(b"broken artifact")
    with pytest.raises(pickle.UnpicklingError):
        MovieRatingModel(str(path))


def test_singleton_reset():
    module.reset_model()
    first = module.get_model()
    assert module.get_model() is first
    module.reset_model()
    assert module.get_model() is not first
    module.reset_model()
