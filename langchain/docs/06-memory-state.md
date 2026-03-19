# Memory and State

LLMs are stateless - they do not remember previous conversations. Memory systems add context from earlier turns to make conversations coherent.

## Why Memory Matters

Without memory:

```text
User: My name is Alice.
AI: Nice to meet you, Alice!

User: What is my name?
AI: I don't know your name. You haven't told me.
```

With memory:

```text
User: My name is Alice.
AI: Nice to meet you, Alice!

User: What is my name?
AI: Your name is Alice.
```

## Memory Approaches

LangChain supports several memory strategies:

| Type | How It Works | Best For |
|------|--------------|----------|
| Buffer | Keep all messages | Short conversations |
| Window | Keep last N messages | Longer conversations |
| Summary | Summarize old messages | Very long conversations |
| Entity | Track key entities | Entity-focused tasks |

## Basic Chat Memory

The simplest approach - track message history manually:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

model = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | model

# Maintain history manually
history = []

def chat(user_input: str) -> str:
    # Call the chain with current history
    response = chain.invoke({
        "history": history,
        "input": user_input,
    })

    # Update history
    history.append(HumanMessage(content=user_input))
    history.append(AIMessage(content=response.content))

    return response.content

# Conversation
print(chat("My name is Alice"))
print(chat("What is my name?"))  # Remembers "Alice"
```

## Using ChatMessageHistory

LangChain provides history management classes:

```python
from langchain_community.chat_message_histories import ChatMessageHistory

history = ChatMessageHistory()

history.add_user_message("My name is Alice")
history.add_ai_message("Nice to meet you, Alice!")

print(history.messages)
# [HumanMessage(content='My name is Alice'),
#  AIMessage(content='Nice to meet you, Alice!')]
```

### Persistent history

Store history in files or databases:

```python
from langchain_community.chat_message_histories import FileChatMessageHistory

# Stores in a JSON file
history = FileChatMessageHistory("chat_history.json")

history.add_user_message("Hello")
history.add_ai_message("Hi there!")

# History persists across restarts
```

For production, use Redis or a database:

```python
from langchain_community.chat_message_histories import RedisChatMessageHistory

history = RedisChatMessageHistory(
    session_id="user_123",
    url="redis://localhost:6379",
)
```

## RunnableWithMessageHistory

The recommended way to add memory to chains:

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Store for different sessions
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Base chain (no memory)
chain = prompt | model

# Wrap with memory
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Use with session ID
config = {"configurable": {"session_id": "user_123"}}

response = chain_with_history.invoke(
    {"input": "My name is Bob"},
    config=config,
)

response = chain_with_history.invoke(
    {"input": "What is my name?"},
    config=config,
)
# Returns "Bob"
```

## Window Memory

Keep only the last N messages to manage context length:

```python
from langchain_core.messages import trim_messages

def get_trimmed_history(session_id: str) -> ChatMessageHistory:
    history = get_session_history(session_id)

    # Keep only last 10 messages
    if len(history.messages) > 10:
        history.messages = history.messages[-10:]

    return history
```

Or use the built-in trimmer:

```python
from langchain_core.messages import trim_messages

trimmer = trim_messages(
    max_tokens=1000,
    strategy="last",  # Keep last messages
    token_counter=model,  # Use model to count tokens
    include_system=True,  # Always keep system message
)

# In your chain
chain = (
    {"history": trimmer, "input": RunnablePassthrough()}
    | prompt
    | model
)
```

## Summary Memory

Summarize old messages to compress history:

```python
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize this conversation in 2-3 sentences:"),
    MessagesPlaceholder(variable_name="messages"),
])

summary_chain = summary_prompt | model | StrOutputParser()

def summarize_if_needed(history: ChatMessageHistory) -> list:
    messages = history.messages

    if len(messages) > 20:
        # Summarize old messages
        old_messages = messages[:-10]
        recent_messages = messages[-10:]

        summary = summary_chain.invoke({"messages": old_messages})

        # Replace old messages with summary
        return [SystemMessage(content=f"Previous conversation summary: {summary}")] + recent_messages

    return messages
```

## Entity Memory

Track specific entities across the conversation:

```python
from langchain_community.memory import ConversationEntityMemory

memory = ConversationEntityMemory(llm=model)

# As conversation progresses, entities are extracted and stored
memory.save_context(
    {"input": "Alice is a software engineer at Google"},
    {"output": "I'll remember that about Alice."},
)

# Later, retrieve entity info
entities = memory.load_memory_variables({"input": "Tell me about Alice"})
print(entities)
# {'entities': {'Alice': 'Software engineer at Google'}}
```

## Memory in Agents

Add memory to agents:

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(model, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools)

# Wrap with history
agent_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

config = {"configurable": {"session_id": "user_456"}}

result = agent_with_history.invoke(
    {"input": "What's the weather in Tokyo?"},
    config=config,
)
```

## Multi-User Sessions

Handle multiple users with separate histories:

```python
from langchain_community.chat_message_histories import RedisChatMessageHistory

def get_user_history(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://localhost:6379",
        ttl=3600,  # Expire after 1 hour
    )

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_user_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Each user gets their own history
alice_config = {"configurable": {"session_id": "alice_session"}}
bob_config = {"configurable": {"session_id": "bob_session"}}

chain_with_history.invoke({"input": "I'm Alice"}, config=alice_config)
chain_with_history.invoke({"input": "I'm Bob"}, config=bob_config)
```

## Clearing History

```python
history = get_session_history("user_123")
history.clear()
```

## Common Mistakes

### Not managing context length

```python
# BAD - eventually exceeds context window
history.append(message)  # Forever growing

# GOOD - trim or summarize
if len(history.messages) > MAX_MESSAGES:
    history.messages = history.messages[-MAX_MESSAGES:]
```

### Forgetting session isolation

```python
# BAD - all users share history
history = ChatMessageHistory()

# GOOD - per-user history
def get_session_history(session_id: str):
    return store.get(session_id, ChatMessageHistory())
```

### Including too much history

```python
# BAD - sends entire history (slow, expensive)
chain.invoke({"history": all_messages})

# GOOD - send relevant recent history
chain.invoke({"history": messages[-10:]})
```

### Not persisting important conversations

For production, always persist history to a database. In-memory storage is lost on restart.

## What You Should Have After This Step

By now, you should understand:

- Why memory is needed for conversations
- Manual history management with `MessagesPlaceholder`
- Using `ChatMessageHistory` and persistent backends
- `RunnableWithMessageHistory` for automatic history management
- Window and summary strategies for long conversations
- Multi-user session handling

Next, you will learn about production concerns: streaming, caching, observability, and error handling.
