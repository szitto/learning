# Project Setup

This section gets you from an empty directory to a Python service repository that feels predictable and maintainable. The goal is not just to get code running. The goal is to set up the repo in a way that still makes sense once tests, Docker, CI, migrations, and deployment are added.

## Why This Setup

For this guide, we use `uv` because it gives you a modern dependency workflow with fast installs, virtual environment support, and a clean path for locking dependencies. If you are coming from JavaScript, it is a good mental fit: one tool handles most of the daily dependency workflow instead of mixing `pip`, `venv`, and extra wrappers.

We will aim for a repo that has:

- a clear `pyproject.toml`
- an isolated virtual environment
- app code under `app/`
- tests under `tests/`
- development dependencies tracked explicitly

## Install uv

Install `uv` using the official method for your OS. Once it is installed, verify it works:

```bash
uv --version
```

If that command works, create your new project directory and initialize the repo metadata.

## Initialize the Project

From an empty directory, run:

```bash
uv init
```

This creates the starting project files, including `pyproject.toml`. That file plays a role similar to `package.json` in the Node world, although Python tools often put more configuration directly into it.

You should inspect `pyproject.toml` early. In Python, this file often becomes the center of project metadata and tool configuration.

## Create the Virtual Environment

Next, create a virtual environment:

```bash
uv venv
```

This creates a local environment, often in `.venv/`, that isolates this project's Python dependencies from the rest of your machine.

If you are used to `node_modules`, the closest Python equivalent is the virtual environment, not a plain dependency folder inside the repo. The important mental model is: each project gets its own interpreter context and installed packages.

Activate it if you want the classic shell workflow:

```bash
source .venv/bin/activate
```

You do not always need activation when using `uv`, but it helps when you want the shell to behave like the project is already selected.

## Add Runtime Dependencies

Install the app dependencies:

```bash
uv add fastapi uvicorn pydantic-settings
```

This updates your project metadata and lock state. You are adding:

- `fastapi` for the web framework
- `uvicorn` for running the ASGI app locally and, in some cases, in production-oriented setups
- `pydantic-settings` for typed, environment-aware configuration management

## Add Development Dependencies

Install the tools you want for testing and code quality:

```bash
uv add --dev pytest ruff
```

These are the Python equivalents of the tools you would expect in a mature JS repo:

- `pytest` for tests
- `ruff` for linting and formatting

Later, you will add database and migration dependencies, but for now keep the setup minimal.

## Recommended Project Layout

At this stage, aim for a layout like this:

```text
.
|-- .venv/
|-- app/
|   |-- __init__.py
|   |-- main.py
|   |-- settings.py
|-- tests/
|   |-- __init__.py
|   |-- test_health.py
|-- pyproject.toml
|-- uv.lock
|-- README.md
```

Suggested meaning of each part:

- `app/main.py` holds the FastAPI app entrypoint
- `app/settings.py` holds configuration loading
- `tests/` mirrors runtime behavior with focused test files
- `pyproject.toml` stores metadata and tool configuration
- `uv.lock` gives you reproducible dependency resolution

## Why `pyproject.toml` Matters

In the JavaScript world, many teams centralize project behavior in `package.json` scripts, then spread lint and test settings across tool-specific files. Python often leans more heavily on `pyproject.toml` as a shared config home.

You will commonly see it hold:

- project metadata
- dependency declarations
- tool configuration for formatters and linters
- test-related settings in some repos

Treat it as a first-class file, not a generated detail.

## Lockfiles and Reproducibility

Just like `package-lock.json` or `pnpm-lock.yaml`, the Python lockfile matters. It helps make installs reproducible across machines and CI.

In this guide, the lockfile is part of the normal development flow. You should commit it.

That gives you a safer deployment story because your local environment, CI environment, and container build are all much more likely to resolve the same dependency versions.

## Running Commands in the Project

When using `uv`, a common pattern is to run tools through it directly:

```bash
uv run pytest
uv run ruff check .
uv run python -V
```

This keeps command execution tied to the project's dependency context.

## Common Early Mistakes

### Using the system Python implicitly

Be explicit about the project environment. Hidden interpreter mismatches cause confusing failures later.

### Not reading `pyproject.toml`

If you treat it as magic, Python tooling will feel arbitrary. Read it often.

### Installing globally out of habit

Avoid treating global Python package installs as your normal workflow. Use the project environment.

### Waiting too long to choose structure

A tiny app becomes a messy app quickly. Start with a clean directory layout before adding routes, models, and settings.

## What You Should Have After This Step

By the end of setup, you should have:

- a new Python repo initialized with `uv init`
- a virtual environment created with `uv venv`
- web dependencies installed with `uv add fastapi uvicorn pydantic-settings`
- dev dependencies installed with `uv add --dev pytest ruff`
- a usable `pyproject.toml`
- a clear app and test directory layout

Next, you will create the first working FastAPI application and run it locally.
