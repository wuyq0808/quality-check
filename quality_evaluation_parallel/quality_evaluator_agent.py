#!/usr/bin/env python3
"""
Quality Evaluator Agent - No Tools
Uses prompt-based evaluation by invoking the browser evaluation method
"""

import json
from datetime import datetime

from strands import Agent
from strands.models import BedrockModel
from strands_browser_direct import evaluate_website_feature


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
        region_name="eu-west-1"
    )

    # Create Strands agent without any tools
    agent = Agent(
        name="QualityEvaluator",
        model=bedrock_model,
        tools=[],  # No tools - pure prompt-based agent
        system_prompt="""
You are a quality evaluation specialist that helps generate comprehensive website feature evaluation tasks.
## Output Template
| Test   | Skyscanner | Booking.com |
|-----------|-----------------------------|-------------------------------|
| Test 1 | 6/7 – Rationale              | 5/7 – Rationale                |
| Test 2 | 6/7 – Rationale             | 5/7 – Rationale                |
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

    # User request for evaluation
    user_request = """
    Test the auto-complete feature for hotel destinations:
- Close any pop-ups/modals/overlays if they appear
- Find the search box for hotel destinations
- Tests:

1. Type in City name, does the main city destination show as the first results?
2. Type in City name check if relevant POI's show up;
3. Type in City name check if POI's are all in the same language
4. Type in City name with typo, check if it can handle typo and show the correct city name
    """

    # Test two different websites in parallel
    websites = [
        "https://www.skyscanner.com/hotels",
        "https://www.booking.com"
    ]

    print("🎯 Starting parallel evaluation of hotel auto-complete features...")
    print("=" * 60)

    # Execute evaluations in parallel - call evaluate_website_feature directly with user_request
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        future_to_website = {
            executor.submit(evaluate_website_feature, website, user_request): website
            for website in websites
        }

        results = {}

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_website):
            website = future_to_website[future]
            try:
                result = future.result()
                results[website] = result
                print(f"✅ Completed evaluation for {website}")
            except Exception as exc:
                print(f"❌ {website} generated an exception: {exc}")
                results[website] = f"Error: {exc}"

    print("\n" + "=" * 60)
    print("📊 PARALLEL EVALUATION RESULTS")
    print("=" * 60)

    for website, result in results.items():
        print(f"\n🌐 Website: {website}")
        print("-" * 40)
        if isinstance(result, str) and "Error:" not in result:
            print(result)
        else:
            print(f"❌ {result}")

        # Write to individual MD file
        website_name = website.replace("https://www.", "").replace("https://", "").replace("/", "_")
        filename = f"{website_name}_evaluation.md"

        with open(filename, "w") as f:
            f.write(f"# Website Evaluation Report\n\n")
            f.write(f"**Website:** {website}\n\n")
            f.write(f"**Evaluation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Feature Tested:** Hotel Auto-complete\n\n")
            f.write("## Test Description\n\n")
            f.write("```\n")
            f.write(user_request.strip())
            f.write("\n```\n\n")
            f.write("## Evaluation Results\n\n")

            if isinstance(result, str) and "Error:" not in result:
                f.write(result)
            else:
                f.write(f"**Error occurred during evaluation:**\n\n")
                f.write(f"```\n{result}\n```\n")

        print(f"📄 Results saved to: {filename}")

    # Generate comparison using QualityEvaluator agent
    print("\n🤖 Generating comparison analysis...")
    evaluator = create_quality_evaluator()

    comparison_prompt = f"""
    Compare the hotel auto-complete feature evaluation results from these two websites:

    Website 1: {websites[0]}
    Results 1: {results[websites[0]]}

    Website 2: {websites[1]}
    Results 2: {results[websites[1]]}

    """

    comparison_result = evaluator(comparison_prompt)

    # Save comparison to file
    with open("comparison_analysis.md", "w") as f:
        f.write(f"# Website Comparison Analysis\n\n")
        f.write(f"**Comparison Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Websites Compared:**\n")
        f.write(f"- {websites[0]}\n")
        f.write(f"- {websites[1]}\n\n")
        f.write(f"**Feature Analyzed:** Hotel Auto-complete\n\n")
        f.write("## Comparison Results\n\n")
        f.write(str(comparison_result))

    print("📄 Comparison analysis saved to: comparison_analysis.md")
    print(f"\n🔍 Comparison Analysis:\n{comparison_result}")

    print("\n🎉 Parallel quality evaluation completed!")