# Lab 3 - Submission requirements

Source: DDM501_Lab3_Testing_CICD.pdf, sections 5.1-5.3.

| Required deliverable | Implementation / evidence | Status |
|---|---|---|
| Unit tests | tests/unit/test_model.py, tests/unit/test_schemas.py | Complete |
| Integration tests | tests/integration/test_api.py | Complete |
| Data validation tests | tests/data/test_data_quality.py, whole MovieLens 100K dataset | Complete |
| Behavioral tests | tests/model/test_model_behavior.py: invariance, directional, minimum functionality, quality gate | Complete |
| Working CI | .github/workflows/ci.yml; quality and Docker jobs passed | Complete |
| CD configured | .github/workflows/cd.yml; tag-triggered GHCR publication and ephemeral staging | Complete; release execution pending GitHub write access |
| Pre-commit and lint configuration | .pre-commit-config.yaml, .flake8, pyproject.toml | Complete |
| At least 80% coverage | docs/evidence/coverage.xml; 73 tests, 100% app coverage | Complete |
| Testing strategy | docs/TESTING_STRATEGY.md | Complete |
| Updated README and CI badge | README.md | Complete |
| Screenshot of passing CI workflows | docs/evidence/github-ci-success.jpg, actual GitHub run | Complete locally; screenshot upload pending GitHub write access |
| Repository link | https://github.com/thanhhai12/ddm501-lab3-testing-cicd | Public, CI green |

Verified passing run: https://github.com/thanhhai12/ddm501-lab3-testing-cicd/actions/runs/37105620946
Test and coverage artifacts are also downloadable from that run when signed in.
The screenshot records commit ad26edd; it does not claim a later documentation
commit was tested by that same run. Docker smoke tests are complete and local
containers were stopped after verification.

Submit the repository URL through LMS. This package does not submit to LMS on
behalf of the student or invent team-member names.
