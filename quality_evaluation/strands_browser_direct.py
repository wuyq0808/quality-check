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
                    # For the calendar date picker:
                      - Year is not displayed and default to the current year. Don't try to see or change the year.
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
                    """,

    "booking_com": "",

    "agoda_com": "Click outside of the calendar to close it if dates are correct",

    "skyscanner_hotels": """
                    # Take snapshot right after the first navigation. You may be redirected to the page 'Are you a person or a robot'.
                      - Don't go to elsewhere. We must resolve the challenge.
                      - Use action human_mouse_move to the button, 
                      - Then press_and_hold action to click the button for 7~12 seconds.
                      - And then must wait long enough for the page to load. MUST WAIT LONG ENOUGH.
                      - If it's longer than 2 minutes, do some more human_mouse_move and clicks.
                      - NEVER USE OTHER ACTIONS. MUST USE THESE ACTIONS TO RESOLVE THE CHALLENGE.

                    # Check-in / Check-out date pickers:
                      - One for check-in, one for check-out. They are 2 different calanders.
                      - When you selected check-in, the check-in calander will be closed.
                      - Must take screenshot before/after every click to make sure.
                    
                    # Clicking a hotel card in search result page may open a new tab.
                      - Must use 'list_tabs' action after clicking a hotel card in search result page.
                      - Always close the hotel details page tab when your done checking it.

                    # For hotel partners offer counting:
                      - MUST Click the hotel card, get into the hotel details page to count. MUST get into the hotel details page.
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
        session_timeout=7200,  # 2h
    )

    # Create explicit Bedrock model with EU region (matching your AWS config)
    bedrock_model = BedrockModel(
        model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="eu-west-1",
        temperature=0.1
    )

    base_system_prompt = f"""
You are a detailed web interaction recorder and observer.
Your job is to systematically document everything you see and do while testing website features.
Be subjective and critical in your observations - we need honest truth, not praise.
Point out usability issues, confusing interfaces, slow performance, and any problems you encounter.

You must use store_observation("text") to store detailed observations on every step. Store as much information as possible.

## Recording Protocol:
1. Take screenshots after every click - screenshots are the cardinal source of truth
2. Use "click_coordinate" action with pixel coordinates to click elements based on visual analysis
3. Dismiss pop-ups, cookie banners using coordinate clicks once you see them
4. After clicking on search, selecting hotel, or any clicking that may trigger a new tab, check all tabs/pages we have. Ensure you're working on the correct tab
5. Document every click, type, hover, and navigation action with precise coordinates
6. Record what you see: UI elements, text, buttons, forms, dropdowns, suggestions
7. Capture any errors, loading states, or unexpected behavior

## What to Record:
- **Every Interaction**: Step-by-step actions and their results
- **UI Behavior**: How elements respond (hover effects, loading states)
- **Content Details**: Exact text shown, placeholder text, error messages
- **Navigation Flow**: How you move between different parts of the feature
- **Edge Cases**: What happens with unusual inputs, empty states, errors

## Output:
Explain every step when you call tools.

Structure for store_observation calls:
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
    _ = agent(feature_instruction)

    # Retrieve all stored observations
    return "\n".join([f"{obs}" for obs in observations])
