# Publish `getdate-next` to PyPI via Trusted Publishing

## Decisions

- [ ] **Version scheme**: `0.1.0.devYYYYMMDDHHMM` (timestamped dev snapshots)
- [ ] **Smoke-test target**: TestPyPI first, then PyPI
- [ ] **LICENSE file**: add `LICENSE` (GPL-2.0-or-later) at repo root
- [ ] **Auth**: Trusted publishing via GitHub OIDC (PyPI + TestPyPI pending publishers)
- [ ] **Bootstrap**: one-time `twine upload` with project-scoped PyPI token, then rotate
- [ ] **Workflow location**: `.github/workflows/publish.yml` in this repo
- [ ] **GitHub URL**: `https://github.com/jonez734/getdate_next` (PyPI name stays `getdate-next`)
- [ ] **sdist contents**: only `pyproject.toml`, `README.md`, `LICENSE`, `tests/test_getdate.py`
- [ ] **GPG signing**: drop — PEP 740 Sigstore attestations handle provenance
- [ ] **Local mirror**: `/srv/repo/getdate_next/` left untouched

## Phase 0 — Repo hygiene (single PR, no network)

- [ ] Add `LICENSE` (full GPL-2.0-or-later text) at repo root
- [ ] Append `[project.urls]` block to `pyproject.toml` with `Homepage`, `Source`, `Issues` pointing at `https://github.com/jonez734/getdate_next`
- [ ] Add `MANIFEST.in` with explicit allowlist (`include LICENSE README.md pyproject.toml`, `include tests/test_getdate.py`, `prune Makefile SPEC.md demo_moneyday.py .github build dist .pytest_cache .ruff_cache __pycache__`)
- [ ] Remove `sign` target from `Makefile`
- [ ] Remove `sign` from `release` dependency chain in `Makefile` (`release: clean version build rename-sdist`)
- [ ] Verify locally: `make build`, then `unzip -l dist/*.whl` and `tar tzf dist/*.tar.gz` to confirm only the allowed files are included
- [ ] Commit on branch `prep-pypi` and push (do **not** tag)

## Phase 1 — PyPI accounts & pending publishers

- [ ] Log in to `pypi.org`
- [ ] Generate a project-scoped PyPI token (scope: project `getdate-next`), copy to a temp file
- [ ] Register a PyPI pending publisher: project `getdate-next`, owner `jonez734`, repo `getdate_next`, workflow filename `publish.yml`, environment `pypi`
- [ ] Register a TestPyPI pending publisher (`https://test.pypi.org/manage/account/publishing/`): same fields, environment `testpypi`

## Phase 2 — One-time bootstrap upload (TestPyPI → PyPI)

- [ ] Install `twine` (`pip install --user twine` or into `.venv312`)
- [ ] Create `~/.pypirc` (chmod 600) with `[testpypi]` and `[pypi]` sections, both `username = __token__`
- [ ] Run `make release` in `getdate_next/` to build sdist + wheel into `/srv/repo/getdate_next/`
- [ ] Run `python -m twine check /srv/repo/getdate_next/getdate_next-*.tar.gz /srv/repo/getdate_next/getdate_next-*.whl` (must pass)
- [ ] Upload to TestPyPI: `python -m twine upload --repository testpypi /srv/repo/getdate_next/getdate_next-*.tar.gz /srv/repo/getdate_next/getdate_next-*.whl`
- [ ] Verify TestPyPI install: `pip install -i https://test.pypi.org/simple/ getdate-next==0.1.0.devYYYYMMDDHHMM` in a fresh venv, then `python -c "from getdate_next import getdate; print(getdate('next friday'))"`
- [ ] Upload to PyPI: `python -m twine upload --repository pypi /srv/repo/getdate_next/getdate_next-*.tar.gz /srv/repo/getdate_next/getdate_next-*.whl`
- [ ] Delete the bootstrap PyPI token on pypi.org (Account → API tokens → Remove)

## Phase 3 — GitHub Actions workflow

- [ ] Create `.github/workflows/publish.yml` with `build` + `publish` jobs (see plan for full contents)
  - [ ] Trigger on `push` tags matching `v*` and on `workflow_dispatch` with a `target` input (`testpypi` or `pypi`)
  - [ ] `build` job stamps `src/getdate_next/_version.py` from the tag, runs `python -m build`, uploads `dist/` artifact
  - [ ] `publish` job grants `permissions: id-token: write, attestations: write`, sets `environment` from the dispatch input, calls `pypa/gh-action-pypi-publish@release/v1`
  - [ ] Override `repository-url` to `https://test.pypi.org/legacy/` when dispatching to TestPyPI

## Phase 4 — First OIDC-driven release

- [ ] Merge the Phase 0 + Phase 3 PR into the default branch
- [ ] On GitHub: Settings → Environments → create `pypi` and `testpypi` environments
- [ ] Run `make tag` to create `v$(VERSION)` locally
- [ ] Run `make push` to push `v$(VERSION)` to GitHub
- [ ] Watch `Actions → publish`; verify build + publish jobs succeed
- [ ] Sanity-check in a fresh venv: `pip install getdate-next`, run the README examples

## Phase 5 — Cleanup (optional)

- [ ] Add a PyPI version badge to `README.md`
- [ ] Add a `CHANGELOG.md` derived from `/srv/repo/getdate_next/` timestamps
- [ ] Update `Makefile` comment block (`deploy-venv` becomes a developer convenience; production releases flow through GitHub)
