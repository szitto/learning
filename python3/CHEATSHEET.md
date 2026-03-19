# Python 3 Best Practices Cheatsheet

Quick reference for writing production-quality Python. Aimed at developers coming from JavaScript/TypeScript.

---

## Project Structure

```text
project/
├── app/
│   ├── __init__.py          # Makes app a package (can be empty)
│   ├── main.py               # Application entrypoint
│   ├── settings.py           # Configuration
│   ├── db.py                 # Database setup
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           └── items.py
├── tests/
│   ├── __init__.py
│   └── test_items.py
├── alembic/                  # Migrations
├── pyproject.toml            # Project metadata & dependencies
├── uv.lock                   # Lockfile (commit this)
└── .env                      # Local secrets (don't commit)
```

---

## Dependency Management

### uv (recommended)

```bash
# Initialize project
uv init

# Create virtual environment
uv venv

# Add dependencies
uv add fastapi uvicorn
uv add --dev pytest ruff

# Install from lockfile
uv sync

# Run commands in project context
uv run pytest
uv run python script.py
```

### Key differences from npm

| npm | uv/Python |
|-----|-----------|
| `package.json` | `pyproject.toml` |
| `package-lock.json` | `uv.lock` |
| `node_modules/` | `.venv/` |
| `npm install` | `uv sync` |
| `npm install pkg` | `uv add pkg` |
| `npx command` | `uv run command` |

---

## Type Hints

### Basic types

```python
name: str = "hello"
count: int = 42
price: float = 19.99
active: bool = True
items: list[str] = ["a", "b"]
mapping: dict[str, int] = {"a": 1}
optional: str | None = None
```

### Function signatures

```python
def greet(name: str) -> str:
    return f"Hello, {name}"

def process(items: list[int]) -> dict[str, int]:
    return {"sum": sum(items)}

async def fetch(url: str) -> bytes:
    ...
```

### Complex types

```python
from typing import TypeVar, Generic, Callable

# Union types
def parse(value: str | int) -> str: ...

# Optional (same as X | None)
from typing import Optional
def find(id: int) -> Optional[Item]: ...

# Callable
handler: Callable[[str, int], bool]

# TypeVar for generics
T = TypeVar("T")
def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

---

## Pydantic Models

### Request/Response schemas

```python
from pydantic import BaseModel, Field, field_validator

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    tags: list[str] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

    model_config = {"from_attributes": True}  # Allows ORM object conversion
```

### Settings from environment

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    api_key: str = Field(..., min_length=32)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()  # Reads from env vars automatically
```

---

## FastAPI Patterns

### Basic route

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int) -> ItemResponse:
    item = find_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
```

### Dependency injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/items")
def list_items(db: Session = Depends(get_db)) -> list[ItemResponse]:
    return db.query(Item).all()
```

### Background tasks

```python
from fastapi import BackgroundTasks

def send_email(to: str, subject: str):
    # slow operation
    ...

@app.post("/signup")
def signup(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Welcome!")
    return {"status": "ok"}
```

### Middleware

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response
```

---

## SQLAlchemy Patterns

### Model definition

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    items: Mapped[list["Item"]] = relationship(back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="items")
```

### Common queries

```python
# Get by ID
item = db.get(Item, item_id)

# Filter
items = db.query(Item).filter(Item.price > 10).all()

# Filter with multiple conditions
items = db.query(Item).filter(
    Item.active == True,
    Item.price.between(10, 100)
).all()

# First or None
item = db.query(Item).filter(Item.name == "foo").first()

# Count
count = db.query(Item).filter(Item.active == True).count()

# Order and limit
items = db.query(Item).order_by(Item.created_at.desc()).limit(10).all()

# Join
results = db.query(Item, User).join(User).filter(User.active == True).all()
```

### CRUD operations

```python
# Create
item = Item(name="New", price=9.99)
db.add(item)
db.commit()
db.refresh(item)  # Reload to get generated id

# Update
item.name = "Updated"
db.commit()

# Delete
db.delete(item)
db.commit()

# Bulk update
db.query(Item).filter(Item.active == False).update({"archived": True})
db.commit()
```

---

## Testing

### Basic test

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_item():
    response = client.post("/items", json={"name": "Test", "price": 9.99})
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

### Fixtures

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_item(db):
    item = Item(name="Test", price=9.99)
    db.add(item)
    db.commit()
    assert item.id is not None
```

### Override dependencies in tests

```python
from app.main import app
from app.db import get_db

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

---

## Async/Await

### When to use async

```python
# Use async for I/O-bound operations
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# FastAPI handles both sync and async routes
@app.get("/sync")
def sync_route():  # OK for CPU-bound or simple operations
    return {"data": compute_something()}

@app.get("/async")
async def async_route():  # Better for I/O-bound operations
    data = await fetch_external_api()
    return {"data": data}
```

### Gather for parallel requests

```python
import asyncio

async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

---

## Error Handling

### Custom exceptions

```python
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
        super().__init__(f"Item {item_id} not found")

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )
```

### Context managers for cleanup

```python
from contextlib import contextmanager

@contextmanager
def temporary_file(path: str):
    try:
        yield open(path, "w")
    finally:
        os.remove(path)

with temporary_file("/tmp/data.txt") as f:
    f.write("hello")
# File is automatically deleted
```

---

## Logging

### Basic setup

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

logger.debug("Detailed info for debugging")
logger.info("General information")
logger.warning("Something unexpected")
logger.error("Something failed")
logger.exception("Error with traceback")  # Use in except blocks
```

### Structured logging with structlog

```python
import structlog

logger = structlog.get_logger()

logger.info("user_login", user_id=123, ip="1.2.3.4")
# Output: {"event": "user_login", "user_id": 123, "ip": "1.2.3.4", ...}
```

---

## Common Gotchas

### Mutable default arguments

```python
# BAD - list is shared between calls
def append(item, items=[]):
    items.append(item)
    return items

# GOOD - create new list each call
def append(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### Late binding in closures

```python
# BAD - all functions return 4
funcs = [lambda: i for i in range(5)]
print([f() for f in funcs])  # [4, 4, 4, 4, 4]

# GOOD - capture value at creation time
funcs = [lambda i=i: i for i in range(5)]
print([f() for f in funcs])  # [0, 1, 2, 3, 4]
```

### String formatting

```python
name = "World"

# f-strings (preferred)
greeting = f"Hello, {name}!"

# .format()
greeting = "Hello, {}!".format(name)

# % formatting (avoid)
greeting = "Hello, %s!" % name
```

### Truthiness

```python
# These are all falsy:
bool(None)      # False
bool(0)         # False
bool("")        # False
bool([])        # False
bool({})        # False

# Check for None explicitly when 0 or "" are valid
if value is None:    # Checks identity
    ...
if value is not None:
    ...
```

### Import circular dependencies

```python
# BAD - circular import at module load
# file_a.py
from file_b import B
class A: ...

# file_b.py
from file_a import A  # Fails!
class B: ...

# GOOD - import inside function or use TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from file_a import A  # Only imported for type checking

class B:
    def method(self) -> "A":  # String annotation
        from file_a import A  # Runtime import
        return A()
```

---

## Performance Tips

### Use generators for large datasets

```python
# BAD - loads all into memory
def get_all_items():
    return [process(item) for item in huge_list]

# GOOD - yields one at a time
def get_all_items():
    for item in huge_list:
        yield process(item)
```

### Use sets for membership testing

```python
# BAD - O(n) lookup
if item in large_list:
    ...

# GOOD - O(1) lookup
large_set = set(large_list)
if item in large_set:
    ...
```

### Use `__slots__` for many instances

```python
# Without slots: each instance has a __dict__ (~200+ bytes)
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# With slots: fixed attributes, much less memory
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

---

## Quick Commands

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app

# Run specific test
uv run pytest tests/test_items.py::test_create_item -v

# Generate migration
uv run alembic revision --autogenerate -m "add users table"

# Apply migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn app.main:app --reload

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
