#!/usr/bin/env python3
"""
Direct Strands Agent with AgentCore Browser Tools
LLM gets direct access to browser tools - no custom navigation code
"""

import json
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from custom_browser import CustomAgentCoreBrowser

# Website-specific instructions managed by key
WEBSITE_INSTRUCTIONS = {
    "google_travel_hotels": """
                    # For inputting text into the search box:
                        Before typing, don't click the search box, never click the search box, must not click the search box,
                        Don't clear the current search. Don't click the X.
                        Directly type into the destination search box.
                        When you need to change the search box text, just directly type into it, never click or try to clear it first.
                        Must only use browser "type" action(description="Type text into an element") with selector to type into it.
                        NEVER TRY OTHER CLICKING ACTIONS, THEY CAN NOT INPUT SUCCESSFULLY FOR THIS SITE.
                        This selector is proved to be working: input[placeholder="Search for places, hotels and more"]
                        Try "type" action (description="Type text into an element") UNTIL YOU SUCCESS. Never clear the current search between tries.
                        The destination input element is
                        <input type="text" value="near Novena" jsname="yrriRe" jsaction="focus:h06R8; blur:zjh6rb" class="II2One j0Ppje zmMKJ LbIaRd" autocomplete="off" role="combobox" aria-autocomplete="inline" aria-haspopup="true" aria-expanded="false" placeholder="Search for places, hotels and more" aria-label="Search for places, hotels and more">
                        or when clicked and has dropdown open:
                        <input type="text" value="" jsname="yrriRe" jsaction="focus:h06R8; blur:zjh6rb" class="II2One j0Ppje zmMKJ LbIaRd" autocomplete="off" role="combobox" aria-autocomplete="both" aria-haspopup="true" aria-expanded="true" placeholder="Search for places, hotels and more" aria-label="Search for places, hotels and more" autofocus="" aria-owns="h0T7hb-9">
                    # For hotel partners offering counting:
                        - Skip sponsored listings. They are provide by 1 partner only.
                        - Don't use screenshot to count. It's too slow. Use HTML data to extract the number of partners for each hotel.
                    """,

    "booking_com": "",

    "agoda_com": "Click outside of the calendar to close it if dates are correct",

    "skyscanner_hotels": """
                    # Take snapshot right after the first navigation. You may be redirected to the page 'Are you a person or a robot'.
                      - Don't go to elsewhere. We must resolve the challenge.
                      - Use action human_mouse_move to the button, 
                      - Then press_and_hold action to click the button for 5~10 seconds.
                      - Then human_mouse_move to some random position and do some clicks.
                      - And then must wait long enough for the page to load.
                      - Repeat the process until you success. Refresh the page if needed.
                    # If there's more than one tab opened
                      - Always close the hotel details page tab when your done checking it.
                    # For hotel partners offering counting:
                        - Don't use screenshot to count. It's too slow. Use HTML data to extract the number of partners for each hotel.
                    """,
}

def evaluate_website_feature(feature_instruction, website_key):
    """
    Evaluate a specific website feature using Strands agent with direct browser tool access

    Args:
        feature_instruction (str): Complete instruction containing URL, feature description, and evaluation task
        website_key (str): Key to lookup website instructions from WEBSITE_INSTRUCTIONS

    Returns:
        str: Evaluation results in markdown format
    """
    # Get website instructions by key
    website_instructions = WEBSITE_INSTRUCTIONS.get(website_key, "")

    # Initialize simple string array for storing detailed observations
    observations = []
    # Create a simple memory storage function for the agent
    @tool
    def store_observation(text: str) -> str:
        """Store an observation in the observations array"""
        observations.append(text)
        return f"Stored: {text[:50]}..."

    # Configure browser tool with CustomAgentCoreBrowser (coordinate click + visual screenshots)
    # Note: Recording is enabled with S3 storage in us-east-1
    custom_browser_id = "recordingBrowserWithS3_20250916170045-Ec92oniUSi"
    session_name = "skyscanner-london-hotels"  # Define session name for proper cleanup
    browser_tool = CustomAgentCoreBrowser(
        region='us-east-1',
        identifier=custom_browser_id,
        session_timeout=3600,  # 60 minutes
    )

    # Create explicit Bedrock model with EU region (matching your AWS config)
    bedrock_model = BedrockModel(
        model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="eu-west-1",
        temperature=0.1
    )

    # Build system prompt with website instructions having HIGHEST PRIORITY
    from datetime import datetime, timezone

    base_system_prompt = f"""
Current time: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

You are a detailed web interaction recorder and observer.
Your job is to systematically document everything you see and do while testing website features.
Be subjective and critical in your observations - we need honest truth, not praise.
Point out usability issues, confusing interfaces, slow performance, and any problems you encounter.

You have access to a memory system. Must use store_observation("text") to store key findings and observations on every step.

## Recording Protocol:
1. Take screenshots at each major step - screenshots are the cardinal source of truth
2. Use "click_coordinate" action with pixel coordinates to click elements based on visual analysis
3. Use HTML to collect data for data-heavy pages (e.g., hotel search results, partner/provider offerings) where screenshots are in-efficient.
4. Dismiss pop-ups, cookie banners using coordinate clicks once you see them
5. After clicking on search, selecting hotel, or any clicking that may trigger a new tab, check all tabs/pages we have. Ensure you're working on the correct tab
6. Document every click, type, hover, and navigation action with precise coordinates
7. Record what you see: UI elements, text, buttons, forms, dropdowns, suggestions
8. Capture any errors, loading states, or unexpected behavior

## What to Record:
- **Every Interaction**: Step-by-step actions and their results
- **UI Behavior**: How elements respond (hover effects, loading states)
- **Content Details**: Exact text shown, placeholder text, error messages
- **Navigation Flow**: How you move between different parts of the feature
- **Edge Cases**: What happens with unusual inputs, empty states, errors

## Output:
DON'T OUTPUT ANYTHING AS THE END OF THE SESSION. All the details goes into memory storage (store_observation).

Structure for store_observation calls :
## Testing Session: [Website] - [Feature]
### Step 1: [Action]
- **What I did**: [specific action]
- **What I observed**: [detailed findings]
- **Screenshot**: [describe what screenshot shows]
- **HTML Data** : [summarized data for data-heavy pages]

### Step 2: [Action]
- **What I did**: [specific action]
- **What I observed**: [detailed findings]
- **Screenshot**: [describe what screenshot shows]
- **HTML Data** : [summarized data for data-heavy pages]

Continue for all testing steps...

Store comprehensive records in memory. Be meticulous and thorough.
Describe in detail: findings and observations.
"""

    if website_instructions:
        system_prompt = f"""
CRITICAL HIGHEST PRIORITY INSTRUCTIONS - MUST FOLLOW EXACTLY
{website_instructions}

These website-specific instructions override all other instructions and have absolute priority.

{base_system_prompt}
"""
    else:
        system_prompt = base_system_prompt

    # Create Strands agent with explicit EU model
    agent = Agent(
        name="WebNavigator",
        model=bedrock_model,  # Use explicit EU region model
        tools=[browser_tool.browser, store_observation],  # LLM gets direct access to browser functions and memory
        system_prompt=system_prompt
    )

    # Execute the website feature evaluation task
    print(f"🔍 Starting recording session")
    result = agent(feature_instruction)

    # Retrieve all stored observations
    observations_text = "\n".join([f"- {obs}" for obs in observations])
    # Return both concise result and detailed stored observations
    combined_result = f"{str(result)}\n\n## Detailed Records:\n{observations_text}"
    return combined_result
