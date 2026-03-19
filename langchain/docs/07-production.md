# Production Concerns

Taking LangChain applications from development to production requires attention to streaming, caching, observability, error handling, and cost management.

## Streaming

Users expect immediate feedback. Streaming shows output as it generates instead of waiting for completion.

### Basic streaming

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

model = ChatOpenAI(model="gpt-4o-mini", streaming=True)
prompt = ChatPromptTemplate.from_template("Explain {topic} in detail.")

chain = prompt | model

for chunk in chain.stream({"topic": "quantum computing"}):
    print(chunk.content, end="", flush=True)
```

### Async streaming

```python
async def stream_response(question: str):
    async for chunk in chain.astream({"topic": question}):
        yield chunk.content
```

### Streaming in FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/chat")
async def chat(question: str):
    async def generate():
        async for chunk in chain.astream({"topic": question}):
            yield chunk.content

    return StreamingResponse(generate(), media_type="text/plain")
```

### Server-Sent Events (SSE)

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

@app.get("/chat/stream")
async def chat_stream(question: str):
    async def generate():
        async for chunk in chain.astream({"topic": question}):
            yield {"event": "message", "data": chunk.content}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())
```

### Stream events (for agents and complex chains)

```python
async for event in agent_executor.astream_events(
    {"input": question},
    version="v2",
):
    kind = event["event"]

    if kind == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if content:
            print(content, end="")

    elif kind == "on_tool_start":
        print(f"\n[Tool: {event['name']}]")

    elif kind == "on_tool_end":
        print(f"[Result: {event['data']['output']}]")
```

## Caching

Avoid redundant LLM calls for identical inputs.

### In-memory cache

```python
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache

set_llm_cache(InMemoryCache())

# First call - hits the API
response1 = model.invoke("What is 2+2?")

# Second identical call - uses cache
response2 = model.invoke("What is 2+2?")
```

### SQLite cache (persistent)

```python
from langchain.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path=".langchain.db"))
```

### Redis cache (production)

```python
from langchain.cache import RedisCache
import redis

redis_client = redis.Redis.from_url("redis://localhost:6379")
set_llm_cache(RedisCache(redis_client))
```

### Semantic cache

Cache based on meaning, not exact match:

```python
from langchain.cache import RedisSemanticCache
from langchain_openai import OpenAIEmbeddings

set_llm_cache(RedisSemanticCache(
    redis_url="redis://localhost:6379",
    embedding=OpenAIEmbeddings(),
    score_threshold=0.95,  # How similar queries must be
))

# These might share a cache entry:
model.invoke("What is the capital of France?")
model.invoke("What's France's capital city?")
```

## Observability with LangSmith

LangSmith provides tracing, debugging, and evaluation for LangChain apps.

### Setup

```bash
pip install langsmith
```

Set environment variables:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=my-project
```

Traces are now automatically sent to LangSmith.

### Manual tracing

```python
from langsmith import traceable

@traceable(name="my_function")
def process_query(query: str) -> str:
    result = chain.invoke({"input": query})
    return result
```

### Adding metadata

```python
result = chain.invoke(
    {"input": "Hello"},
    config={
        "metadata": {"user_id": "123", "request_id": "abc"},
        "tags": ["production", "v2"],
    },
)
```

### Run evaluation

```python
from langsmith.evaluation import evaluate

def correctness(run, example):
    """Check if the answer is correct."""
    prediction = run.outputs["output"]
    reference = example.outputs["expected"]
    return {"score": 1 if prediction == reference else 0}

results = evaluate(
    chain.invoke,
    data="my-dataset",
    evaluators=[correctness],
)
```

## Error Handling

### Retries

```python
chain_with_retry = chain.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)
```

### Fallbacks

```python
from langchain_anthropic import ChatAnthropic

primary = ChatOpenAI(model="gpt-4o")
fallback = ChatAnthropic(model="claude-sonnet-4-20250514")

model_with_fallback = primary.with_fallbacks([fallback])
```

### Graceful degradation

```python
from langchain_core.runnables import RunnableLambda

def safe_invoke(chain):
    def wrapper(input):
        try:
            return chain.invoke(input)
        except Exception as e:
            return {"error": str(e), "fallback": "Unable to process request"}
    return RunnableLambda(wrapper)

safe_chain = safe_invoke(chain)
```

### Timeout

```python
import asyncio

async def invoke_with_timeout(chain, input, timeout=30):
    try:
        return await asyncio.wait_for(
            chain.ainvoke(input),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return {"error": "Request timed out"}
```

## Rate Limiting

### Simple rate limiter

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = Lock()

    def wait(self):
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [c for c in self.calls if now - c < 60]

            if len(self.calls) >= self.calls_per_minute:
                sleep_time = 60 - (now - self.calls[0])
                time.sleep(sleep_time)

            self.calls.append(time.time())

rate_limiter = RateLimiter(calls_per_minute=60)

def rate_limited_invoke(input):
    rate_limiter.wait()
    return chain.invoke(input)
```

### Using tenacity for retries with backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
)
def invoke_with_retry(input):
    return chain.invoke(input)
```

## Cost Management

### Track token usage

```python
from langchain.callbacks import get_openai_callback

with get_openai_callback() as cb:
    result = chain.invoke({"input": "Hello"})
    print(f"Tokens: {cb.total_tokens}")
    print(f"Cost: ${cb.total_cost:.4f}")
```

### Token counting before calling

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

tokens = count_tokens("Your prompt here")
if tokens > 4000:
    # Truncate or summarize
    pass
```

### Cost estimation

```python
COST_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}

def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    costs = COST_PER_1K_TOKENS.get(model, {"input": 0, "output": 0})
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000
```

## Testing

### Unit testing chains

```python
import pytest
from unittest.mock import MagicMock

def test_chain_structure():
    # Test that chain is properly constructed
    assert chain.first == prompt
    assert chain.last == parser

def test_with_mock_model():
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="Test response")

    test_chain = prompt | mock_model | parser
    result = test_chain.invoke({"input": "Hello"})

    assert result == "Test response"
    mock_model.invoke.assert_called_once()
```

### Integration testing

```python
@pytest.mark.integration
def test_full_chain():
    """Test with real LLM (use sparingly, costs money)."""
    result = chain.invoke({"input": "What is 2+2?"})
    assert "4" in result.lower()
```

### Testing with fixtures

```python
@pytest.fixture
def mock_retriever():
    from langchain_core.documents import Document

    mock = MagicMock()
    mock.invoke.return_value = [
        Document(page_content="Relevant content", metadata={"source": "test"})
    ]
    return mock

def test_rag_chain(mock_retriever):
    chain = build_rag_chain(retriever=mock_retriever)
    result = chain.invoke("Question?")
    assert result is not None
```

## Configuration Management

### Settings class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str | None = None
    langsmith_api_key: str | None = None

    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000

    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600

    class Config:
        env_file = ".env"

settings = Settings()
```

### Environment-based model selection

```python
import os

def get_model():
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ChatOpenAI(model="gpt-4o", temperature=0)
    else:
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
```

## Common Production Mistakes

### Not handling API failures

Always wrap LLM calls in error handling. APIs fail, rate limits hit, networks timeout.

### Ignoring costs

LLM calls are expensive. Cache aggressively, trim context, use cheaper models when possible.

### No observability

Without tracing, debugging production issues is nearly impossible. Use LangSmith or similar.

### Blocking on LLM calls

Use async for web applications. Streaming improves perceived latency significantly.

### Not testing edge cases

Test with long inputs, empty inputs, malicious inputs, and concurrent requests.

## What You Should Have After This Step

By now, you should understand:

- Streaming for better user experience
- Caching strategies (in-memory, Redis, semantic)
- Observability with LangSmith
- Error handling: retries, fallbacks, timeouts
- Rate limiting and cost management
- Testing strategies
- Configuration management

You now have the knowledge to build production-ready LangChain applications.
