# Data and Migrations

Most production applications stop being toy apps the moment they persist state. Once you add a database, deployment gets more serious: schema changes matter, ordering matters, rollback strategy matters, and local development has to resemble reality more closely.

For this guide, we use:

- PostgreSQL as the database
- SQLAlchemy as the database toolkit and ORM
- Alembic for schema migrations

## Why PostgreSQL

PostgreSQL is a strong default because it is widely used, production-proven, and well supported across Python libraries and hosting platforms. It also teaches habits that transfer well to managed databases in the cloud.

## Run PostgreSQL Locally

Before writing database code, you need a running PostgreSQL instance. The easiest approach for local development is Docker:

```bash
docker run -d \
  --name postgres-dev \
  -e POSTGRES_DB=app \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -p 5432:5432 \
  postgres:16
```

This starts a PostgreSQL 16 container with a database named `app` and matching credentials. The `-p 5432:5432` flag makes it accessible on your host at `localhost:5432`.

You can verify it is running with:

```bash
docker ps
docker logs postgres-dev
```

To stop it later:

```bash
docker stop postgres-dev
```

To start it again:

```bash
docker start postgres-dev
```

Later, when you reach the containerization section, you will move to a Docker Compose setup that runs both the app and database together. For now, a standalone PostgreSQL container is enough to learn the database integration.

## Install the Database Dependencies

Add the persistence stack to the project:

```bash
uv add sqlalchemy alembic psycopg[binary]
```

These packages give you:

- `SQLAlchemy` for models, sessions, and queries
- `Alembic` for versioned schema changes
- `psycopg[binary]` as the PostgreSQL driver

## Define the Database Connection

You will eventually want a settings field for the connection string, something like:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
```

That value should come from the environment in real deployments. Keep the connection string in config, not scattered across the codebase.

## Add SQLAlchemy Structure

At a minimum, you will want:

- a module that creates the engine
- a session factory
- model classes

Create a file at `app/db.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.settings import settings


class Base(DeclarativeBase):
    """
    Base class for all ORM models. Every model you define will inherit from this.
    SQLAlchemy uses this to track all your tables and their relationships.
    """
    pass


engine = create_engine(settings.database_url)
"""
The engine is the connection factory. It holds the database URL and connection
pool settings. You typically create one engine per application.
"""

SessionLocal = sessionmaker(bind=engine)
"""
SessionLocal is a factory that creates new database sessions. Each session is
a workspace for your database operations - like a transaction boundary. You
create a new session for each request, use it, then close it.
"""
```

Understanding the pieces:

- **Engine**: The connection manager. It knows how to connect to your database and pools connections for efficiency. Think of it like a database client instance in Node.
- **Session**: A unit-of-work container. You open a session, make queries or changes, commit or rollback, then close it. Similar to how you might use a transaction in Knex or Prisma.
- **Base**: The parent class for all your models. SQLAlchemy uses this to discover your tables and generate DDL.

## Add a First Model

Create a file at `app/models.py` for the sample app:

```python
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
```

Understanding the syntax:

- **`__tablename__`**: The actual table name in PostgreSQL. SQLAlchemy requires this to map the class to a database table.
- **`Mapped[int]`**: A type hint that tells SQLAlchemy (and your editor) what Python type this column holds. This is SQLAlchemy 2.0 style.
- **`mapped_column(Integer, ...)`**: Defines the actual database column. `Integer` is the SQL type, which may differ from the Python type (e.g., `String(255)` becomes `VARCHAR(255)` in SQL).
- **Why both `Mapped[int]` and `Integer`?**: The type hint is for Python/editor tooling. The `Integer` argument is for the database DDL. They work together but serve different purposes.

If you have used Prisma or TypeORM, this is the equivalent of a schema definition, but written as a Python class instead of a schema file.

This gives you a concrete thing to persist when you later evolve the `POST /items` endpoint beyond returning a hardcoded object.

## Initialize Alembic

Set up migrations with:

```bash
uv run alembic init alembic
```

This creates:

- `alembic.ini` - main configuration file
- `alembic/` - directory for migration scripts
- `alembic/env.py` - Python file that runs during migrations

Before migrations will work, you must configure Alembic to know about your models and database.

## Configure Alembic

### Step 1: Set the database URL

Open `alembic.ini` and find the `sqlalchemy.url` line. You can either hardcode it for local development:

```ini
sqlalchemy.url = postgresql+psycopg://app:app@localhost:5432/app
```

Or, for a cleaner setup, leave it empty and set it dynamically in the next step:

```ini
sqlalchemy.url =
```

### Step 2: Wire up your models

Open `alembic/env.py`. This file controls how Alembic connects to your database and discovers your models.

Find the line that says:

```python
target_metadata = None
```

Replace it with:

```python
from app.db import Base
from app.settings import settings
from app import models  # Import so models are registered with Base

target_metadata = Base.metadata
```

The `target_metadata` tells Alembic about all your SQLAlchemy models. When you import `models`, Python executes that module, which registers each model class with `Base`. Alembic then compares `Base.metadata` against the actual database to generate migrations.

### Step 3: Set the database URL dynamically (optional but recommended)

In the same `alembic/env.py` file, find the `run_migrations_online` function. Inside it, look for:

```python
connectable = engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)
```

Replace it with:

```python
connectable = create_engine(settings.database_url, poolclass=pool.NullPool)
```

And add this import at the top of the file:

```python
from sqlalchemy import create_engine
```

This makes Alembic use the same `database_url` setting as your app, so you only configure the connection in one place.

## Create the First Migration

After defining the model and wiring Alembic, generate a migration:

```bash
uv run alembic revision --autogenerate -m "create items table"
```

Review the generated migration. Do not blindly trust autogenerated output just because the command succeeded. Migrations are production artifacts. Treat them with the same seriousness you would treat infrastructure changes.

## Apply the Migration

Run the schema change:

```bash
uv run alembic upgrade head
```

At this point, your local PostgreSQL instance should have the new table.

This explicit migration step is one of the biggest practical differences between a demo app and a deployable service. Database shape is no longer implied by code alone. It becomes a versioned part of the release process.

## How Persistence Fits the App

Once the database exists, your route flow usually starts to look like this:

1. request hits FastAPI route
2. request payload is validated
3. route or service layer opens a session
4. model instances are queried or created
5. transaction is committed if needed
6. response model is returned

That is the point where your app begins to resemble a normal production backend instead of a pure in-memory demo.

## Connect Routes to the Database

FastAPI uses dependency injection to provide database sessions to routes. First, create a dependency function in `app/db.py`:

```python
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session to a route.
    The session is automatically closed when the request ends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

The `yield` keyword makes this a generator. FastAPI runs the code before `yield` at the start of the request, provides the session to your route, then runs the `finally` block after the response is sent.

Now use it in a route:

```python
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemResponse

app = FastAPI()


@app.post("/items", response_model=ItemResponse)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(name=payload.name, price=payload.price)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

Understanding the pattern:

- **`Depends(get_db)`**: Tells FastAPI to call `get_db()` and inject the result as the `db` parameter. This is similar to middleware in Express, but scoped to individual routes.
- **`db.add(item)`**: Stages the new object for insertion.
- **`db.commit()`**: Writes the changes to the database.
- **`db.refresh(item)`**: Reloads the object from the database to get generated values like `id`.
- **`db.query(Item)`**: Starts a query against the items table.

This dependency injection approach means your routes stay testable. In tests, you can override `get_db` to provide a test database or mock session.

## Why Alembic Matters in Production

It is tempting to think of migrations as a developer convenience. They are more than that.

In production, Alembic helps you:

- track schema history
- deploy schema changes in a repeatable way
- keep environments aligned
- reason about which app version expects which database shape

Without a migration process, even a small team quickly loses confidence in deployments.

## Local vs Deployment Migration Flow

Locally, a simple flow is:

1. update models
2. generate migration
3. review migration
4. run `uv run alembic upgrade head`
5. run tests

In deployment, the same idea still exists, but timing matters more. You need to decide whether migrations run:

- as a dedicated release step
- in a one-off task or job
- as part of app startup, which is often less safe for mature systems

This guide will treat migrations as a deliberate deployment concern, not something hidden inside application startup.

## Common Mistakes

### Treating the ORM model as the only source of truth

Once migrations exist, schema history matters too. Code and migration files both matter.

### Skipping migration review

Autogenerated does not mean correct. Review DDL changes before running them against anything important.

### Hardcoding database URLs in random files

Keep them in settings and environment variables.

### Forgetting that deployment order matters

A schema change can break an older app version or vice versa. Think about compatibility, not just local correctness.

## What You Should Have After This Step

By now, you should have:

- PostgreSQL in the app architecture
- dependencies installed with `uv add sqlalchemy alembic psycopg[binary]`
- a basic SQLAlchemy model setup
- Alembic initialized with `uv run alembic init alembic`
- a migration created with `uv run alembic revision --autogenerate -m "create items table"`
- the schema applied with `uv run alembic upgrade head`

Next, you will focus on the operational concerns that make the service safe to run beyond a local machine.
