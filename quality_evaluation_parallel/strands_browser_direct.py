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

def evaluate_website_feature(website_url, feature_description):
    """
    Evaluate a specific website feature using Strands agent with direct browser tool access

    Args:
        website_url (str): The URL of the website to evaluate
        feature_description (str): Description of the feature to test and evaluate

    Returns:
        str: Evaluation results in markdown format
    """
    try:
        # Configure browser tool with AgentCore using new S3 recording browser
        # Note: Recording is enabled with S3 storage in us-east-1
        custom_browser_id = "recordingBrowserWithS3_20250916170045-Ec92oniUSi"
        session_name = "skyscanner-london-hotels"  # Define session name for proper cleanup
        browser_tool = AgentCoreBrowser(
            region='us-east-1',
            identifier=custom_browser_id,
            session_timeout=900,  # 15 minutes
        )
        
        # Create explicit Bedrock model with EU region (matching your AWS config)
        bedrock_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="eu-west-1",
            temperature=0.1
        )

        # Create Strands agent with explicit EU model
        agent = Agent(
            name="WebNavigator",
            model=bedrock_model,  # Use explicit EU region model
            tools=[browser_tool.browser],  # LLM gets direct access to browser functions
            system_prompt="""
You are a detailed web interaction recorder and observer. Your job is to systematically document everything you see and do while testing website features.

## Recording Protocol:
1. Always take screenshots at each major step
2. Document every click, type, hover, and navigation action
3. Record what you see: UI elements, text, buttons, forms, dropdowns, suggestions
4. Note timing and responsiveness of interactions
5. Capture any errors, loading states, or unexpected behavior

## What to Record:
- **Initial Page State**: What's visible when you first arrive
- **Every Interaction**: Step-by-step actions and their results
- **UI Behavior**: How elements respond (hover effects, loading states)
- **Content Details**: Exact text shown, placeholder text, error messages
- **Performance Observations**: Loading times, responsiveness, delays
- **Navigation Flow**: How you move between different parts of the feature
- **Edge Cases**: What happens with unusual inputs, empty states, errors

## Output Format:
Provide a chronological narrative of your testing session with detailed observations. Do NOT rate or evaluate - just record what happened.

Structure as:
## Testing Session: [Website] - [Feature]
### Step 1: [Action]
- **What I did**: [specific action]
- **What I observed**: [detailed findings]
- **Screenshot**: [describe what screenshot shows]

### Step 2: [Action]
- **What I did**: [specific action]
- **What I observed**: [detailed findings]
- **Screenshot**: [describe what screenshot shows]

Continue for all testing steps...

Focus on comprehensive documentation - another agent will use your detailed records for evaluation.
"""
        )

        # Execute the website feature evaluation task
        result = agent(f"""
Navigate to {website_url} and evaluate the following feature:

{feature_description}

Please test thoroughly and document all your observations.
        """)

        return str(result)
        
    except Exception as e:
        error_msg = f"Strands browser tool implementation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {'status': 'error', 'error': error_msg}

if __name__ == "__main__":
    # Example usage
    website_url = "https://www.skyscanner.com"
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

    result = evaluate_website_feature(website_url, feature_description)

    print(result)

    if result and "error" not in str(result).lower():
        print(f"\n🎉 SUCCESS: Strands Agent with custom browser completed!")
    else:
        print(f"❌ Error occurred")