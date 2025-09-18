#!/usr/bin/env python3
"""
Direct Strands Agent with AgentCore Browser Tools
LLM gets direct access to browser tools - no custom navigation code
"""

import json
from datetime import datetime

from strands import Agent
from strands.models import BedrockModel
from strands_tools.browser import AgentCoreBrowser

def evaluate_website_feature(website_urls, feature_description):
    try:
        custom_browser_id = "recordingBrowserWithS3_20250916170045-Ec92oniUSi"
        browser_tool = AgentCoreBrowser(
            region='us-east-1',
            identifier=custom_browser_id,
            session_timeout=1800
        )
        
        bedrock_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="eu-west-1"
        )

        agent = Agent(
            name="WebNavigator",
            model=bedrock_model,
            tools=[browser_tool.browser],
            system_prompt="""
You have direct access to browser tools. Use them to complete web navigation tasks.
You must visit the sites IN SEPERATE BROWSER TABS/WINDOWS. Rate and compare the sites on the requested case.

Be detailed and consistent in the response.
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

OUTPUT in MARKDOWN with the following structure:
| Test Cases   | [Website 1] | [Website 2] |
|-----------|-----------------------------|-----------------------------|
| Test Case | 6/7 - Rationale              | 6/7 - Rationale |
### Summary - Focus on the test case
[Website 1]
- standout strengths  
- drawbacks  
[Website 2]
- standout strengths  
- drawbacks  
"""
        )

        result = agent(f"""
Open {website_urls} IN SEPERATE BROWSER TABS/WINDOWS evaluate the following feature:
{feature_description}
Please test thoroughly and provide detailed feedback using the rating system.
        """)

        return str(result)
        
    except Exception as e:
        error_msg = f"Strands browser tool implementation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {'status': 'error', 'error': error_msg}

if __name__ == "__main__":
    # Example usage
    website_urls = [
        "https://www.skyscanner.com/hotels",
        "https://www.booking.com"
    ]
    feature_description = """
    Test the auto-complete feature for hotel destinations:
- For booking.com, will be a overlay modal about Sign In. Must find it and Click the X button on the top right to close it.
- Find the search box for hotel destinations

Test case: (You must try more then enough variations to be sure)
Type in City name with typo, check if it can handle typo and show the correct city name
    """

    result = evaluate_website_feature(str(website_urls), feature_description)

    # Write result to markdown file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"website_evaluation_{timestamp}.md"

    with open(filename, 'w') as f:
        f.write(str(result))

    if result and "error" not in str(result).lower():
        print(f"\n🎉 SUCCESS: Sites completed! Output saved to {filename}")
    else:
        print(f"❌ Error occurred")