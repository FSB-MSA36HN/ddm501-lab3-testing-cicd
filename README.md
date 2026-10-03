# DDM501 - Lab 3: Testing & CI/CD for ML Systems

[![CI](https://github.com/thanhhai12/ddm501-lab3-testing-cicd/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhai12/ddm501-lab3-testing-cicd/actions/workflows/ci.yml)

Movie rating prediction with a real Surprise SVD trained on MovieLens 100K.
This lab follows the supplied Lab 3 movie-rating specification; Labs 1 and 2
used credit default risk. All four testing layers and the CI/CD workflows are implemented.

## Reproduce

Python 3.11 and a C++ compiler are required for Surprise 1.1.3.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-build.txt
pip install --no-build-isolation -r requirements.txt -r requirements-dev.txt
python scripts/train_model.py
pytest --cov=app --cov-fail-under=80 --cov-report=html --cov-report=xml
black --check app tests scripts
isort --check-only app tests scripts
flake8 app tests scripts
mypy app
pre-commit install
pre-commit run --all-files
uvicorn app.main:app --port 8000
```

The dataset is committed, so training does not prompt for a download. Use only
trusted local model artifacts: pickle is a Python serialization format.

## Results and submission evidence

73 tests passed locally; application coverage is **100%** (minimum 80%).
Seeded five-fold RMSE **0.936182**, MAE **0.737780**. Training refuses to save
an artifact if RMSE >= 1.0 or MAE >= 0.8. These metrics are out-of-fold;
the final serving artifact is subsequently fitted on all 100,000 ratings.

- [Testing strategy](docs/TESTING_STRATEGY.md)
- [Test output](docs/evidence/pytest.txt), [coverage XML](docs/evidence/coverage.xml)
- [Training output](docs/evidence/training.txt), [metrics](models/metrics.json)
- [Pre-commit output](docs/evidence/pre-commit.txt)
- [GitHub Actions](https://github.com/thanhhai12/ddm501-lab3-testing-cicd/actions)
- CI screenshots are in `docs/evidence/` after the remote run completes.

## API

| Route | Contract |
|---|---|
| `GET /health` | `model_loaded` readiness flag; HTTP 200 alone is not readiness |
| `POST /predict` | Nonblank string IDs, max 50 chars; returns a rating in [1,5] |
| `POST /predict/batch` | 1-100 pairs; same validation and order as single scoring |
| `GET /model/info` | Version, model type and load state |
| `GET /docs` | Interactive OpenAPI documentation |

```bash
curl -s -H 'Content-Type: application/json' \
  -d '{"user_id":"196","movie_id":"242"}' http://localhost:8000/predict
```

Invalid inputs produce 422, unavailable models 503, scoring failures 500 with
no internal exception details. Unknown IDs use SVD's bias/global-mean fallback.

## CI and CD

CI runs on pushes to main/develop, PRs to main and manual dispatch. It checks
Black, isort, Flake8 and mypy; trains a seeded model; enforces the coverage and
model quality gates; uploads HTML/XML/JUnit evidence; builds and smoke-tests
the Docker image using the model artifact from that same run.

CD runs on `v*` tags. It repeats quality gates before publishing an immutable
version tag and `latest` to GHCR using GITHUB_TOKEN. A dependent job runs the
released image and validates health and prediction in **ephemeral staging** on
an Actions runner. This is a real temporary deployment, not a persistent public
production service. No cloud account or paid infrastructure is required.

```bash
git tag v1.0.0
git push origin v1.0.0
# Pull a release; use the previous immutable version tag to roll back.
docker pull ghcr.io/thanhhai12/ddm501-lab3-testing-cicd:v1.0.0
```

For local Docker verification, train first, then:

```bash
docker build -t movie-rating-api:lab3 .
docker run --rm -p 8001:8000 movie-rating-api:lab3
```

The image runs as a non-root user. Its healthcheck uses Python's standard
library and checks model_loaded, so it needs no curl package.

## Data and limitations

MovieLens 100K: 100,000 ratings, 943 users, 1,682 movies. Source and terms are
included in [the original GroupLens README](data/MOVIELENS_README.txt).
The data is for educational use under its original terms. It is not covered
by the repository code license. Source: https://grouplens.org/datasets/movielens/100k/.
Cold-start fallbacks do not personalize unseen users. Full-training known-pair
tests are functionality checks; only the held-out CV gate measures quality.
