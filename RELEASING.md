# Releasing muriel (Python SDK)

Releases publish to PyPI from GitHub Actions (`.github/workflows/publish.yml`)
when a GitHub Release is published, using PyPI Trusted Publishing (no token).

## Every release

1. Bump the version in **two** places, the same:
   - `pyproject.toml` → `version`
   - `muriel/__init__.py` → `__version__`
2. Check locally: `python -m pytest -q tests`
3. Commit and push to `main`.
4. On GitHub → muriel-sdk-python → Releases → **Draft a new release**:
   tag `vX.Y.Z` (must equal the version, with a `v`), target `main` →
   **Publish release**.
5. Watch Actions → **publish**, then `pip index versions muriel` or check
   pypi.org (can take a minute or two).

## What the workflow does

- **build**: installs, runs the tests, checks both version strings match the
  tag, builds the sdist and wheel, runs `twine check`.
- **publish** (environment `pypi`, `id-token: write`): uploads with
  `pypa/gh-action-pypi-publish`.

## One-time setup (done)

pypi.org → the `muriel` project → Publishing → GitHub publisher: owner
`Muriel-AI-Inc`, repository `muriel-sdk-python`, workflow `publish.yml`,
environment `pypi`.

## Errors seen

| Error | Fix |
|---|---|
| `pyproject version X != tag vY`, or the `__version__` check fails | Fix the version strings, delete the release and tag, release again. |
| "File already exists" on upload | PyPI never accepts the same version twice; bump the version. |

## History

- **0.2.8** (2026-10-21): published by the workflow without problems.
