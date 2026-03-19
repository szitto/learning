# LangChain Cheatsheet

Quick reference for LangChain patterns and syntax.

---

## Installation

```bash
# Core
uv add langchain langchain-openai python-dotenv

# For Anthropic
uv add langchain-anthropic

# For RAG
uv add langchain-chroma tiktoken

# For agents
uv add langchain-community duckduckgo-search
```

---

## Setup

```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file

# Models read API keys from environment automatically
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

openai = ChatOpenAI(model="gpt-4o-mini")
anthropic = ChatAnthropic(model="claude-sonnet-4-20250514")
```

---

## Models

### Chat Models

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,    # 0-2, lower = deterministic
    max_tokens=1000,
)

# Call methods
response = model.invoke(messages)           # Single call
responses = model.batch([msgs1, msgs2])     # Parallel
for chunk in model.stream(messages):        # Streaming
    print(chunk.content)
await model.ainvoke(messages)               # Async
```

### Common Models

| Provider | Model | Notes |
|----------|-------|-------|
| OpenAI | `gpt-4o` | Most capable |
| OpenAI | `gpt-4o-mini` | Fast, cheap |
| Anthropic | `claude-sonnet-4-20250514` | Strong reasoning |
| Anthropic | `claude-3-5-haiku-20241022` | Fast, cheap |

---

## Messages

```python
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)

messages = [
    SystemMessage(content="You are helpful."),
    HumanMessage(content="Hello"),
    AIMessage(content="Hi there!"),
    HumanMessage(content="How are you?"),
]

response = model.invoke(messages)
print(response.content)
```

---

## Prompts

### Chat Prompt Template

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}."),
    ("human", "{question}"),
])

messages = prompt.invoke({"role": "teacher", "question": "What is Python?"})
```

### With History Placeholder

```python
from langchain_core.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])
```

### Partial Templates

```python
partial_prompt = prompt.partial(role="assistant")
messages = partial_prompt.invoke({"question": "Hello"})
```

---

## Output Parsers

### String

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
text = parser.invoke(ai_message)  # Extracts .content
```

### JSON

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
data = parser.invoke(ai_message)  # Returns dict
```

### Pydantic (Structured)

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

# Modern approach - use with_structured_output
structured_model = model.with_structured_output(Person)
person = structured_model.invoke("John is 30 years old")
print(person.name)  # "John"
```

---

## LCEL (Chains)

### Basic Chain

```python
chain = prompt | model | parser
result = chain.invoke({"question": "Hello"})
```

### Parallel Execution

```python
from langchain_core.runnables import RunnableParallel

chain = RunnableParallel(
    summary=summary_chain,
    translation=translation_chain,
) | merge_step
```

### Passthrough

```python
from langchain_core.runnables import RunnablePassthrough

chain = {
    "context": retriever,
    "question": RunnablePassthrough(),
} | prompt | model
```

### Custom Functions

```python
from langchain_core.runnables import RunnableLambda

def process(x):
    return x.upper()

chain = prompt | model | StrOutputParser() | RunnableLambda(process)
```

### Branching

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: "math" in x["q"], math_chain),
    general_chain,  # default
)
```

### Fallbacks & Retries

```python
chain_with_fallback = primary_chain.with_fallbacks([backup_chain])
chain_with_retry = chain.with_retry(stop_after_attempt=3)
```

---

## RAG

### Load Documents

```python
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    DirectoryLoader,
)

loader = DirectoryLoader("docs/", glob="**/*.md")
documents = loader.load()
```

### Split

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(documents)
```

### Embed & Store

```python
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma.from_documents(
    chunks,
    embeddings,
    persist_directory="./db",
)
```

### Retrieve

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",  # or "mmr"
    search_kwargs={"k": 4},
)

docs = retriever.invoke("search query")
```

### RAG Chain

```python
def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

answer = rag_chain.invoke("What is X?")
```

---

## Tools & Agents

### Create Tool

```python
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search for information. Use when you need current data."""
    return f"Results for: {query}"
```

### Create Agent

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(model, [search], prompt)
executor = AgentExecutor(agent=agent, tools=[search], verbose=True)

result = executor.invoke({"input": "Search for Python news"})
```

### Built-in Tools

```python
from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()
tools = [search]
```

---

## Memory

### Manual History

```python
from langchain_core.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

history = []
chain = prompt | model

response = chain.invoke({"history": history, "input": "Hi"})
history.append(HumanMessage(content="Hi"))
history.append(response)
```

### With RunnableWithMessageHistory

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

store = {}

def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

config = {"configurable": {"session_id": "user123"}}
response = chain_with_memory.invoke({"input": "Hi"}, config=config)
```

---

## Streaming

### Basic

```python
for chunk in chain.stream({"input": "Hello"}):
    print(chunk, end="", flush=True)
```

### Async

```python
async for chunk in chain.astream({"input": "Hello"}):
    print(chunk, end="")
```

### FastAPI SSE

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.get("/chat")
async def chat(q: str):
    async def generate():
        async for chunk in chain.astream({"input": q}):
            yield {"data": chunk}
    return EventSourceResponse(generate())
```

---

## Caching

```python
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache, SQLiteCache

# In-memory
set_llm_cache(InMemoryCache())

# Persistent
set_llm_cache(SQLiteCache(database_path=".langchain.db"))
```

---

## Callbacks & Tracing

### LangSmith (set env vars)

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=my-project
```

### Token Counting

```python
from langchain.callbacks import get_openai_callback

with get_openai_callback() as cb:
    result = chain.invoke({"input": "Hello"})
    print(f"Tokens: {cb.total_tokens}, Cost: ${cb.total_cost:.4f}")
```

---

## Error Handling

```python
# Retries
chain = chain.with_retry(stop_after_attempt=3)

# Fallbacks
chain = primary.with_fallbacks([backup])

# Timeout (async)
import asyncio
result = await asyncio.wait_for(chain.ainvoke(input), timeout=30)
```

---

## Common Patterns

### Q&A over Documents

```python
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | qa_prompt
    | model
    | StrOutputParser()
)
```

### Conversational RAG

```python
chain = (
    RunnablePassthrough.assign(
        context=lambda x: retriever.invoke(x["question"])
    )
    | prompt
    | model
    | StrOutputParser()
)

with_memory = RunnableWithMessageHistory(chain, get_history, ...)
```

### Multi-Step Reasoning

```python
chain = (
    {"analysis": analysis_chain}
    | {"summary": summary_chain, "analysis": lambda x: x["analysis"]}
    | final_chain
)
```

### Router

```python
from langchain_core.runnables import RunnableBranch

router = RunnableBranch(
    (lambda x: "code" in x["q"].lower(), code_chain),
    (lambda x: "math" in x["q"].lower(), math_chain),
    general_chain,
)
```

---

## Quick Commands

```bash
# Run script
uv run python app/main.py

# Test
uv run pytest

# Format
uv run ruff format .

# Lint
uv run ruff check .
```

---

## Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...

# Optional providers
ANTHROPIC_API_KEY=sk-ant-...

# LangSmith (recommended for production)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=my-project

# Redis (for caching/memory)
REDIS_URL=redis://localhost:6379
```
