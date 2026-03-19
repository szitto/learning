# Structured Output Examples

This folder demonstrates modern approaches to extracting structured data from text using LangChain, without the repetition found in older examples.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the examples**:
   ```bash
   # Modern Pydantic approach (recommended)
   python example_pydantic.py

   # Legacy ResponseSchema approach (improved)
   python example_response_schema.py

   # Using Anthropic Claude
   python example_anthropic.py
   ```

## Examples Included

- **example_pydantic.py**: Modern approach using Pydantic models with `.with_structured_output()`
- **example_response_schema.py**: Improved version of the course example (no repetition)
- **example_anthropic.py**: Same structured output using Claude instead of GPT
- **sample_data.py**: Sample customer reviews used in examples

## Key Improvements Over Course Example

1. ✅ No repetition of field descriptions
2. ✅ Type safety with Pydantic
3. ✅ Cleaner, more maintainable code
4. ✅ Works with multiple LLM providers

## Learn More

- [LangChain Structured Output Docs](https://python.langchain.com/docs/how_to/structured_output/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
