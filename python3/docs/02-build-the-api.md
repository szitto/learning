# Build the API

Now that the project is initialized, it is time to create the first real service. The goal here is not to build a huge application. The goal is to create a clean FastAPI app that already looks like something you could grow into production.

## Why FastAPI

`FastAPI` is a strong learning choice because it makes modern Python backend patterns visible instead of hiding them.

It gives you:

- request and response validation
- type-driven route definitions
- clear OpenAPI generation
- a modern `ASGI` runtime model

For a JavaScript developer, it often feels like a mix of Express-style routing and typed request modeling, but with stronger conventions around Python typing and validation.

## Create the Basic App Entry Point

Start with a small app in `app/main.py`.

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

This gives you the minimum useful service:

- the app object exists
- there is an HTTP route
- there is a health-style endpoint you will keep using later in Docker and deployment guides

## Run the App Locally

Use `uvicorn` to start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The `--reload` flag is for local development only. It watches files and restarts the server on change.

Once the server is running, you should be able to hit:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

The `/docs` route is one of the nice FastAPI defaults. It gives you an interactive OpenAPI UI, which is useful while learning and also valuable for internal service development.

## Understand the App Object

This line matters:

```python
app = FastAPI()
```

That object is your ASGI application. It is the thing your server process loads and runs.

When you execute:

```bash
uv run uvicorn app.main:app --reload
```

you are telling `uvicorn` to import `app.main`, then load the object named `app`.

This import-path style is a core Python deployment pattern. You will see it again in containers and hosted deployments.

## Add a Real API Route

Once the health check works, add a small domain route. For example, an items endpoint:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id, "name": f"item-{item_id}"}
```

This introduces a few useful concepts immediately:

- path parameters
- type conversion from the route definition
- automatic validation if the value is not an integer

## Add Request and Response Models

FastAPI becomes much more useful once you define shapes for incoming and outgoing data. Use Pydantic models for that.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ItemCreate(BaseModel):
    name: str
    price: float


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float


@app.post("/items", response_model=ItemResponse)
def create_item(payload: ItemCreate):
    return {"id": 1, "name": payload.name, "price": payload.price}
```

Understanding the pattern:

- **`BaseModel`**: The base class for Pydantic data models. Unlike `BaseSettings`, these do not read from environment variables. They validate and parse data you pass to them.
- **`name: str`**: A required field. If the incoming JSON is missing `name` or it is not a string, Pydantic returns a 422 validation error automatically.
- **`ItemCreate` vs `ItemResponse`**: Separate models for input and output. The create model does not have `id` because the client does not provide it. The response model includes `id` because the server generates it.
- **`response_model=ItemResponse`**: Tells FastAPI to validate and serialize the return value using this model. It also generates accurate OpenAPI documentation.
- **`payload: ItemCreate`**: When a Pydantic model appears as a function parameter, FastAPI parses the request body as JSON and validates it against the model.

This is one of the places where FastAPI feels more structured than a minimal Express app. Request validation and response shaping are part of the normal flow, not an afterthought.

You can later move these models to a separate file like `app/schemas/item.py` as the app grows.

## Add Settings Early

Even before you add a database, you should create a simple settings layer. Do not scatter environment variable reads across random files.

An example `app/settings.py` might look like this:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "python-production-guide"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
```

Understanding the syntax:

- **`BaseSettings`**: A Pydantic class that automatically reads values from environment variables. If you define `app_name: str`, Pydantic looks for an `APP_NAME` environment variable (case-insensitive matching).
- **`= "python-production-guide"`**: The default value if the environment variable is not set. Without a default, the setting becomes required and the app will fail to start if it is missing.
- **`model_config`**: A class-level configuration for Pydantic. This is Pydantic v2 syntax. It replaces the older `class Config` inner class.
- **`SettingsConfigDict(...)`**: Configures how settings are loaded. Here it tells Pydantic to also read from a `.env` file, which is convenient for local development.
- **`settings = Settings()`**: Creates a singleton instance at module load time. Import this instance throughout your app rather than creating new `Settings()` objects.

Then in `app/main.py` you can use it:

```python
from fastapi import FastAPI

from app.settings import settings

app = FastAPI(title=settings.app_name)
```

If you later add `DATABASE_URL` to your environment or `.env` file, you can access it as `settings.database_url` after adding it to the class.

This matters in production because configuration should come from the environment, not from hardcoded constants buried in route files.

## Suggested Early Directory Structure

As the app grows, move toward this layout:

```text
app/
|-- __init__.py
|-- main.py
|-- settings.py
|-- api/
|   |-- __init__.py
|   |-- routes/
|       |-- __init__.py
|       |-- health.py
|       |-- items.py
|-- schemas/
|   |-- __init__.py
|   |-- item.py
```

You do not need to split files aggressively on day one, but you should know where the app is headed. A production app usually benefits from separating routes, schemas, settings, and later database code.

## Development Server vs Production Server

This distinction is important.

For local development, this is correct:

```bash
uv run uvicorn app.main:app --reload
```

For production, the concern changes. You usually care about:

- worker processes
- container entrypoint behavior
- startup timing
- health checks
- logging configuration

So the local `uvicorn` command is part of the story, but not the full deployment model. Do not confuse "the app starts on my laptop" with "the service is production-ready."

## What You Should Have After This Step

By now, you should have:

- a working `FastAPI` app
- a `/health` endpoint
- at least one domain route
- local execution through `uvicorn`
- a basic direction for request/response models
- a settings layer ready for environment-based config

Next, you will make the app safer to change by adding tests, linting, formatting, and type-aware habits.
