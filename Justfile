pytest := "python -m pytest --pdb -vv tests/"

mod stories
mod core

help:
    @just --list

# Run tests in all projects
test-all:
    just core::test

# Run checks in all projects
check-all:
    pre-commit run --all-files --hook-stage manual
