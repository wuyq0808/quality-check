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
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception
from strands_browser_direct import evaluate_website_feature
from constants import WebsiteKey, NEXT_DAY_ONE_NIGHT, CITIES, GOOGLE_TRAVEL, AGODA, BOOKING_COM, SKYSCANNER_HOTELS, WEBSITES


class Feature(Enum):
    RELEVANCE_OF_TOP_LISTINGS = "relevance_of_top_listings"
    AUTOCOMPLETE_FOR_DESTINATIONS_HOTELS = "autocomplete_for_destinations_hotels"
    FIVE_PARTNERS_PER_HOTEL = "five_partners_per_hotel"
    HERO_POSITION_PARTNER_MIX = "hero_position_partner_mix"
    DISTANCE_ACCURACY = "distance_accuracy"

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def process_and_save_result(website_key, result, feature_key=None, city=None, checkin_checkout=None):
    """Process and save a single recording result"""
    import os

    print(f"\n🌐 Website: {website_key}")
    print("-" * 40)
    if isinstance(result, str) and "Error:" not in result:
        print(result)
    else:
        print(f"❌ {result}")

    # Convert to string values for filename
    website_key_str = website_key.value
    checkin_checkout_str = checkin_checkout["key"]
    city_str = city

    # Create nested directory structure: quality_evaluation_output/text_recording/[feature]/[city]/[checkin_checkout]/[website]/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("quality_evaluation_output", "text_recording", feature_key, city_str, checkin_checkout_str, website_key_str)
    filename = f"{timestamp}.md"

    os.makedirs(output_dir, exist_ok=True)
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
# Checking Steps
## General Steps Taken
- Destination: [e.g. Barcelona (May visit multiple cities, here for the main city)]
- Check-in: [e.g. 2024-09-20], Check-out: [e.g. 2024-09-21]
- [Other steps]

## Differences Steps Between Sites
- [e.g. Skyscanner has 2 separate inputs for check-in and check-out, Google Travel has a single date range picker]
- [e.g. Booking.com requires closing a pop-up]

Concise summary of steps taken, general steps and differences between sites.

# Feature: [Feature Name Being Tested]
| Checks   | Skyscanner | (Website 2) | (and so on) |
|-----------|-----------------------------|-------------------------------|-------------|
| Check 1 | 6/7 – Rationale              | 5/7 – Rationale                | (and so on) |
| Check 2 | 6/7 – Rationale             | 5/7 – Rationale                | (and so on) |
| Overall rating (last row) | 6/7 – Rationale             | 5/7 – Rationale                | (and so on) |

# Summary
- **Skyscanner**  
  - standout strengths  
  - drawbacks  
- **Booking.com**  
  - standout strengths  
  - drawbacks  
"""
    )

    return agent


def execute_website_evaluations(websites, feature_instruction, feature_key=None, city=None, checkin_checkout=None):
    """Execute evaluations for all websites sequentially"""
    results = {}

    for website in websites:
        website_url = website['url']
        print(f"🔄 Starting evaluation for {website_url}")

        try:
            feature_prompt = f"""Navigate to {website_url} and execute the following:
{feature_instruction}
"""

            # Use explicit Retrying object for deterministic retry behavior
            retrying = Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=4, max=10),
                retry=retry_if_exception(Exception)
            )

            result = retrying(evaluate_website_feature, feature_prompt, website_key=website.get('key'))
            results[website_url] = result
            print(f"✅ Completed evaluation for {website_url}")

            # Process and save result immediately
            process_and_save_result(website.get('key'), result, feature_key, city, checkin_checkout)

        except Exception as exc:
            print(f"❌ {website_url} generated an exception: {exc}")
            error_result = f"Error: {exc}"
            results[website_url] = error_result

            # Process and save error result immediately
            process_and_save_result(website.get('key'), error_result, feature_key, city, checkin_checkout)

    return results


def generate_feature_comparison(feature, feature_instruction, websites, results, city=None, checkin_checkout=None):
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

    # Save comparison to file with full hierarchy: feature/city/checkin_checkout
    import os
    city_str = city
    checkin_checkout_str = checkin_checkout["key"]
    output_dir = os.path.join("quality_evaluation_output", "comparison_analysis", feature.value, city_str, checkin_checkout_str)
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_filename = f"{timestamp}.md"
    comparison_filepath = os.path.join(output_dir, comparison_filename)

    with open(comparison_filepath, "w") as f:
        f.write(str(comparison_result))

    print(f"📄 Comparison analysis saved to: {comparison_filepath}")



def get_feature_websites(feature):
    """Get websites to test for a specific feature"""
    match feature:
        case Feature.FIVE_PARTNERS_PER_HOTEL:
            # Only use meta-search sites that show multiple partners
            return [
                SKYSCANNER_HOTELS,
                GOOGLE_TRAVEL,
            ]
        case Feature.HERO_POSITION_PARTNER_MIX:
            # Only use meta-search sites that show multiple partners
            return [
                SKYSCANNER_HOTELS,
                GOOGLE_TRAVEL,
            ]
        case _:
            return WEBSITES


def get_feature_prompt(feature, destination, checkin_date, checkout_date):
    """Get feature prompt by name with parameterized destination and dates"""
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
3. Select check-in: {checkin_date}; check-out: {checkout_date}.
4. Click search, wait for result.

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
3. Select check-in: {checkin_date}; check-out: {checkout_date}.
4. Click search, wait for result.
5. Get into first hotel details page to see partner offerings. We have partner offering displayed on the search result list, but the details page is more clearer and easier to navigate.

Checks:
1. Check first 5 hotels in hotel search results to see if >= 5 partner offering rates for each hotel. Count the number of booking partners/providers shown for each of the first 5 hotels in the search results.
            """

        case Feature.HERO_POSITION_PARTNER_MIX:
            return f"""
Steps:
1. Find the destination input,
2. Input destination: {destination}.
3. Select check-in: {checkin_date}; check-out: {checkout_date}.
4. Click search, wait for result.

Checks:
1. Top Position Partner Variation Check: Perform multiple hotel searches and verify that the top (hero) result features a varied mix of partners over time and across queries. Document which partner appears in the top position for each search.
2. Partner Distribution Diversity Check: Check if the first few hotel cards (top 5 results) represent a healthy mix of different booking partners rather than being dominated by a single one. Count and document partner distribution.
3. Fair Rotation Across Markets Check: Run hotel searches across multiple regions or cities and check if local and global partners are fairly represented in the hero position mix. (Try other cities then just {destination})
            """

        case Feature.DISTANCE_ACCURACY:
            return f"""
Steps:
1. Find the destination input,
2. Input destination: {destination}.
3. Select check-in: {checkin_date}; check-out: {checkout_date}.
4. Click search, wait for result.
5. Check first 5 hotels.

Checks:
1. Displayed Distance to Landmark Accuracy Check: Verify that the distance shown on each hotel card accurately reflects the straight-line or walking distance to the specified reference point (e.g. city center or user-selected landmark).
2. Landmark Reference Accuracy Check: Check that the hotel’s distance is being measured from the correct reference point (e.g. central landmark or city center, not airport or other default).
3. Unit of Measurement Check: Ensure that distances are displayed using the correct units (e.g. km or miles) based on user region or settings.
            """

        case _:
            raise ValueError(f"Unknown feature: {feature}")


if __name__ == "__main__":
    import concurrent.futures
    from datetime import datetime, timedelta
    from strands_browser_direct import evaluate_website_feature

    # Features to run
    features = [
        # Feature.AUTOCOMPLETE_FOR_DESTINATIONS_HOTELS,
        # Feature.RELEVANCE_OF_TOP_LISTINGS,
        Feature.FIVE_PARTNERS_PER_HOTEL,
        Feature.HERO_POSITION_PARTNER_MIX,
        Feature.DISTANCE_ACCURACY
    ]

    # Define checkin_checkout parameters
    checkin_checkout = NEXT_DAY_ONE_NIGHT

    # Calculate check-in and check-out dates from checkin_checkout constant
    today = datetime.now()
    checkin_days, checkout_days = checkin_checkout["value"]
    checkin_date = (today + timedelta(days=checkin_days)).strftime("%Y-%m-%d")
    checkout_date = (today + timedelta(days=checkout_days)).strftime("%Y-%m-%d")

    # Loop through all cities
    for city in CITIES:
        print(f"\n🏙️ Starting evaluation for city: {city}")

        # Loop through all features for each city
        for feature in features:
            print(f"\n🚀 Testing feature: {feature.value}")

            feature_instruction = get_feature_prompt(feature, city, checkin_date, checkout_date)
            feature_websites = get_feature_websites(feature)

            # Execute evaluations sequentially
            results = execute_website_evaluations(feature_websites, feature_instruction, feature.value, city, checkin_checkout)

            # Generate comparison analysis
            generate_feature_comparison(feature, feature_instruction, feature_websites, results, city, checkin_checkout)

            print(f"✅ Completed feature: {feature.value} for city: {city}")

        print(f"✅ Completed all features for city: {city}")