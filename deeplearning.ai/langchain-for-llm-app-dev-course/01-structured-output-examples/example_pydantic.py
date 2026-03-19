"""
Modern Structured Output Example using Pydantic Models
This is the RECOMMENDED approach - clean, type-safe, no repetition!
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from sample_data import customer_review_1, customer_review_2, customer_review_3

# Load environment variables
load_dotenv()

# Define the structure we want to extract (single source of truth!)
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


def extract_review_info(review_text: str) -> ReviewExtraction:
    """Extract structured information from a review."""

    # Initialize LLM with structured output
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(ReviewExtraction)

    # Simple prompt - no need to repeat field descriptions!
    prompt = ChatPromptTemplate.from_template(
        "Extract the relevant information from this product review:\n\n{text}"
    )

    # Create chain
    chain = prompt | structured_llm

    # Execute
    result = chain.invoke({"text": review_text})
    return result


def main():
    """Run extraction on sample reviews."""

    reviews = [
        ("Review 1", customer_review_1),
        ("Review 2", customer_review_2),
        ("Review 3", customer_review_3),
    ]

    for name, review in reviews:
        print(f"\n{'='*60}")
        print(f"{name}")
        print(f"{'='*60}")
        print(f"Original text: {review[:100]}...")
        print()

        result = extract_review_info(review)

        print(f"📦 Gift: {result.gift}")
        print(f"🚚 Delivery days: {result.delivery_days}")
        print(f"💰 Price mentions: {result.price_value}")


if __name__ == "__main__":
    main()
