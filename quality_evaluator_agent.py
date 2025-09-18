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
"""
    )

    return agent


def evaluate_website_quality(website_url, user_request):
    """
    Evaluate website quality by generating evaluation prompts and invoking browser testing

    Args:
        website_url (str): The website URL to evaluate
        user_request (str): User's description of what to evaluate

    Returns:
        dict: Combined evaluation results
    """
    try:
        # Create the quality evaluator agent
        evaluator = create_quality_evaluator()

        # Generate detailed evaluation prompt
        prompt_generation_task = f"""
        Generate a comprehensive feature evaluation description for testing this website: {website_url}

        User request: {user_request}

        Create detailed test steps that include:
        1. Navigation steps
        2. Specific interactions to test
        3. Expected behaviors to verify
        4. Edge cases to check
        5. Usability aspects to evaluate

        Format your response as a clear, step-by-step testing guide that can be executed by an automated browser agent.
        """

        print("🤖 Generating evaluation criteria...")
        evaluation_criteria = evaluator(prompt_generation_task)

        print("🌐 Executing browser-based evaluation...")
        # Invoke the browser evaluation method
        browser_results = evaluate_website_feature(website_url, str(evaluation_criteria))

        # Combine results
        results = {
            "website_url": website_url,
            "user_request": user_request,
            "evaluation_criteria": str(evaluation_criteria),
            "browser_evaluation": browser_results,
            "timestamp": datetime.now().isoformat()
        }

        return results

    except Exception as e:
        error_msg = f"Quality evaluation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "website_url": website_url,
            "user_request": user_request,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import concurrent.futures
    from strands_browser_direct import evaluate_website_feature

    # Use the same feature description from strands_browser_direct.py
    feature_description = """
    Test the auto-complete feature for hotel destinations:
1. Find and click the Hotels link/button to reach hotels page
2. Test the auto complete feature:

Auto-complete for destinations/hotels
Type in City name, does the main city destination show as the first results?
Type in City name check if relevant POI's show up; 
Type in City name check if POI's are all in the same language 
Type in City name with typo, check if it can handle typo and show the correct city name
    """

    # Test two different websites in parallel
    websites = [
        "https://www.skyscanner.com",
        "https://www.booking.com"
    ]

    print("🎯 Starting parallel evaluation of hotel auto-complete features...")
    print("=" * 60)

    # Execute evaluations in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        future_to_website = {
            executor.submit(evaluate_website_feature, website, feature_description): website
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
            f.write(feature_description.strip())
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

    Provide a comprehensive comparison analysis including:
    1. Which website performs better overall
    2. Specific strengths and weaknesses of each
    3. Recommendations for improvement
    4. Final comparative rating
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