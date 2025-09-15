# Development Guidelines

## Tests
Run all tests before committing:

```
PYTHONPATH=. pytest -q
```

## Code Style
Follow PEP 8 conventions. Use [Black](https://black.readthedocs.io/en/stable/) with a maximum line length of 88.

## Linting/Formatting
Before committing, format and lint the code:

```
black -l 88 .
flake8
```

## Project Root
To programmatically locate the repository root, use:

```python
from utils.paths import get_project_root
```

## Commit Message Format
Adopt [Conventional Commits](https://www.conventionalcommits.org/) to structure commit messages, e.g., `feat: add new feature` or `fix: correct a bug`.

## Branch Naming Strategy
Create branches using descriptive prefixes such as `feature/` for new functionality or `fix/` for bug fixes.

## Pull-Request Review Expectations
Open a pull request for every change. Include a clear description of the problem and solution, ensure that tests and linters pass, and respond to reviewer feedback promptly.

## Before Pushing
Run the linter and tests to verify everything is passing:

```
black -l 88 .
flake8
PYTHONPATH=. pytest -q
```

Keep this file up to date as project practices evolve.
