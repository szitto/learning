# RAG Fundamentals

Retrieval Augmented Generation (RAG) combines LLMs with external knowledge. Instead of relying solely on the model's training data, you retrieve relevant documents and include them in the prompt.

## Why RAG?

LLMs have limitations:

- **Knowledge cutoff**: Training data has a date limit
- **No access to private data**: They do not know your company's docs
- **Hallucination**: They may invent facts confidently
- **Token limits**: Cannot process entire databases

RAG solves these by retrieving relevant context at query time.

## RAG Pipeline Overview

```text
User Query → Embed Query → Search Vector Store → Retrieve Documents
                                                        ↓
                                            Combine with Prompt
                                                        ↓
                                                   LLM Call
                                                        ↓
                                                    Response
```

## Install RAG Dependencies

```bash
uv add langchain-chroma langchain-openai tiktoken
```

This gives you:

- `langchain-chroma` - ChromaDB vector store (local, good for development)
- `tiktoken` - Token counting for text splitting

For production, consider:

```bash
uv add pinecone-client  # Managed vector database
```

## Step 1: Load Documents

LangChain provides document loaders for many formats:

```python
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    WebBaseLoader,
    DirectoryLoader,
)

# Load a text file
loader = TextLoader("docs/guide.txt")
documents = loader.load()

# Load a PDF
loader = PyPDFLoader("docs/manual.pdf")
documents = loader.load()

# Load from web
loader = WebBaseLoader("https://example.com/docs")
documents = loader.load()

# Load all files from a directory
loader = DirectoryLoader("docs/", glob="**/*.md")
documents = loader.load()
```

Each document has:

```python
doc = documents[0]
print(doc.page_content)  # The text content
print(doc.metadata)      # {"source": "docs/guide.txt", ...}
```

## Step 2: Split Documents

Documents need to be split into chunks that fit the model's context window:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Characters per chunk
    chunk_overlap=200,    # Overlap between chunks
    length_function=len,
)

chunks = splitter.split_documents(documents)
print(f"Split {len(documents)} documents into {len(chunks)} chunks")
```

Understanding the parameters:

- **`chunk_size`**: Maximum characters per chunk. Smaller = more precise retrieval, larger = more context.
- **`chunk_overlap`**: Overlap prevents cutting off important context at boundaries.
- **`RecursiveCharacterTextSplitter`**: Tries to split on natural boundaries (paragraphs, sentences) before falling back to characters.

### Choosing chunk size

| Chunk Size | Trade-off |
|------------|-----------|
| 200-500 | More precise, may lose context |
| 500-1000 | Good balance for most use cases |
| 1000-2000 | More context, less precise matching |

## Step 3: Create Embeddings

Embeddings convert text to vectors for similarity search:

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Embed a single query
query_vector = embeddings.embed_query("How do I deploy?")

# Embed multiple documents
doc_vectors = embeddings.embed_documents([
    "First document text",
    "Second document text",
])
```

Common embedding models:

| Model | Dimensions | Use Case |
|-------|------------|----------|
| `text-embedding-3-small` | 1536 | Fast, cheap, good for most cases |
| `text-embedding-3-large` | 3072 | Higher quality, more expensive |

## Step 4: Store in Vector Database

ChromaDB for local development:

```python
from langchain_chroma import Chroma

# Create vector store from documents
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",  # Save to disk
)

# Or load existing
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)
```

## Step 5: Retrieve Documents

Create a retriever from the vector store:

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4},  # Return top 4 matches
)

# Use the retriever
docs = retriever.invoke("How do I deploy to production?")

for doc in docs:
    print(doc.page_content[:200])
    print("---")
```

### Search types

```python
# Similarity search (default)
retriever = vectorstore.as_retriever(search_type="similarity")

# MMR - balances relevance and diversity
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 10},
)

# Similarity with score threshold
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8},
)
```

## Step 6: Build the RAG Chain

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

# Format retrieved docs into a string
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# The prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """Answer questions based on the provided context.
If you cannot find the answer in the context, say "I don't have information about that."

Context:
{context}"""),
    ("human", "{question}"),
])

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# The RAG chain
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | model
    | StrOutputParser()
)

# Use it
response = rag_chain.invoke("How do I deploy to production?")
print(response)
```

## Complete RAG Example

Putting it all together:

```python
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# 1. Load documents
loader = DirectoryLoader("docs/", glob="**/*.md", loader_cls=TextLoader)
documents = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# 3. Create embeddings and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./db")

# 4. Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# 5. Build chain
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer based on context:\n{context}"),
    ("human", "{question}"),
])

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# 6. Query
response = rag_chain.invoke("What is the deployment process?")
print(response)
```

## Adding Sources to Responses

Include document sources in the response:

```python
from langchain_core.runnables import RunnableParallel

def format_docs_with_sources(docs):
    formatted = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source", "Unknown")
        formatted.append(f"[{i+1}] {doc.page_content}\nSource: {source}")
    return "\n\n".join(formatted)

# Return both answer and sources
rag_chain_with_sources = RunnableParallel(
    answer=rag_chain,
    sources=retriever | (lambda docs: [d.metadata.get("source") for d in docs]),
)

result = rag_chain_with_sources.invoke("How do I deploy?")
print(result["answer"])
print("Sources:", result["sources"])
```

## Hybrid Search

Combine semantic search with keyword search:

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# Keyword search
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 4

# Semantic search
semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Combine with weights
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, semantic_retriever],
    weights=[0.4, 0.6],  # 40% keyword, 60% semantic
)
```

## Contextual Compression

Filter retrieved documents to only relevant parts:

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(model)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever,
)

# Returns only the relevant portions of each document
docs = compression_retriever.invoke("What are the deployment steps?")
```

## Common Mistakes

### Not persisting the vector store

```python
# BAD - rebuilds embeddings every time
vectorstore = Chroma.from_documents(chunks, embeddings)

# GOOD - persist to disk
vectorstore = Chroma.from_documents(
    chunks, embeddings,
    persist_directory="./chroma_db"
)
```

### Chunks too large or too small

```python
# BAD - too small, loses context
splitter = RecursiveCharacterTextSplitter(chunk_size=100)

# BAD - too large, imprecise retrieval
splitter = RecursiveCharacterTextSplitter(chunk_size=5000)

# GOOD - reasonable size with overlap
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
```

### Not handling empty retrieval

```python
def format_docs(docs):
    if not docs:
        return "No relevant documents found."
    return "\n\n".join(doc.page_content for doc in docs)
```

### Ignoring metadata

```python
# Include source information in chunks
for chunk in chunks:
    chunk.metadata["source"] = chunk.metadata.get("source", "unknown")
    chunk.metadata["chunk_index"] = chunks.index(chunk)
```

## What You Should Have After This Step

By now, you should understand:

- The RAG pipeline: load → split → embed → store → retrieve → generate
- How to use document loaders and text splitters
- How to create and query vector stores
- How to build a complete RAG chain
- Advanced patterns: sources, hybrid search, compression

Next, you will learn about agents and tools for autonomous LLM applications.
