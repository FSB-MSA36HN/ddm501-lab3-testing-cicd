# Testing strategy - DDM501 Lab 3

## Scope and connection to earlier labs

Lab 1 established serving contracts; Lab 2 made training reproducible and gated
model promotion. Lab 3 applies the same discipline to the movie-rating starter
explicitly required by its PDF: prevent broken code, bad data, regressions and
unvalidated artifacts from reaching a deployment.

## Test pyramid and risk coverage

| Layer | File | Risks addressed |
|---|---|---|
| Unit | tests/unit/test_model.py | Missing/corrupt artifacts, unloaded state, rounding/clipping, input IDs, singleton lifecycle, batch order |
| Schema | tests/unit/test_schemas.py | Missing/blank/incorrectly typed or long IDs; batch boundaries 0/100/101; output rating boundaries and nonfinite values |
| Integration | tests/integration/test_api.py | Startup executes; metadata; single/batch agreement; 404/405/422; 503 when unavailable; 500 on inference failure without leaking internals |
| Data | tests/data/test_data_quality.py | Whole-file schema, no nulls, positive IDs/timestamps, valid rating range, distribution, entity counts, duplicate pairs and minimum user history |
| Behavioral | tests/model/test_model_behavior.py | Repeated-input/order/whitespace invariance, cold-start fallback, known-pair minimum functionality, learned preference direction, out-of-fold RMSE/MAE |
| Container | .github/workflows/ci.yml | Actual image build, readiness and prediction through HTTP |

Real-model tests never skip if the artifact is missing: CI must train before
running them. TestClient is a context manager to execute startup. Unit tests
use narrowly scoped monkeypatches for error paths; integration and behavioral
tests load the actual trained artifact. Data tests read all 100,000 rows rather
than a synthetic fixture that could conceal a broken input file.

## Behavioral testing decisions

Invariance compares corresponding batch positions after reversing the order;
a set comparison could conceal duplicate loss or pair mismatches. Whitespace
normalization is checked both at the schema boundary and directly in the wrapper.
For an unseen user, SVD's prediction is global mean plus learned movie bias.
The directional test compares the 30 highest-bias and 30 lowest-bias movies:
this encodes a defensible direction without assuming that arbitrary numerical
IDs have a monotonic relationship to ratings. A known-pair tolerance is a basic
functionality check, not a substitute for held-out evaluation.

## Quality gates and reproducibility

Five folds use shuffled KFold(seed=501); SVD also fixes random_state=501.
RMSE < 1.0 and MAE < 0.8 are enforced before the model is saved. Measured values:
RMSE 0.9361820512; MAE 0.7377801472. Final training uses the full dataset only
after CV. Dataset and dependency versions are recorded in the repository.
Coverage is scoped to app, with a hard 80% floor. Measured locally: 73 passed,
100% statement coverage. XML and terminal output are committed; CI uploads
HTML, XML and JUnit reports for independent inspection.

## Release controls

Pre-commit checks formatting, import order, linting, YAML/JSON, merge markers,
private keys and oversized additions; mypy checks app. CI repeats quality gates
without relying on developers installing hooks. The Docker job consumes the
same artifact trained in the quality job. CD repeats gates on the tagged commit
and publishes versioned GHCR artifacts. Ephemeral staging validates the released
image, then cleans it up. Rollback uses the prior immutable image tag.

## Limits

100% statement coverage does not imply every path or behavior is correct.
Checks do not prove fairness, accuracy on future data, persistent cloud deployment
or production capacity. Surprise pickle artifacts are trusted build outputs.
MovieLens data retains GroupLens's original usage terms. No fake CI screenshots
or training-set accuracy claims are used as validation evidence.
