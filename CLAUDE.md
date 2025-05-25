# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Compone is a Python component framework for generating HTML/XML markup using
type-safe Python objects as an alternative to template engines. The codebase is
organized as a multi-package monorepo with clear separation of concerns.

## Architecture

### Package Structure
- **core/**: Main `compone` package - core component framework and HTML generation
- **cli/**: `compone-cli` - CLI tools for HTML conversion and utilities
- **ssg/**: `compone-ssg` - Static Site Generator built on compone
- **stories/**: `compone-stories` - Component development environment (like Storybook)
- **frameworks/**: UI framework integrations (Bootstrap 5, Preline UI, etc.)
- **docs/**: MkDocs Material documentation site

### Development Environment
Uses `devenv.nix` for reproducible development with:
- Multiple Python versions (3.10-3.13) managed by uv
- Just command runner for task automation
- Pre-commit hooks (ruff formatting, linting, file checks)
- Bun for JavaScript dependencies in stories package

## Common Development Commands

### Root Level Commands
```bash
just install-versions   # Install dependencies across all Python versions
just test-all           # Run tests across all packages
just check-all          # Run pre-commit hooks on entire codebase
just clean              # Wipe development environment
```

### Core Package Development
```bash
just core::test               # Run tests with Python 3.12
just core::test-all           # Test across Python 3.10-3.13
just core::watchtests         # Continuous testing with file watching
just core::check              # Run linters and pre-commit hooks
```

### Framework Package Development
Framework packages (like Bootstrap 5) are tested individually:
```bash
cd frameworks/bootstrap5/
uv run pytest tests/    # Run framework-specific tests
```

### Stories Development (Component Playground)
```bash
just stories::install            # Install bun dependencies
just stories::gencss             # Generate Tailwind CSS with file watching
just stories::check              # Run pre-commit hooks
```

### Documentation
```bash
just docs::serve              # Serve docs locally with mkdocs
just docs::generate           # Build static documentation
just docs::publish            # Deploy to GitHub Pages
```

## Testing Strategy

- **Multi-version testing**: All packages are tested across Python 3.10-3.13
- **Core tests**: Comprehensive coverage in `core/tests/` for HTML generation, escaping, HTMX integration
- **Benchmarks**: Performance tests using pytest-benchmark
- **Framework tests**: Individual test suites for UI framework components

## Development Workflow

1. **Environment setup**: Uses uv for Python package management with workspace configuration
2. **Code quality**: Pre-commit hooks enforce ruff formatting and linting
3. **Testing**: Multi-version testing ensures compatibility across Python versions
4. **Component development**: Use stories package for interactive component development
5. **Documentation**: MkDocs Material based docs with automatic GitHub Pages deployment

## Key Files and Patterns

### Component Development
- Components use `@Component` decorator pattern
- HTML elements available through `compone.html` module
- Type-safe attribute handling with `**attrs` pattern
- Framework components follow consistent patterns (see `frameworks/bootstrap5/` examples)

### Package Configuration
- Each package has its own `pyproject.toml` with specific dependencies
- uv workspace configuration in root `pyproject.toml`
- Justfiles provide package-specific commands

### Environment Variables
- `VIRTUAL_ENV`: picked up by uv, points to `.venvs/py3.12`
- `PYTHONPATH`: Includes all projects for development (`core`, `cli`, `stories`, `frameworks/*`, `ssg`, etc...)

## Running Individual Tests
```bash
# Run specific test file
just core::test tests/test_html.py

# Run with specific Python version
just core::test 3.11 tests/
```
