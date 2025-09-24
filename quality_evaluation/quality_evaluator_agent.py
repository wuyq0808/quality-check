#!/usr/bin/env python3
"""
Quality Evaluator Agent - No Tools
Uses prompt-based evaluation by invoking the browser evaluation method
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum

from strands import Agent
from strands.models import BedrockModel
from strands_browser_direct import evaluate_website_feature


class Feature(Enum):
    RELEVANCE_OF_TOP_LISTINGS = "relevance_of_top_listings"
    AUTOCOMPLETE_FOR_DESTINATIONS_HOTELS = "autocomplete_for_destinations_hotels"
    FIVE_PARTNERS_PER_HOTEL = "five_partners_per_hotel"

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def process_and_save_result(website_url, result):
    """Process and save a single recording result"""
    import os

    # Create output directory if it doesn't exist
    output_dir = "quality_evaluation_output"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n🌐 Website: {website_url}")
    print("-" * 40)
    if isinstance(result, str) and "Error:" not in result:
        print(result)
    else:
        print(f"❌ {result}")

    # Save recording result to timestamped file
    website_name = website_url.replace("https://www.", "").replace("https://", "").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{website_name}_recording_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(str(result))

    print(f"📄 Results saved to: {filepath}")


def create_quality_evaluator():
    """
    Create a Strands agent without tools that can generate evaluation prompts
    and invoke the browser evaluation method

    Returns:
        Agent: Configured Strands agent for quality evaluation
    """
    # Create explicit Bedrock model with EU region
    bedrock_model = BedrockModel(
        model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="eu-west-1",
        temperature=0.1
    )

    # Create Strands agent without any tools
    agent = Agent(
        name="QualityEvaluator",
        model=bedrock_model,
        tools=[],  # No tools - pure prompt-based agent
        system_prompt="""
You are a senior web product manager.
Analyze the recorded observations of navigating the sites, Evaluate the features of multiple websites.
Be subjective and critical in your evaluations - we need honest truth, not praise.
Point out usability issues, confusing interfaces, slow performance, and any problems you encounter.

Rating Definition
1 - Terrible
Non-functional, misleading
2 - Very Bad
Barely usable or broken elements
3 - Bad
Significant usability/content gaps
4 - Neutral
Works, but forgettable
5 - Good
Solid experience, few flaws
6 - Very Good
Polished and competitive
7 - Excellent
Best-in-class; highly competitive

## Output Template
# Feature: [Feature Name Being Tested]
| Checks   | Skyscanner | (Website 2) | (and so on) |
|-----------|-----------------------------|-------------------------------|-------------|
| Check 1 | 6/7 – Rationale              | 5/7 – Rationale                | (and so on) |
| Check 2 | 6/7 – Rationale             | 5/7 – Rationale                | (and so on) |
### Summary
- **Skyscanner**  
  - standout strengths  
  - drawbacks  
- **Booking.com**  
  - standout strengths  
  - drawbacks  
"""
    )

    return agent


def execute_website_evaluations(websites, feature_instruction):
    """Execute evaluations for all websites sequentially"""
    results = {}

    for website in websites:
        website_url = website['url']
        print(f"🔄 Starting evaluation for {website_url}")

        try:
            feature_prompt = f"""Navigate to {website_url} and execute the following:
{feature_instruction}
"""

            result = evaluate_website_feature(feature_prompt, website_key=website.get('key'))
            results[website_url] = result
            print(f"✅ Completed evaluation for {website_url}")

            # Process and save result immediately
            process_and_save_result(website_url, result)

        except Exception as exc:
            print(f"❌ {website_url} generated an exception: {exc}")
            error_result = f"Error: {exc}"
            results[website_url] = error_result

            # Process and save error result immediately
            process_and_save_result(website_url, error_result)

    return results


def generate_feature_comparison(feature, feature_instruction, websites, results):
    """Generate comparison analysis using QualityEvaluator agent"""
    print("\n🤖 Generating comparison analysis...")
    evaluator = create_quality_evaluator()

    # Build comparison prompt for all websites
    website_results = []
    for i, website in enumerate(websites, 1):
        website_url = website['url']
        website_results.append(f"Website {i}: {website_url}")
        website_results.append(f"Results {i}: {results[website_url]}")
        website_results.append("")

    comparison_prompt = f"""
    Based on these detailed recording sessions that were produced by executing the following test request, evaluate and compare:

Feature: {feature.value.replace("_", " ").title()}

Feature checks:
{feature_instruction}

Recording Results from executing the above checks:
{"\n".join(website_results)}
    """

    comparison_result = evaluator(comparison_prompt)

    # Save comparison to file
    import os
    output_dir = "quality_evaluation_output"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_filename = f"comparison_analysis_{timestamp}.md"
    comparison_filepath = os.path.join(output_dir, comparison_filename)

    with open(comparison_filepath, "w") as f:
        f.write(str(comparison_result))

    print(f"📄 Comparison analysis saved to: {comparison_filepath}")


# Common website list for all features
WEBSITES = [
    {
        "url": "https://www.agoda.com",
        "key": "agoda_com"
    },
    {
        "url": "https://www.google.com/travel/hotels",
        "key": "google_travel_hotels"
    },
    {
        "url": "https://www.booking.com",
        "key": "booking_com"
    },
    {
        "url": "https://www.skyscanner.com/hotels",
        "key": "skyscanner_hotels"
    }
]

def get_feature_prompt(feature, destination):
    """Get feature prompt by name with parameterized destination"""
    match feature:
        case Feature.AUTOCOMPLETE_FOR_DESTINATIONS_HOTELS:
            return f"""
Test and record interactions with the auto-complete feature for hotel destinations:

Destination: {destination}

Steps:
1. Find the search box for hotel destinations and do the following:

Checks:
1. Type in City name, does the main city destination show as the first results?
2. Type in City name check if relevant POI's show up
3. Type in City name check if POI's are all in the same language
4. Type in City name with typo, check if it can handle typo and show the correct city name (MUST try more then enough variations to be thorough)
            """

        case Feature.RELEVANCE_OF_TOP_LISTINGS:
            return f"""
Steps:
1. Find the destination input,
2. Input destination: {destination}.
3. Select check-in: today; check-out: tomorrow.
4. Select 2 adults, 1 room
5. Click search, wait for result.

Checks:
1. Intent Alignment Check: Verify that the top listings align with user intent (e.g. centrally located, well-reviewed, reasonably priced options appear first).
2. Review Score Relevance Check: Confirm that top listings include hotels with strong guest scores unless filters or sorting override it.
3. Star Rating vs Price Balance Check: Ensure that the first few listings represent a healthy mix of quality (e.g. 3–5 star) and value, rather than skewing too heavily toward one end.
4. Repeat Search Consistency Check: Repeat the same search multiple times and check if the top listings remain consistent unless availability changes. (REFRESH THE PAGE AND SEARCH AGAIN TO MAKE SURE IT IS RENEWED)
5. Local Context Appropriateness Check: For destination-specific searches (e.g. Tokyo city center), verify that top listings are contextually appropriate (e.g. located in Shinjuku rather than suburban outskirts).
            """
        
        case Feature.FIVE_PARTNERS_PER_HOTEL:
            return f"""
Steps:
1. Find the destination input,
2. Input destination: {destination}.
3. Select check-in: today; check-out: tomorrow.
4. Select 2 adults, 1 room
5. Click search, wait for result.

Checks:
1. Check 10 hotels in hotel search results to see if >= 5 partners offering rates for each hotel. Count the number of booking partners/providers shown for each of the first 10 hotels in the search results.
            """    
        case _:
            raise ValueError(f"Unknown feature: {feature}")


if __name__ == "__main__":
    import concurrent.futures
    from strands_browser_direct import evaluate_website_feature

    # Choose which feature to run
    feature = Feature.RELEVANCE_OF_TOP_LISTINGS
    # feature = Feature.AUTOCOMPLETE_FOR_DESTINATIONS_HOTELS
    feature_instruction = get_feature_prompt(feature, "Barcelona")

    # Execute evaluations sequentially
    results = execute_website_evaluations(WEBSITES, feature_instruction)

    # Generate comparison analysis
    generate_feature_comparison(feature, feature_instruction, WEBSITES, results)