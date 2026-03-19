# LLM Basics

This section covers the fundamental building blocks: prompts, model calls, and output parsing.

## Prompt Templates

Hardcoding prompts is fine for experiments, but real applications need templates:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that speaks {language}."),
    ("human", "{question}"),
])

# Fill in the template
messages = prompt.invoke({
    "language": "Spanish",
    "question": "What is the capital of France?",
})

print(messages)
# [SystemMessage(content='You are a helpful assistant that speaks Spanish.'),
#  HumanMessage(content='What is the capital of France?')]
```

Understanding the syntax:

- **`("system", "...")`**: Creates a SystemMessage. The tuple format is `(role, content)`.
- **`{language}`**: A placeholder that gets filled when you call `invoke()`.
- **`prompt.invoke(dict)`**: Returns a list of messages with placeholders filled in.

## Prompt Template Patterns

### Simple string template

```python
from langchain_core.prompts import PromptTemplate

# For simple string output (not chat messages)
prompt = PromptTemplate.from_template(
    "Summarize this text in {num_sentences} sentences:\n\n{text}"
)

result = prompt.invoke({
    "num_sentences": 3,
    "text": "Long article here...",
})
# Returns a string, not messages
```

### Chat template with examples

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You translate text to {language}."),
    ("human", "Hello"),
    ("ai", "Hola"),
    ("human", "Goodbye"),
    ("ai", "Adiós"),
    ("human", "{text}"),
])
```

### Partial templates

```python
# Pre-fill some values
partial_prompt = prompt.partial(language="French")

# Later, only need to provide the remaining values
messages = partial_prompt.invoke({"question": "How are you?"})
```

## Invoking Models

There are several ways to call a model:

### invoke() - Single call, wait for full response

```python
response = model.invoke(messages)
print(response.content)
```

### stream() - Get response as it generates

```python
for chunk in model.stream(messages):
    print(chunk.content, end="", flush=True)
```

### batch() - Multiple calls in parallel

```python
responses = model.batch([
    [HumanMessage(content="What is 2+2?")],
    [HumanMessage(content="What is 3+3?")],
])

for r in responses:
    print(r.content)
```

### ainvoke() - Async version

```python
import asyncio

async def main():
    response = await model.ainvoke(messages)
    print(response.content)

asyncio.run(main())
```

## Output Parsing

LLMs return text, but you often want structured data. Output parsers convert text to Python objects.

### String output parser

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
result = parser.invoke(response)  # Extracts .content as a string
```

### JSON output parser

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ("system", "Return a JSON object with 'name' and 'age' fields."),
    ("human", "Generate a random person."),
])

# The model's response should be valid JSON
response = model.invoke(prompt.invoke({}))
data = parser.invoke(response)  # Returns a Python dict
```

### Pydantic output parser

For type-safe structured output:

```python
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="The person's full name")
    age: int = Field(description="The person's age in years")
    occupation: str = Field(description="The person's job")

parser = PydanticOutputParser(pydantic_object=Person)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract person information from the text.\n{format_instructions}"),
    ("human", "{text}"),
])

# Include format instructions in the prompt
formatted_prompt = prompt.partial(
    format_instructions=parser.get_format_instructions()
)

chain = formatted_prompt | model | parser
person = chain.invoke({"text": "John Smith is a 35 year old engineer."})

print(person.name)  # "John Smith"
print(person.age)   # 35
```

### Structured output (recommended for OpenAI/Anthropic)

Modern models support structured output natively:

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

# Use with_structured_output for guaranteed structure
structured_model = model.with_structured_output(Person)

person = structured_model.invoke("John Smith is a 35 year old engineer.")
print(person.name)  # "John Smith"
```

This is more reliable than output parsers because the model is constrained to produce valid output.

## Few-Shot Prompting

Include examples to guide the model:

```python
from langchain_core.prompts import FewShotChatMessagePromptTemplate

examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "fast", "output": "slow"},
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}"),
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

final_prompt = ChatPromptTemplate.from_messages([
    ("system", "You give the opposite of words."),
    few_shot_prompt,
    ("human", "{word}"),
])

response = model.invoke(final_prompt.invoke({"word": "hot"}))
print(response.content)  # "cold"
```

## Dynamic Few-Shot Selection

Select relevant examples based on the input:

```python
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

examples = [
    {"input": "What's 2+2?", "output": "4"},
    {"input": "How do I make pasta?", "output": "Boil water, add pasta..."},
    {"input": "What's the capital of France?", "output": "Paris"},
]

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(),
    Chroma,
    k=2,  # Select 2 most similar examples
)

# When user asks a math question, it selects the math example
selected = example_selector.select_examples({"input": "What's 5+5?"})
```

## Putting It Together

A complete example combining prompts, models, and parsing:

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Components
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Be concise."),
    ("human", "{question}"),
])

parser = StrOutputParser()

# Chain them together (covered in detail next section)
chain = prompt | model | parser

# Use the chain
response = chain.invoke({"question": "What is photosynthesis?"})
print(response)
```

## Common Mistakes

### Forgetting to invoke the prompt

```python
# BAD - passing template object, not messages
response = model.invoke(prompt)

# GOOD - invoke the prompt first
messages = prompt.invoke({"question": "Hello"})
response = model.invoke(messages)

# BETTER - use a chain (covered next section)
chain = prompt | model
response = chain.invoke({"question": "Hello"})
```

### Not including format instructions

When using output parsers, the model needs to know the expected format:

```python
# BAD - model doesn't know what format you want
prompt = ChatPromptTemplate.from_template("Extract: {text}")

# GOOD - include format instructions
prompt = ChatPromptTemplate.from_template(
    "Extract the following:\n{format_instructions}\n\nText: {text}"
)
formatted = prompt.partial(format_instructions=parser.get_format_instructions())
```

### Using high temperature for structured output

```python
# BAD - high temperature increases parsing failures
model = ChatOpenAI(model="gpt-4o-mini", temperature=1.5)

# GOOD - low temperature for structured output
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

## What You Should Have After This Step

By now, you should understand:

- How to create prompt templates with placeholders
- Different ways to invoke models (sync, stream, batch, async)
- How to parse LLM output into structured data
- When to use output parsers vs. structured output
- Few-shot prompting patterns

Next, you will learn how to chain these components together using LangChain Expression Language (LCEL).
