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
            session_timeout=900,  # 15 minutes
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
You are a senior product manager. You have direct access to browser tools. Use them to complete web navigation tasks.
You must visit the sites in seperate browser tabs. Rate and compare the sites on the requested case.
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
| Cases | [Website 1] | [Website 2] |
|-----------|-----------------------------|-----------------------------|
| Case | 6/7 - Rationale              | 6/7 - Rationale |
### Summary
[Website 1]
- standout strengths  
- drawbacks  
[Website 2]
- standout strengths  
- drawbacks
"""
        )

        result = agent(f"""
Open {website_urls} and evaluate the following feature:
{user_prompt}
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
        "https://www.booking.com",
    ]
    user_prompt = """
For booking.com, there may be an overlay modal about Sign In. Use screenshot to find it, and MUST close it by Clicking the close button: <button aria-label="Dismiss sign-in info." type="button" class="de576f5064 b46cd7aad7 e26a59bb37 c295306d66 c7a901b0e7 daf5d4cb1c"><span class="ec1ff2f0cb"><span class="fc70cba028 ca6ff50764" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="50px"><path d="m13.31 12 6.89-6.89a.93.93 0 1 0-1.31-1.31L12 10.69 5.11 3.8A.93.93 0 0 0 3.8 5.11L10.69 12 3.8 18.89a.93.93 0 0 0 1.31 1.31L12 13.31l6.89 6.89a.93.93 0 1 0 1.31-1.31z"></path></svg></span></span></button>

Find the search box for hotel destinations, test the auto complete feature on it.

Cases: (MUST try more then enough variations to be sure; MUST check large amount of typo likely to be made by users)
1. Type in City name, does the main city destination show as the first results?
2. Type in City name check if relevant POI's show up;
3. Type in City name check if POI's are all in the same language
4. Type in City name with typo, check if it can handle typo and show the correct city name
    """

    result = evaluate_website_feature(str(website_urls), user_prompt)

    # Write result to markdown file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"website_evaluation_{timestamp}.md"

    with open(filename, 'w') as f:
        f.write(str(result))