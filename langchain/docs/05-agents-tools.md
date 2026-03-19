# Agents and Tools

Agents are LLMs that can decide what actions to take. Instead of following a fixed chain, they reason about the task and choose from available tools.

## What Is an Agent?

A chain is like a recipe - fixed steps in order.

An agent is like a chef - decides what to do based on the situation.

```text
Chain:   Input → Step A → Step B → Step C → Output

Agent:   Input → Think → Choose Tool → Observe → Think → Choose Tool → ... → Output
```

## When to Use Agents

Use agents when:

- The task requires **multiple steps** that depend on intermediate results
- You need **external tool access** (search, calculations, APIs)
- The **path is not predetermined** - different queries need different approaches
- You want the LLM to **reason about what to do**

Use chains when:

- The workflow is **predictable**
- You want **more control** over execution
- **Latency matters** - agents make multiple LLM calls
- The task is **simple enough** for a fixed pipeline

## Tools

Tools are functions the agent can call. Each tool has:

- A name
- A description (the LLM reads this to decide when to use it)
- Input schema
- The actual function

### Creating Tools

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for.
    """
    # In reality, call a weather API
    return f"The weather in {city} is sunny, 22°C"

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression like '2 + 2' or '10 * 5'.
    """
    try:
        result = eval(expression)  # In production, use a safe math parser
        return str(result)
    except Exception as e:
        return f"Error: {e}"
```

The docstring is critical - it tells the LLM when and how to use the tool.

### Tool with complex inputs

```python
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum results to return")

@tool(args_schema=SearchInput)
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information."""
    # Call search API
    return f"Found {max_results} results for: {query}"
```

### Built-in tools

```python
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Web search
search = DuckDuckGoSearchRun()

# Wikipedia
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

tools = [search, wikipedia]
```

## Creating an Agent

### Using create_react_agent (recommended)

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

load_dotenv()

# Define tools
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: Sunny, 22°C"

@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    return str(eval(expression))

tools = [get_weather, calculate]

# Get a pre-built ReAct prompt
prompt = hub.pull("hwchase17/react")

# Create the model
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Create the agent
agent = create_react_agent(model, tools, prompt)

# Wrap in executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # See the agent's reasoning
    max_iterations=10,
)

# Run
result = agent_executor.invoke({
    "input": "What's the weather in Tokyo and what is 25 * 4?"
})
print(result["output"])
```

### Using Tool-Calling Models (modern approach)

OpenAI and Anthropic support native tool calling:

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(model, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = agent_executor.invoke({"input": "What's the weather in Paris?"})
```

## Understanding Agent Execution

When you call an agent, this happens:

1. **Think**: LLM receives the input and tool descriptions
2. **Act**: LLM decides to call a tool with specific inputs
3. **Observe**: Tool executes, result is added to context
4. **Repeat**: LLM sees the result, decides if more tools are needed
5. **Finish**: LLM generates final response

Example trace:

```text
Input: "What's the weather in Tokyo and what is 25 * 4?"

Thought: I need to get the weather and do a calculation. Let me start with weather.
Action: get_weather
Action Input: Tokyo
Observation: Weather in Tokyo: Sunny, 22°C

Thought: Now I need to calculate 25 * 4.
Action: calculate
Action Input: 25 * 4
Observation: 100

Thought: I have both pieces of information now.
Final Answer: The weather in Tokyo is sunny at 22°C, and 25 × 4 = 100.
```

## Agent Configuration

### Limiting iterations

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=5,  # Stop after 5 tool calls
    max_execution_time=30,  # Stop after 30 seconds
)
```

### Handling errors

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True,  # Retry on parse errors
    # Or provide custom handler
    handle_parsing_errors="Please format your response correctly.",
)
```

### Early stopping

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    early_stopping_method="generate",  # Generate final answer when stuck
)
```

## Custom Agent Prompts

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant. Use tools to find accurate information.

Available tools: {tool_names}

Tool descriptions:
{tools}

Always verify information before answering. Cite your sources."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(model, tools, prompt)
```

## Retriever as a Tool

Combine RAG with agents:

```python
from langchain.tools.retriever import create_retriever_tool

# Assuming you have a retriever from RAG setup
retriever_tool = create_retriever_tool(
    retriever,
    name="search_docs",
    description="Search internal documentation. Use for questions about company policies, procedures, or products.",
)

tools = [retriever_tool, get_weather, calculate]
```

## Structured Tool Output

Return structured data from tools:

```python
from pydantic import BaseModel

class WeatherResult(BaseModel):
    city: str
    temperature: float
    condition: str
    humidity: int

@tool
def get_detailed_weather(city: str) -> WeatherResult:
    """Get detailed weather information for a city."""
    return WeatherResult(
        city=city,
        temperature=22.5,
        condition="Sunny",
        humidity=65,
    )
```

## Async Agents

```python
import asyncio

async def main():
    result = await agent_executor.ainvoke({
        "input": "What's the weather in London?"
    })
    print(result["output"])

asyncio.run(main())
```

## Streaming Agent Output

```python
async for event in agent_executor.astream_events(
    {"input": "What's the weather?"},
    version="v2",
):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
    elif event["event"] == "on_tool_start":
        print(f"\n[Using tool: {event['name']}]")
```

## Common Mistakes

### Vague tool descriptions

```python
# BAD - LLM won't know when to use this
@tool
def search(q: str) -> str:
    """Search."""
    ...

# GOOD - clear description
@tool
def search_products(query: str) -> str:
    """Search the product catalog. Use this when the user asks about
    product availability, prices, or specifications."""
    ...
```

### Not handling tool errors

```python
# BAD - crashes on error
@tool
def fetch_data(url: str) -> str:
    """Fetch data from URL."""
    return requests.get(url).text

# GOOD - graceful error handling
@tool
def fetch_data(url: str) -> str:
    """Fetch data from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching {url}: {e}"
```

### Too many tools

Agents get confused with many tools. Keep it focused:

```python
# BAD - 20 tools, agent gets confused
tools = [tool1, tool2, ..., tool20]

# GOOD - focused set for the task
tools = [search_docs, calculate, get_weather]
```

### Not testing tool independently

```python
# Test tools before using in agent
result = get_weather.invoke("Tokyo")
print(result)  # Verify it works
```

## What You Should Have After This Step

By now, you should understand:

- What agents are and when to use them
- How to create tools with `@tool` decorator
- How to create agents with `create_tool_calling_agent`
- The Think → Act → Observe loop
- Agent configuration: iterations, timeouts, error handling
- How to combine RAG retrievers with agents

Next, you will learn about memory and state management for conversational applications.
