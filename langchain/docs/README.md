# LangChain Production Guide

A documentation set teaching developers how to build LLM-powered applications with LangChain.

## What This Is

This guide walks you through building production-ready applications with LangChain, from basic LLM calls to complex agents and RAG systems.

## Target Audience

Developers who understand Python basics and want to build applications that use large language models. Prior AI/ML experience is not required.

## Tech Stack

- **Framework:** LangChain
- **LLM Providers:** OpenAI, Anthropic (examples for both)
- **Vector Store:** ChromaDB (local), Pinecone (production)
- **Dependency Management:** uv
- **Testing:** pytest
- **Observability:** LangSmith

## Reading Order

### Core Path

1. [Overview](00-overview.md) - What LangChain is and when to use it
2. [Project Setup](01-project-setup.md) - Bootstrap a LangChain project
3. [LLM Basics](02-llm-basics.md) - Models, prompts, and output parsing
4. [Chains and LCEL](03-chains-lcel.md) - Composing operations with LangChain Expression Language
5. [RAG Fundamentals](04-rag-fundamentals.md) - Retrieval Augmented Generation
6. [Agents and Tools](05-agents-tools.md) - Autonomous LLM agents
7. [Memory and State](06-memory-state.md) - Conversation history and state management
8. [Production Concerns](07-production.md) - Streaming, caching, observability, error handling

## Quick Start

```bash
# Initialize project
uv init
uv venv
uv add langchain langchain-openai python-dotenv

# Set your API key
echo "OPENAI_API_KEY=sk-..." > .env

# Run your first chain
uv run python app/main.py
```

## Quick Reference

See [../CHEATSHEET.md](../CHEATSHEET.md) for a condensed reference covering:

- Core components
- LCEL patterns
- Common chain types
- RAG setup
- Agent patterns
- Memory types
- Streaming
- Error handling
