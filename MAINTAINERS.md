# Maintainers' Guide

This document outlines essential guidelines for maintaining the SignEasy project.
It provides instructions for testing, building, and deploying the package, as well as managing CI workflows.

## Overview

SignEasy project is managed via [Poetry](https://python-poetry.org/) for dependency management at backend side
and [npm](https://www.npmjs.com/) for dependency management at frontend side. This guide assumes familiarity with
GitHub Actions, npm, Poetry, and common Python development workflows.


Key configurations:

- Python Versions Supported: >= 3.10, <4.0
- Build Tool: `poetry`, `npm`
- Testing Tools: `pytest`, `coverage`
- Linting Tools: `flake8`, `pylint`
- [Flowbite](https://flowbite.com/) as a UI library
- [Tailwind CSS](https://tailwindcss.com/) as a CSS framework

## Testing the project

Unit tests and coverage reporting are managed using `pytest` and `coverage`.

### Running the tests

1. Install dependencies:
   ```bash
   poetry install --with=dev --with=testing --no-root
   ```
2. Run the tests:
   ```bash
   coverage run -m pytest ./se ./tests
   coverage combine
   coverage report
   ```
### Debugging and Logging

To investigate LLM responses, you can use the `llm_responses.jsonl` file in the `storage` directory.
For example, you can use the following command:

```bash
tail -f storage/data/llm_responses.jsonl | jq
```

and upload a file to the server for analysis.

### CI Workflow

Tests are executed automatically on supported platforms and Python versions.
See the configuration in `.github/workflows/ci.yml` ([ci](https://github.com/sergeyklay/hackathon2025-signeasy/blob/main/.gi)).
