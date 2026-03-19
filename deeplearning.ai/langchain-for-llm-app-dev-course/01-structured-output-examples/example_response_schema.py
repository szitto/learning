"""
Improved ResponseSchema Example (Legacy Approach)
Shows how to eliminate repetition from the course example.
Note: Pydantic approach (example_pydantic.py) is preferred for new code.
"""

import os
from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchemaOutputParser
from langchain.output_parsers.structured import ResponseSchema
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sample_data import customer_review_1, customer_review_2

# Load environment variables
load_dotenv()

# Define schemas - single source of truth
gift_schema = ResponseSchema(
    name="gift",
    description="Was the item purchased as a gift for someone else? Answer True if yes, False if not or unknown."
)

delivery_days_schema = ResponseSchema(
    name="delivery_days",
    description="How many days did it take for the product to arrive? If this information is not found, output -1."
)

price_value_schema = ResponseSchema(
    name="price_value",
    description="Extract any sentences about the value or price, and output them as a comma separated Python list."
)

response_schemas = [gift_schema, delivery_days_schema, price_value_schema]


def extract_review_info(review_text: str) -> dict:
    """Extract structured information from a review using ResponseSchema."""

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Create output parser
    output_parser = ResponseSchemaOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    # IMPROVED: Minimal prompt - let format_instructions do all the work!
    # No need to repeat field descriptions here!
    review_template = """\
Extract information from the following product review:

{text}

{format_instructions}
"""

    prompt = ChatPromptTemplate.from_template(template=review_template)

    # Create chain
    chain = prompt | llm | output_parser

    # Execute
    result = chain.invoke({
        "text": review_text,
        "format_instructions": format_instructions
    })

    return result


def main():
    """Run extraction on sample reviews."""

    print("IMPROVED ResponseSchema Approach (No Repetition!)")
    print("=" * 60)

    reviews = [
        ("Review 1", customer_review_1),
        ("Review 2", customer_review_2),
    ]

    for name, review in reviews:
        print(f"\n{name}")
        print("-" * 60)
        print(f"Original: {review[:80]}...")
        print()

        result = extract_review_info(review)

        print(f"Gift: {result['gift']}")
        print(f"Delivery days: {result['delivery_days']}")
        print(f"Price mentions: {result['price_value']}")
        print()


if __name__ == "__main__":
    main()
