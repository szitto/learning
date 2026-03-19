# LangChain Overview

## What LangChain Is

LangChain is a framework for building applications powered by large language models (LLMs). It provides:

- **Abstractions** over different LLM providers (OpenAI, Anthropic, local models)
- **Composability** through chains that connect multiple operations
- **Tools** for retrieval, agents, memory, and output parsing
- **Integrations** with vector stores, databases, APIs, and other services

Think of it as the "web framework" for LLM applications. Just as FastAPI gives you structure for building APIs, LangChain gives you structure for building LLM-powered features.

## When to Use LangChain

LangChain is a good fit when you need:

- **Multiple LLM calls** chained together
- **Retrieval Augmented Generation (RAG)** - combining LLMs with your own data
- **Agents** that can decide what actions to take
- **Memory** across conversation turns
- **Structured output** parsing from LLM responses
- **Provider flexibility** - ability to swap OpenAI for Anthropic easily

## When NOT to Use LangChain

LangChain adds complexity. For simple use cases, you might be better off with direct API calls:

- **Single LLM call** - just use the OpenAI/Anthropic SDK directly
- **Simple chat interface** - the provider SDKs handle this well
- **Highly custom workflows** - LangChain's abstractions might get in the way
- **Minimal dependencies** - LangChain pulls in many packages

If you are unsure, start with direct API calls. Add LangChain when you find yourself building the same patterns repeatedly.

## Core Concepts

### Models

LangChain wraps LLM providers with a consistent interface:

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Same interface, different providers
openai_model = ChatOpenAI(model="gpt-4o")
anthropic_model = ChatAnthropic(model="claude-sonnet-4-20250514")

# Both work the same way
response = openai_model.invoke("Hello!")
```

### Prompts

Templates for constructing LLM inputs:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])

# Fill in the template
messages = prompt.invoke({"question": "What is Python?"})
```

### Chains

Sequences of operations connected together:

```python
chain = prompt | model | output_parser
result = chain.invoke({"question": "What is Python?"})
```

### Retrieval

Combining LLMs with external data sources:

```python
# Store documents in a vector database
vectorstore.add_documents(documents)

# Retrieve relevant documents based on a query
relevant_docs = vectorstore.similarity_search("How do I deploy?")

# Pass retrieved docs to the LLM
chain.invoke({"context": relevant_docs, "question": query})
```

### Agents

LLMs that can decide what actions to take:

```python
agent = create_react_agent(model, tools, prompt)
result = agent.invoke({"input": "What's the weather in Tokyo?"})
# Agent decides to call weather_tool, then formats response
```

## LangChain Ecosystem

The LangChain ecosystem has several packages:

| Package | Purpose |
|---------|---------|
| `langchain-core` | Base abstractions (prompts, messages, output parsers) |
| `langchain` | Chains, agents, retrieval patterns |
| `langchain-openai` | OpenAI integration |
| `langchain-anthropic` | Anthropic integration |
| `langchain-community` | Community integrations (vector stores, tools) |
| `langgraph` | Stateful, multi-actor applications |
| `langsmith` | Observability and evaluation platform |

You typically install `langchain` plus provider-specific packages like `langchain-openai`.

## What You Will Build

Through this guide, you will build increasingly complex applications:

1. **Basic chat** - prompt templates, model calls, output parsing
2. **Document Q&A** - RAG pipeline with vector store
3. **Conversational agent** - memory, tools, and autonomous reasoning
4. **Production service** - streaming, caching, observability

## What This Guide Covers

- Project setup with uv
- Working with different LLM providers
- Prompt engineering and templates
- LangChain Expression Language (LCEL)
- Document loading and text splitting
- Vector stores and embeddings
- Retrieval chains
- Agents and tool use
- Conversation memory
- Streaming responses
- Error handling and retries
- Observability with LangSmith

## What This Guide Does Not Cover

- Fine-tuning models
- Training embeddings
- Self-hosting LLMs
- LangGraph (stateful agents) - this deserves its own guide
- Every LangChain integration - we focus on common patterns

## Recommended Reading Order

Read the docs in this order:

1. `docs/00-overview.md` (you are here)
2. `docs/01-project-setup.md`
3. `docs/02-llm-basics.md`
4. `docs/03-chains-lcel.md`
5. `docs/04-rag-fundamentals.md`
6. `docs/05-agents-tools.md`
7. `docs/06-memory-state.md`
8. `docs/07-production.md`
