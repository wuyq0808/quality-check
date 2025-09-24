#!/usr/bin/env python3
"""
Quality Evaluator Agent - No Tools
Uses prompt-based evaluation by invoking the browser evaluation method
"""

import json
from datetime import datetime, timezone

from strands import Agent
from strands.models import BedrockModel
from strands_browser_direct import evaluate_website_feature


def process_and_save_result(website_url, result):
    """Process and save a single recording result"""
    import os

    # Create output directory if it doesn't exist
    output_dir = "quality_evaluation_parallel_output"
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
Evaluate the features of multiple websites based on provided evaluation recordings.

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
| Cases   | Skyscanner | (Website 2) | (and so on) |
|-----------|-----------------------------|-------------------------------|-------------|
| Case 1 | 6/7 – Rationale              | 5/7 – Rationale                | (and so on) |
| Case 2 | 6/7 – Rationale             | 5/7 – Rationale                | (and so on) |
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


if __name__ == "__main__":
    import concurrent.futures
    from strands_browser_direct import evaluate_website_feature

def get_test_scenarios(scenario_name):
    """Get test scenario by name"""
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    scenarios = {
        "hotel_search_quality": {
            "websites": [
                {
                    "url": "https://www.agoda.com",
                    "instructions": ""
                },
                {
                    "url": "https://www.google.com/travel/hotels",
                    "instructions": ""
                },
                {
                    "url": "https://www.booking.com",
                    "instructions": "Close overlay modal about Sign In."
                },
                {
                    "url": "https://www.skyscanner.com/hotels",
                    "instructions": ""
                }
            ],
            "base_request": f"""
Current time: {current_time}

Steps:
1. Find the destination input,
2. Input destination: Barcelona.
3. Select check-in: now+7d; check-out: now+8d.
4. Wait for the search result.
Intent Alignment Check: Verify that the top listings align with user intent (e.g. centrally located, well-reviewed, reasonably priced options appear first).

Cases:
1. Review Score Relevance Check: Confirm that top listings include hotels with strong guest scores unless filters or sorting override it.
2. Star Rating vs Price Balance Check: Ensure that the first few listings represent a healthy mix of quality (e.g. 3–5 star) and value, rather than skewing too heavily toward one end.
3. Repeat Search Consistency Check: Repeat the same search multiple times and check if the top listings remain consistent unless filters, sort, or availability changes.
4. Local Context Appropriateness Check: For destination-specific searches (e.g. Tokyo city center), verify that top listings are contextually appropriate (e.g. located in Shinjuku rather than suburban outskirts).
            """
        },



        "autocomplete_feature": {
            "websites": [
                # {
                #     "url": "https://www.agoda.com",
                #     "instructions": ""
                # },
                # {
                #     "url": "https://www.google.com/travel/hotels",
                #     "instructions": ""
                # },
                {
                    "url": "https://www.booking.com",
                    "instructions": "Close overlay modal about Sign In."
                },
                {
                    "url": "https://www.skyscanner.com/hotels",
                    "instructions": ""
                }
            ],
            "base_request": f"""
Current time: {current_time}

Test and record interactions with the auto-complete feature for hotel destinations:

Steps:
1. Find the search box for hotel destinations
2. Record all interactions with the auto complete feature

Cases: (MUST try more then enough variations to be thorough)
1. Type in City name, does the main city destination show as the first results?
2. Type in City name check if relevant POI's show up
3. Type in City name check if POI's are all in the same language
4. Type in City name with typo, check if it can handle typo and show the correct city name
            """
        }
    }

    return scenarios[scenario_name]

if __name__ == "__main__":
    import concurrent.futures
    from strands_browser_direct import evaluate_website_feature

    # Choose which scenario to run
    scenario = get_test_scenarios("autocomplete_feature")
    # scenario = get_test_scenarios("hotel_search_quality")

    base_request = scenario["base_request"]
    websites = scenario["websites"]
    print("🎯 Starting evaluation")
    print("=" * 60)

    # Execute evaluations sequentially - call evaluate_website_feature with complete prompt
    results = {}

    for config in websites:
        website_url = config['url']
        print(f"🔄 Starting evaluation for {website_url}")

        try:
            # Create complete prompt combining website URL, base request, and specific instructions
            website_instructions = config['instructions']
            instructions_section = f"\nWebsite-specific instructions:\n{website_instructions}\n" if website_instructions else ""

            complete_prompt = f"""Navigate to {website_url} and evaluate the following:

{base_request}{instructions_section}
Please test thoroughly and document all your observations."""

            result = evaluate_website_feature(complete_prompt)
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

    print("\n" + "=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)

    # Generate comparison using QualityEvaluator agent
    print("\n🤖 Generating comparison analysis...")
    evaluator = create_quality_evaluator()

    # Build comparison prompt for all websites
    website_results = []
    for i, config in enumerate(websites, 1):
        website_url = config['url']
        website_results.append(f"Website {i}: {website_url}")
        website_results.append(f"Results {i}: {results[website_url]}")
        website_results.append("")

    comparison_prompt = f"""
    Based on these detailed recording sessions that were produced by executing the following test request, evaluate and compare the auto-complete feature for hotel destinations:

Base Test Request:
{base_request}

Website-specific instructions were also provided for each site.

Recording Results from executing the above test:
{"\n".join(website_results)}
    """

    comparison_result = evaluator(comparison_prompt)

    # Save comparison to file
    import os
    output_dir = "quality_evaluation_parallel_output"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_filename = f"comparison_analysis_{timestamp}.md"
    comparison_filepath = os.path.join(output_dir, comparison_filename)

    with open(comparison_filepath, "w") as f:
        f.write(str(comparison_result))

    print(f"📄 Comparison analysis saved to: {comparison_filepath}")
    print(f"\n🔍 Comparison Analysis:\n{comparison_result}")

    print("\n🎉 Parallel quality evaluation completed!")