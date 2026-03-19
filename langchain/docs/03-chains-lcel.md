# Chains and LCEL

LangChain Expression Language (LCEL) is how you compose operations into chains. It is the core pattern for building LangChain applications.

## What Is LCEL?

LCEL uses the pipe operator (`|`) to connect components:

```python
chain = prompt | model | parser
```

Each component:

- Takes an input
- Produces an output
- Passes that output to the next component

This is similar to Unix pipes or RxJS observables.

## The Runnable Interface

Every LCEL component implements the `Runnable` interface:

```python
# All components support these methods:
chain.invoke(input)        # Single call
chain.stream(input)        # Streaming
chain.batch([input1, ...]) # Parallel calls
await chain.ainvoke(input) # Async
```

This consistency means you can compose any components together and get all these capabilities automatically.

## Basic Chain

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])

model = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

# Create the chain
chain = prompt | model | parser

# Use it
response = chain.invoke({"question": "What is LCEL?"})
print(response)
```

## Understanding Data Flow

Let's trace what happens when you call `chain.invoke()`:

```python
chain = prompt | model | parser

# When you call:
result = chain.invoke({"question": "Hello"})

# This happens:
# 1. prompt.invoke({"question": "Hello"})
#    → Returns: [SystemMessage(...), HumanMessage("Hello")]
#
# 2. model.invoke([SystemMessage(...), HumanMessage("Hello")])
#    → Returns: AIMessage(content="Hi there!")
#
# 3. parser.invoke(AIMessage(content="Hi there!"))
#    → Returns: "Hi there!"
```

## RunnableLambda - Custom Functions

Convert any function into a chain component:

```python
from langchain_core.runnables import RunnableLambda

def add_exclamation(text: str) -> str:
    return text + "!"

# Wrap the function
add_exclamation_runnable = RunnableLambda(add_exclamation)

# Use in a chain
chain = prompt | model | StrOutputParser() | add_exclamation_runnable
```

Shorter syntax using a decorator:

```python
from langchain_core.runnables import chain as chain_decorator

@chain_decorator
def add_exclamation(text: str) -> str:
    return text + "!"

# Now it's already a Runnable
my_chain = prompt | model | StrOutputParser() | add_exclamation
```

## RunnablePassthrough - Pass Input Through

Sometimes you need to pass the original input alongside transformed data:

```python
from langchain_core.runnables import RunnablePassthrough

# Pass the question through while also generating context
chain = {
    "context": retriever,  # Gets documents
    "question": RunnablePassthrough(),  # Passes the original question
} | prompt | model | parser
```

## RunnableParallel - Run Steps in Parallel

Execute multiple chains simultaneously:

```python
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel(
    summary=summary_chain,
    translation=translation_chain,
    sentiment=sentiment_chain,
)

# All three run in parallel, results combined into a dict
results = parallel_chain.invoke({"text": "Some long article..."})

print(results["summary"])
print(results["translation"])
print(results["sentiment"])
```

Dict syntax is shorthand for `RunnableParallel`:

```python
# These are equivalent:
chain1 = RunnableParallel(a=chain_a, b=chain_b) | next_step
chain2 = {"a": chain_a, "b": chain_b} | next_step
```

## Branching with RunnableBranch

Choose different paths based on conditions:

```python
from langchain_core.runnables import RunnableBranch

def is_math_question(input: dict) -> bool:
    question = input["question"].lower()
    return any(word in question for word in ["calculate", "math", "+", "-", "*", "/"])

branch = RunnableBranch(
    (is_math_question, math_chain),
    # Default branch (no condition)
    general_chain,
)

# Routes to math_chain if is_math_question returns True
result = branch.invoke({"question": "Calculate 2+2"})
```

## Binding Arguments

Pre-configure a component with fixed arguments:

```python
# Create a model with specific settings
model_with_tools = model.bind(
    tools=[weather_tool, search_tool],
    tool_choice="auto",
)

# Or set stop sequences
model_with_stop = model.bind(stop=["\n\n", "END"])

chain = prompt | model_with_tools | parser
```

## Configurable Chains

Make parts of a chain configurable at runtime:

```python
from langchain_core.runnables import ConfigurableField

model = ChatOpenAI(model="gpt-4o-mini").configurable_fields(
    model_name=ConfigurableField(
        id="model_name",
        name="Model Name",
        description="The model to use",
    )
)

chain = prompt | model | parser

# Use default model
result = chain.invoke({"question": "Hello"})

# Override at runtime
result = chain.with_config(
    configurable={"model_name": "gpt-4o"}
).invoke({"question": "Hello"})
```

## Fallbacks

Handle failures gracefully:

```python
# If primary model fails, try the fallback
model_with_fallback = primary_model.with_fallbacks([fallback_model])

# With retries
chain_with_retry = chain.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)
```

## Common Chain Patterns

### Sequential processing

```python
chain = step1 | step2 | step3
```

### Parallel then merge

```python
chain = {"a": chain_a, "b": chain_b} | merge_results
```

### Context injection

```python
chain = {
    "context": get_context_chain,
    "question": RunnablePassthrough(),
} | qa_prompt | model | parser
```

### Multi-step reasoning

```python
chain = (
    initial_prompt | model | parser
    | {"analysis": RunnablePassthrough()} 
    | followup_prompt | model | parser
)
```

## Debugging Chains

### View intermediate steps

```python
from langchain_core.tracers import ConsoleCallbackHandler

chain.invoke(
    {"question": "Hello"},
    config={"callbacks": [ConsoleCallbackHandler()]},
)
```

### Get the chain structure

```python
print(chain)  # Shows the chain structure
chain.get_graph().print_ascii()  # ASCII visualization
```

### Add logging

```python
from langchain_core.runnables import RunnableLambda

def log_step(x):
    print(f"Current value: {x}")
    return x

chain = prompt | RunnableLambda(log_step) | model | RunnableLambda(log_step) | parser
```

## Async Chains

LCEL chains automatically support async:

```python
import asyncio

async def main():
    # Same chain works async
    result = await chain.ainvoke({"question": "Hello"})
    
    # Async streaming
    async for chunk in chain.astream({"question": "Hello"}):
        print(chunk, end="")
    
    # Async batch
    results = await chain.abatch([
        {"question": "Q1"},
        {"question": "Q2"},
    ])

asyncio.run(main())
```

## Common Mistakes

### Not handling dict vs string inputs

```python
# If your chain expects a dict:
chain.invoke({"question": "Hello"})  # ✓

# But some components output strings:
chain.invoke("Hello")  # ✗ May fail if prompt expects dict

# Fix with RunnableLambda:
chain = RunnableLambda(lambda x: {"question": x}) | prompt | model
```

### Forgetting output types

```python
# model outputs AIMessage, not string
chain = prompt | model
result = chain.invoke({"question": "Hello"})
print(result.content)  # Need .content

# Add parser to get string directly
chain = prompt | model | StrOutputParser()
result = chain.invoke({"question": "Hello"})
print(result)  # Already a string
```

### Not matching parallel outputs to prompt inputs

```python
# Prompt expects {context, question}
prompt = ChatPromptTemplate.from_template(
    "Context: {context}\nQuestion: {question}"
)

# Parallel must produce matching keys
chain = {
    "context": retriever,    # Must produce 'context'
    "question": RunnablePassthrough(),  # Must produce 'question'
} | prompt | model
```

## What You Should Have After This Step

By now, you should understand:

- The LCEL pipe syntax for composing chains
- How data flows through a chain
- RunnableLambda, RunnablePassthrough, RunnableParallel
- How to branch, bind arguments, and configure chains
- Fallbacks and retries
- Debugging techniques

Next, you will learn how to build RAG (Retrieval Augmented Generation) systems that combine LLMs with your own data.
