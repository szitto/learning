# Testing and Quality

Once the app runs locally, the next job is making it safe to change. A production service is not just code that works once. It is code you can refactor, extend, and deploy with confidence.

For this guide, the quality toolchain is intentionally small:

- `pytest` for tests
- `ruff` for linting and formatting
- type hints for clarity and better editor and framework feedback

## Why Keep the Stack Small

If you come from JavaScript, you may be used to separate tools for formatting, linting, test running, type checking, and import sorting. Python can also become tool-heavy, but for a learning path it is better to keep the stack tight.

`ruff` replaces a surprising amount of the usual tool sprawl. It can handle linting and formatting in one place, which is great when you want fewer moving parts.

## Add Your First Test

Start by testing the endpoint you already built. A simple health check test proves the app boots and responds correctly.

Example test file: `tests/test_health.py`

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Run the test suite with:

```bash
uv run pytest
```

That command should become part of your muscle memory.

## Test the Route Behavior, Not the Framework

When writing early application tests, focus on behavior you own.

Good things to test:

- expected status codes
- JSON response shapes
- validation behavior for invalid inputs
- domain logic that transforms or persists data

Less useful early tests:

- restating FastAPI internals
- asserting implementation details that will change during refactors
- snapshotting huge responses without a reason

## Use `pytest` as the Default Testing Tool

`pytest` is the standard practical choice for most Python services. It gives you straightforward assertions, test discovery, fixtures, and a large ecosystem when you need more depth.

Run tests explicitly through the project environment:

```bash
uv run pytest
```

If you want more detailed output while debugging, use:

```bash
uv run pytest -v
```

## Lint and Format with Ruff

Run lint checks with:

```bash
uv run ruff check .
```

Run formatting with:

```bash
uv run ruff format .
```

For a JavaScript developer, this is the rough equivalent of combining common ESLint and Prettier workflows into a single faster toolchain.

In a production repo, these commands usually run:

- before commits, either manually or through hooks
- in CI on every branch and pull request
- locally before container builds and releases

## Add Type Hints Early

Python type hints are not just for strict static typing setups. They improve readability, framework integration, editor support, and refactoring confidence.

FastAPI especially benefits from clear type usage because it uses types to help drive validation and API schema generation.

Examples:

```python
def get_item(item_id: int) -> dict[str, int | str]:
    return {"item_id": item_id, "name": f"item-{item_id}"}
```

```python
class ItemCreate(BaseModel):
    name: str
    price: float
```

You do not need to become a type-system purist to benefit from this. Use type hints where they communicate intent and reduce ambiguity.

## A Practical Testing Strategy

For the kind of service in this guide, think in three layers:

### Route tests

Use the test client to verify status codes, payloads, and validation behavior.

### Service or domain tests

If you later extract business logic into helper or service modules, test that logic directly without always going through HTTP.

### Integration tests

Once the database is added, write a smaller number of tests that prove the app works across the HTTP and persistence boundary.

Do not start by trying to build a giant, perfect test pyramid. Start by proving the app's critical behavior and expand where failure would be expensive.

## A Practical Quality Workflow

A good local quality loop looks like this:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

That is enough to catch a surprising number of issues early.

## Common Mistakes

### Treating tests as optional until later

The earlier the tests exist, the easier it is to change the app structure without fear.

### Overtesting framework details

You do not need to prove that FastAPI itself works. Test your routes, data handling, validation decisions, and failure behavior.

### Splitting formatting and linting into too many tools too early

You can always add more tooling later. Start with `ruff` unless you have a specific reason not to.

### Avoiding type hints because Python is dynamic

Dynamic does not mean unclear. Type hints are one of the fastest wins for maintainability.

## What You Should Have After This Step

By now, you should have:

- at least one `pytest` test covering the app
- a repeatable `uv run pytest` workflow
- linting with `uv run ruff check .`
- formatting with `uv run ruff format .`
- basic type-aware habits in route and model definitions

Next, you will add PostgreSQL, define persistence, and manage schema changes with migrations.
