# Development Guidelines

- **Tests**: Run all tests before committing:

  ```
  PYTHONPATH=. pytest -q
  ```

- **Code style**: Follow PEP 8 conventions. Use [Black](https://black.readthedocs.io/en/stable/) with a maximum line length of 88.

- **Linting/formatting**: Before committing, format and lint the code:

  ```
  black -l 88 .
  flake8
  ```

- **Project root**: To programmatically locate the repository root, use:

  ```python
  from utils.paths import get_project_root
  ```

- Keep this file up to date as project practices evolve.
