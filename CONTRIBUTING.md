# Contributing to opencode-trading

Thanks for your interest in improving the OpenCode ↔ TradingCodex adapter.
This guide covers how to file bugs, suggest features, and submit pull
requests.

## Reporting bugs

Open a GitHub issue at
<https://github.com/sigco3111/opencode-trading/issues/new>. Please include:

- The exact command you ran (e.g. `opencode-trading convert --workspace ~/foo`)
- The full traceback (do not paste screenshots of terminal output)
- Your Python version (`python --version`) and `opencode-trading --version`
- The TradingCodex version (if you used `convert`), e.g. `pip show tradingcodex`
- A minimal `tests/fixtures/sample-tcx-workspace`-shaped reproducer if possible

## Suggesting features

Open a GitHub issue with the `enhancement` label. Describe:

- The user-facing problem (not the proposed solution)
- The use case (who benefits, how often)
- Any alternatives you considered
- Whether you are willing to submit a PR

## Submitting pull requests

1. **Fork** the repo and create a topic branch from `main`:

   ```bash
   git checkout -b feat/<short-topic>
   ```

2. **Install dev deps** in a virtualenv:

   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Write tests first** (TDD). Every new behavior needs a failing test in
   `tests/test_<module>.py` before the implementation lands.

4. **Run the full QA suite** locally — all must pass:

   ```bash
   ruff check src tests
   ruff format --check src tests
   mypy src --strict
   pytest -v
   ```

5. **Commit** with a [Conventional Commits](https://www.conventionalcommits.org/)
   prefix: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `perf:`.
   Scope with a module name when relevant: `feat(attach): …`.

6. **Push** and open the PR against `main`. Fill in the PR template:
   what changed, why, how it was tested, any breaking change.

## Coding style

- **PEP 8** + the project's `ruff` config (`line-length = 100`, rules
  `E, F, I, W, B, UP`).
- **Type hints** on every public function and method. The project runs
  `mypy src --strict`; the PR will be blocked on any new strict-mode error.
- **No new runtime dependencies** unless absolutely necessary. The adapter
  is zero-deps by design; justify any addition in the PR description.
- **Public API stability** — once a name is in the docs/README, it is
  part of the contract. Renames require a deprecation shim and a CHANGELOG
  entry.

## Test requirements

- New behavior → new test in the matching `tests/test_<module>.py`.
- Bug fixes → a regression test that fails on `main` and passes after the fix.
- Test files use `from __future__ import annotations`, `pytest` style, and
  `tmp_path: Path` for filesystem fixtures.
- No `unittest.mock` for filesystem or JSON — use `tmp_path` and real
  read/write to keep tests honest.
- The full suite must stay green; current baseline is **131 tests**.

## Release process

Maintainers cut releases by:

1. Updating `CHANGELOG.md` with a new `## [X.Y.Z]` section.
2. Bumping `version` in `pyproject.toml`.
3. Committing `chore(release): bump to vX.Y.Z`.
4. Tagging `git tag -a vX.Y.Z -m "vX.Y.Z: <one-line summary>"`.
5. Pushing the tag → GitHub Actions `.github/workflows/release.yml`
   builds the sdist+wheel and publishes to PyPI.

By submitting a PR, you agree your contribution is licensed under the
project's MIT license.
