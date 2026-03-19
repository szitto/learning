# Project Setup

This section gets you from an empty directory to a working LangChain project with proper structure for growth.

## Install uv

If you do not have `uv` installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify it works:

```bash
uv --version
```

## Initialize the Project

Create a new project:

```bash
mkdir langchain-app
cd langchain-app
uv init
uv venv
```

## Install Dependencies

Add the core LangChain packages:

```bash
uv add langchain langchain-openai python-dotenv
```

This gives you:

- `langchain` - core framework and chains
- `langchain-openai` - OpenAI model integration
- `python-dotenv` - load API keys from `.env` files

For Anthropic models instead of (or in addition to) OpenAI:

```bash
uv add langchain-anthropic
```

For RAG capabilities (vector stores, embeddings):

```bash
uv add langchain-chroma tiktoken
```

For development tools:

```bash
uv add --dev pytest pytest-asyncio
```

## Configure API Keys

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-your-key-here
# Or for Anthropic:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

Load environment variables in your code:

```python
from dotenv import load_dotenv

load_dotenv()  # Reads .env file and sets environment variables
```

LangChain model classes automatically read from environment variables, so you do not need to pass API keys explicitly.

## Project Structure

Start with this layout:

```text
langchain-app/
├── app/
│   ├── __init__.py
│   ├── main.py           # Application entrypoint
│   ├── chains/
│   │   ├── __init__.py
│   │   └── qa.py         # Question-answering chain
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py  # Prompt templates
│   └── tools/
│       ├── __init__.py
│       └── search.py     # Custom tools
├── tests/
│   ├── __init__.py
│   └── test_chains.py
├── data/                 # Documents for RAG
├── .env                  # API keys (don't commit)
├── .gitignore
├── pyproject.toml
└── uv.lock
```

## Create Your First LangChain Script

Create `app/main.py`:

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

def main():
    # Initialize the model
    model = ChatOpenAI(model="gpt-4o-mini")

    # Make a simple call
    response = model.invoke([HumanMessage(content="Hello! What is LangChain?")])

    print(response.content)

if __name__ == "__main__":
    main()
```

Run it:

```bash
uv run python app/main.py
```

If you see a response from the LLM, your setup is working.

## Understanding the Model Interface

The `ChatOpenAI` class wraps OpenAI's chat completion API:

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o-mini",      # Model name
    temperature=0.7,           # Randomness (0-2, lower = more deterministic)
    max_tokens=1000,           # Maximum response length
    # api_key="..."            # Optional - defaults to OPENAI_API_KEY env var
)
```

Common models:

| Provider | Model | Use Case |
|----------|-------|----------|
| OpenAI | `gpt-4o` | Most capable, higher cost |
| OpenAI | `gpt-4o-mini` | Fast, cheap, good for most tasks |
| Anthropic | `claude-sonnet-4-20250514` | Strong reasoning, good at following instructions |
| Anthropic | `claude-3-5-haiku-20241022` | Fast, cheap |

## Using Anthropic Instead

To use Anthropic's Claude models:

```python
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

load_dotenv()

model = ChatAnthropic(model="claude-sonnet-4-20250514")
response = model.invoke([HumanMessage(content="Hello!")])
print(response.content)
```

The interface is identical to OpenAI. This is one of LangChain's main benefits - you can swap providers without changing your application logic.

## Message Types

LangChain uses typed messages to represent conversation turns:

```python
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)

messages = [
    SystemMessage(content="You are a helpful coding assistant."),
    HumanMessage(content="How do I read a file in Python?"),
    AIMessage(content="You can use the open() function..."),
    HumanMessage(content="Can you show me an example?"),
]

response = model.invoke(messages)
```

Understanding the message types:

- **SystemMessage**: Instructions for the AI's behavior. Usually comes first.
- **HumanMessage**: Input from the user.
- **AIMessage**: Previous responses from the AI (for conversation history).

## Common Setup Mistakes

### Not loading environment variables

```python
# BAD - API key not found
model = ChatOpenAI()  # Fails silently or errors

# GOOD - load .env first
from dotenv import load_dotenv
load_dotenv()
model = ChatOpenAI()  # Now it finds OPENAI_API_KEY
```

### Committing API keys

Never commit `.env` files. Add to `.gitignore` immediately.

### Installing wrong packages

LangChain has many packages. Common confusion:

- `langchain` - the framework (you need this)
- `langchain-core` - base classes (installed automatically with langchain)
- `langchain-openai` - OpenAI integration (install separately)
- `langchain-community` - community integrations (install if needed)

### Using deprecated imports

LangChain has restructured its imports. Use the new style:

```python
# OLD (deprecated)
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# NEW (correct)
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
```

## What You Should Have After This Step

By now, you should have:

- A project initialized with `uv init`
- LangChain packages installed
- API keys configured in `.env`
- A working script that calls an LLM
- Understanding of the basic model interface

Next, you will learn about prompts, output parsing, and the building blocks of LangChain applications.
