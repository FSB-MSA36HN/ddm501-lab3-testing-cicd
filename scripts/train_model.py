"""Train seeded SVD on the committed MovieLens 100K data; fail quality gate."""
import json
import pickle
from pathlib import Path

import numpy as np
from surprise import SVD, Dataset, Reader
from surprise.model_selection import KFold, cross_validate

BASE = Path(__file__).resolve().parents[1]


def main() -> None:
    data = Dataset.load_from_file(
        str(BASE / "data/u.data"), Reader(line_format="user item rating timestamp", sep="\t")
    )
    model = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=501)
    scores = cross_validate(
        model,
        data,
        measures=["RMSE", "MAE"],
        cv=KFold(n_splits=5, random_state=501, shuffle=True),
        verbose=True,
    )
    metrics = {
        "rmse": float(np.mean(scores["test_rmse"])),
        "mae": float(np.mean(scores["test_mae"])),
        "seed": 501,
        "folds": 5,
        "rows": len(data.raw_ratings),
    }
    if metrics["rmse"] >= 1.0 or metrics["mae"] >= 0.8:
        raise SystemExit(f"Model quality gate failed: {metrics}")
    model.fit(data.build_full_trainset())
    (BASE / "models").mkdir(exist_ok=True)
    with (BASE / "models/svd_model.pkl").open("wb") as stream:
        pickle.dump(model, stream)
    (BASE / "models/metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
