"""
Structured Output with Anthropic Claude
Shows the same Pydantic approach works with different LLM providers.
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from sample_data import customer_review_1

# Load environment variables
load_dotenv()


class ReviewExtraction(BaseModel):
    """Extract structured information from a product review."""

    gift: bool = Field(
        description="Was the item purchased as a gift for someone else?"
    )
    delivery_days: int = Field(
        description="How many days did it take for the product to arrive? Use -1 if not found.",
        default=-1
    )
    price_value: list[str] = Field(
        description="Extract any sentences about the value or price",
        default_factory=list
    )


def extract_review_info_claude(review_text: str) -> ReviewExtraction:
    """Extract structured information using Claude."""

    # Initialize Claude with structured output
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
    structured_llm = llm.with_structured_output(ReviewExtraction)

    # Same simple prompt as OpenAI example!
    prompt = ChatPromptTemplate.from_template(
        "Extract the relevant information from this product review:\n\n{text}"
    )

    # Create chain
    chain = prompt | structured_llm

    # Execute
    result = chain.invoke({"text": review_text})
    return result


def main():
    """Run extraction using Claude."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not found in .env file")
        print("Add it to run this example with Claude.")
        return

    print("Structured Output with Anthropic Claude")
    print("=" * 60)
    print(f"Review: {customer_review_1[:100]}...")
    print()

    result = extract_review_info_claude(customer_review_1)

    print(f"📦 Gift: {result.gift}")
    print(f"🚚 Delivery days: {result.delivery_days}")
    print(f"💰 Price mentions: {result.price_value}")
    print()
    print("✅ Same Pydantic model works with different LLM providers!")


if __name__ == "__main__":
    main()
