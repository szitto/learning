# Containerization

Containerization is where the app starts to feel genuinely portable. Instead of relying on your laptop's Python install and whatever happens to be configured locally, you define a repeatable runtime image that can move between local development, CI, and deployment targets.

## Why Containerize the App

For this guide, Docker gives you a practical boundary around:

- the Python version
- installed dependencies
- filesystem layout
- startup command
- exposed network port

This is especially useful when you want the same application shape to run on a VPS, AWS ECS/Fargate, and Fly.io.

## A Minimal Dockerfile

Start with a small image definition:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This example is intentionally simple. It teaches the important ideas:

- base image defines the runtime
- `uv` is copied from the official image for fast, reliable installs
- working directory is explicit
- dependency files are copied before app code
- runtime command is part of the image contract

For a more production-optimized image, you can use a multi-stage build that does not include `uv` in the final image:

```dockerfile
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY app ./app

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Understanding multi-stage builds:

- **`FROM ... AS builder`**: Names the first stage. Everything in this stage is used to build the app but does not end up in the final image.
- **`FROM python:3.13-slim`** (second one): Starts a fresh image. This becomes the final runtime image.
- **`COPY --from=builder /app/.venv ...`**: Copies only the virtual environment from the builder stage. The venv contains all installed packages and is fully portable because both stages use the same base image.
- **`ENV PATH="/app/.venv/bin:$PATH"`**: Puts the venv's `bin` directory first in PATH. This means `uvicorn` resolves to the venv's copy without needing `uv run`.
- **Why this works**: Python virtual environments are just directories with executables and packages. As long as the Python version matches, you can copy a venv between stages or even between machines.

The final image does not contain `uv`, `pip`, or any build tools. It only has Python, the venv with your dependencies, and your application code. This keeps the image smaller and reduces attack surface.

## Why Copy Dependency Files First

Notice the order:

1. copy `pyproject.toml` and `uv.lock`
2. install dependencies
3. copy application source

That ordering helps Docker layer caching. If your app code changes but dependencies do not, rebuilds stay faster.

## Build the Image

From the project root:

```bash
docker build -t python-production-guide .
```

This produces a container image containing the app and its runtime dependencies.

## Run the Container Locally

Run it directly first:

```bash
docker run --rm -p 8000:8000 python-production-guide
```

Then check:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

This is your first realistic proof that the app works outside your host Python environment.

## Add Docker Compose for a Production-Like Local Setup

Once the app depends on PostgreSQL, a single container is not enough. Use Docker Compose to run the service and database together.

Example `compose.yaml`:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://app:app@db:5432/app
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 5s
      retries: 5
```

Understanding the `depends_on` and `healthcheck` pattern:

- **`depends_on: db`** (simple form): Only waits for the container to *start*, not for PostgreSQL to be *ready*. Your app will likely crash on first startup because the database is not accepting connections yet.
- **`depends_on: db: condition: service_healthy`**: Waits for the `db` service to pass its health check before starting `app`. This is what you usually want.
- **`healthcheck`**: Defines how Docker determines if a service is healthy. The `pg_isready` command is PostgreSQL's built-in readiness check.
- **`interval`, `timeout`, `retries`**: Control how often Docker checks, how long to wait for each check, and how many failures before marking unhealthy.

This setup gives you a much more useful local environment because networking, dependency wiring, and service startup begin to resemble real deployment conditions.

Without the health check, you will often see the app crash on first startup, then succeed on restart after Compose retries. The health check pattern avoids this race condition.

## Start the Stack

Run:

```bash
docker compose up --build
```

If you later add migrations as a startup or release step, this local stack becomes the place where you validate the full app shape before shipping it anywhere else.

## Image Build vs Runtime Configuration

One of the most important container lessons is knowing what belongs in the image and what belongs in the environment.

Good image contents:

- application source
- installed dependencies
- startup command
- static defaults that are not secret

Good runtime configuration:

- database URLs
- API keys
- secrets
- environment-specific hostnames
- deployment-specific feature flags

Do not bake secrets into the Dockerfile. Do not hardcode production configuration into the image.

## Exposed Ports and Network Binding

In local development, you might run on the default `127.0.0.1` binding. In containers, the app usually needs to listen on all interfaces inside the container:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

That is why the Docker `CMD` is slightly different from the local development command.

## What About Multi-Stage Builds?

Multi-stage builds are useful once you care more about image size, build performance, or separating builder dependencies from runtime dependencies.

For learning, start with a single clear Dockerfile. Once the flow makes sense, you can evolve to more optimized images later.

## Common Mistakes

### Copying the entire project too early

That makes Docker caching worse and rebuilds slower.

### Baking secrets into the image

Secrets belong in runtime configuration, not build steps.

### Forgetting container network binding

An app listening only on localhost inside the container will not behave the way you expect when published.

### Treating Compose as production by default

Docker Compose is great for local realism and simple VPS deployments, but it is not the universal deployment abstraction for every platform.

## What You Should Have After This Step

By now, you should have:

- a Dockerfile beginning with `FROM python:3.13-slim`
- a way to build the image locally
- a way to run the app in a container
- a Docker Compose setup with an `app` service and a database service
- a clear understanding of build-time versus runtime configuration

Next, you will connect this local container workflow to CI/CD so quality checks and deployments become repeatable.
