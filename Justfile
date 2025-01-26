mod stories
mod core
mod docs

help:
    @just --list

# Install packages in all Python version virtualenvs
install-versions:
    #!/usr/bin/env bash
    for version in 3.9 3.10 3.11 3.12 3.13; do \
        run-python-version $version uv sync
    done

# Run tests in all projects
test-all:
    just core::test-all

# Run checks in all projects
check-all:
    pre-commit run --all-files --hook-stage manual

# Completely wip the development environment and start from scratch
reset-devenv:
    rm -rf .venv .venvs .direnv .pre-commit-config.yaml .pytest_cache .ruff_cache
