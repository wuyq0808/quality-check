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

def evaluate_website_feature(website_urls, user_prompt):
    try:
        browser_tool = AgentCoreBrowser(
            region='us-east-1',
            identifier="recordingBrowserWithS3_20250916170045-Ec92oniUSi",
            session_timeout=1800
        )
        
        bedrock_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="eu-west-1",
            temperature=0.1
        )

        agent = Agent(
            name="WebNavigator",
            model=bedrock_model,
            tools=[browser_tool.browser],
            system_prompt="""
You have direct access to browser tools. Use them to complete web navigation tasks.
You must visit the sites IN SEPERATE BROWSER TABS/WINDOWS. Rate and compare the sites on the requested case.
Always take screenshots for input.

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

Output in markdown with the following structure:
| Cases (Must not include cases not listed in user prompt)   | [Website 1] | [Website 2] |
|-----------|-----------------------------|-----------------------------|
| Case | 6/7 - Rationale              | 6/7 - Rationale |
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
{user_prompt}
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
    ]
    user_prompt = """
- Find the search box for hotel destinations, input London
- Click search
- You will see a small map view, that is NOT the map we need to test.
- MUST open the full map by clicking the expend button: <button type="button" class="MapHotelOverview_MapHotelOverview__expandButton__d7Qzn" aria-label="Expand map"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true" width="1.5rem" height="1.5rem" class="MapHotelOverview_MapHotelOverview__expandIcon__q-LtV"><path d="M7.667 14.921a1 1 0 0 1 1.439 1.39l-.025.024-2.667 2.667h1.585a1 1 0 0 1 .993.884l.006.116a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-4a1 1 0 1 1 2 0v1.587zm8.334 6.081a1 1 0 0 1 0-2h1.583l-2.665-2.667a1 1 0 0 1-.082-1.32l.083-.094a1 1 0 0 1 1.414 0L19 17.591v-1.589a1 1 0 0 1 .883-.993l.116-.007a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1zM8 2.998a1 1 0 0 1 0 2H6.416l2.665 2.668a1 1 0 0 1 .082 1.32l-.083.094a1 1 0 0 1-1.414 0L5 6.41v1.588a1 1 0 0 1-.883.993L4 8.998a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1zm12 0a1 1 0 0 1 1 1v4a1 1 0 1 1-2 0V6.41l-2.666 2.67a1 1 0 0 1-1.32.083l-.094-.083a1 1 0 0 1 0-1.414l2.664-2.668H16a1 1 0 0 1-.993-.883l-.005-.117a1 1 0 0 1 1-1z"></path></svg></button>

Test Cases:
Map: Zoom level & default focus
Open the hotel map view and verify that the default zoom level and map center appropriately focus on the selected city or search location.
Map: Hotel clustering
Zoom out on the map and check that nearby hotel listings are grouped into visual clusters that dynamically update as the user zooms in.
Map: POI or landmark visibility
Ensure that key points of interest (e.g. train stations, airports, landmarks) are visible and labeled on the map, especially at standard zoom levels.
    """

    result = evaluate_website_feature(str(website_urls), user_prompt)

    # Write result to markdown file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"website_evaluation_{timestamp}.md"

    with open(filename, 'w') as f:
        f.write(str(result))