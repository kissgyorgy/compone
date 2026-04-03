# Repository overview

Compone is a Python component framework for generating HTML, XML, RSS,
and similar markup from typed Python objects instead of template strings.
This repository is a uv workspace monorepo with the core library plus CLI,
static-site, stories, framework-integration, and docs packages.

# Command discovery and environment

- Start in `devenv shell` when possible. It activates `.venvs/py3.13`, sets
  `PYTHONPATH` across workspace packages, and provides the `run-version` /
  `activate-version` helpers used by the Justfiles.
- Discover root-level commands with `just --list` or `just help`.
- Discover package-local commands with:
  - `(cd core && just --list)`
  - `(cd stories && just --list)`
  - `(cd docs && just --list)`
- The `compone` CLI is plugin-based. Command wiring lives in `cli/compone_cli/cli.py`,
  while extra subcommands are registered from package `pyproject.toml` entry points
  under the `compone.cli` group.

# Frequently used commands

- `just test-all` — run the multi-version test entry point from the repo root.
- `(cd core && just test)` — run the core test suite on Python 3.12.
- `(cd core && just test 3.11 tests/test_html.py)` — run a specific core test target on a chosen Python version.
- `(cd core && just test-all)` — run the core test suite across 3.10–3.13.

# Monorepo structure

- `core/` — main `compone` package.
- `cli/` — `compone-cli`, including the top-level CLI entrypoint and HTML-to-component conversion command.
- `ssg/` — `compone-ssg`, a static site generator built on compone components.
- `stories/` — `compone-stories`, a Storybook-like preview environment for components.
- `frameworks/` — framework-specific component libraries.
- `docs/` — MkDocs Material documentation site.
