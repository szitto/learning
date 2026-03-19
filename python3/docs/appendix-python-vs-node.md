# Python vs Node Appendix

## Mental Model Mapping

If you already know Node, the fastest way to learn Python production is to map familiar concepts to Python equivalents.

- `package.json` maps roughly to `pyproject.toml`
- `npm install` maps to `uv add` or `uv sync`
- `node_modules` maps to a virtual environment
- `express` maps loosely to `FastAPI` or `Flask`
- `jest` maps to `pytest`
- `eslint` and `prettier` often collapse into `ruff`
- `dotenv` maps to environment variables plus a settings layer
- `pm2` or a raw Node process maps to a Python process runner such as `uvicorn` or `gunicorn` with workers

The big mental shift is that Python projects often treat the environment and interpreter as more visible parts of the workflow than Node projects do.

## Tooling Equivalents

Here is a practical translation table for the stack used in this guide.

| Node / JS concept | Python equivalent | Why it matters |
| --- | --- | --- |
| `package.json` scripts | shell commands, Make targets, task runner, CI steps | Python repos often rely less on a single script hub |
| `npm` / `pnpm` | `uv` | installs and locks dependencies |
| `node_modules` | `.venv` | isolates project dependencies |
| `express` | `FastAPI` | web framework |
| `jest` / `vitest` | `pytest` | test runner and assertion style |
| `eslint` + `prettier` | `ruff` | linting and formatting |
| `prisma migrate` / knex migrations | `Alembic` | schema migration workflow |
| ORM such as Prisma/Sequelize | `SQLAlchemy` | data access layer |

## Runtime Differences

Node production usually feels like running JavaScript on one runtime with one event loop model, then scaling with processes or containers as needed.

Python is a little more fragmented in a good way:

- there is a distinction between `WSGI` and `ASGI`
- framework choice affects sync versus async style more directly
- local development server commands are often not the same as production server commands
- production often means explicitly choosing worker count and server entrypoint

For a modern API, you will usually care about `ASGI`, which is what `FastAPI` uses.

## Deployment Differences

Node developers often think in terms of "build app, set env vars, run process." That still exists in Python, but the surrounding conventions differ.

Typical Python production concerns include:

- creating a virtual environment or image with the right interpreter
- installing from a lockfile-resolved dependency set
- choosing `uvicorn` or `gunicorn` worker strategy
- running database migrations as an explicit deployment step
- treating `pyproject.toml` as a central config surface

Another major difference is artifact shape. In JavaScript, especially frontend work, production often means a transformed build output. In Python backend work, the most common artifact is still your source tree plus installed dependencies inside a container image.

## Common Mistakes for JS Developers Learning Python

### Expecting frontend-style build steps

Python backend deployments usually do not center on minification, bundling, or obfuscation. Focus first on containers, config, migrations, health checks, and worker processes.

### Underestimating the role of the interpreter

In Python, interpreter version matters a lot. A mismatch between local Python and deployed Python can break installs or runtime behavior.

### Treating local dev server commands as production commands

`uvicorn app.main:app --reload` is great for local development. It is not the production deployment story by itself.

### Skipping migrations in the deployment model

Schema changes are usually first-class deployment concerns. Do not treat them as a side detail.

### Assuming all frameworks hide infrastructure equally

Some platforms make Python feel very managed, but the underlying runtime model still matters. You still need to understand workers, config, image contents, and startup behavior.

### Overcomplicating early packaging choices

You do not need to learn every Python packaging standard before shipping a service. Learn the operational path first: `pyproject.toml`, locked dependencies, tests, container image, deployment target.
