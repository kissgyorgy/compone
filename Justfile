just_run := "just --unstable"
pytest := "python -m pytest --pdb -vv tests/"

mod stories
mod core

help:
    @just --unstable --list

# Install dependencies for all projects
install-all:
    poetry install
    @{{ just_run }} stories::install

# Run tests in all projects
test-all:
    @{{ just_run }} core::test

# Run checks in all projects
check-all:
    @{{ just_run }} core::check
