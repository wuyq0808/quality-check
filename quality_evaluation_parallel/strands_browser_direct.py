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

def evaluate_website_feature(website_specific_prompt):
    """
    Evaluate a specific website feature using Strands agent with direct browser tool access

    Args:
        website_specific_prompt (str): Complete prompt containing URL, feature description, and website-specific instructions

    Returns:
        str: Evaluation results in markdown format
    """
    try:
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
            session_timeout=1800,  # 30 minutes
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
            tools=[browser_tool.browser, store_observation],  # LLM gets direct access to browser functions and memory
            system_prompt="""
You are a detailed web interaction recorder and observer. Your job is to systematically document everything you see and do while testing website features.
You have access to a memory system. Must use store_observation("text") to store key findings and observations on every step.

## Recording Protocol:
1. Always take screenshots at each major step - screenshots are the cardinal source of truth
2. Get HTML data only when recording important data (e.g., hotel lists, search results) to help support what's visible in screenshots
3. Use click_coordinate with pixel coordinates to click elements based on visual analysis
4. Must dismiss/close pop-ups, cookie banners, and modals using coordinate clicks once you see them
5. After clicking on search/screenshot failure, MUST check all tabs/pages we have. Ensure you're working on the correct tab
6. Document every click, type, hover, and navigation action with precise coordinates
7. Record what you see: UI elements, text, buttons, forms, dropdowns, suggestions
8. For data-heavy pages (hotel lists, search results), use HTML data only to help extract details that support what's shown in screenshots
9. Note timing and responsiveness of interactions
10. Capture any errors, loading states, or unexpected behavior

## What to Record:
- **Initial Page State**: What's visible when you first arrive (screenshots are the primary record)
- **Every Interaction**: Step-by-step actions and their results
- **UI Behavior**: How elements respond (hover effects, loading states)
- **Content Details**: Exact text shown, placeholder text, error messages
- **Performance Observations**: Loading times, responsiveness, delays
- **Navigation Flow**: How you move between different parts of the feature
- **Edge Cases**: What happens with unusual inputs, empty states, errors

## Output:
Your main output must be very brief - NEVER summarize / analyze / evaluate EVEN IF ASKED - just key results. All the details goes into memory storage.

Structure for memory storage:
## Testing Session: [Website] - [Feature]
### Step 1: [Action]
- **What I did**: [specific action]
- **What I observed**: [detailed findings]
- **Screenshot**: [describe what screenshot shows - this is what's real]
- **HTML Data** (if helpful for important data): [supporting details to help extract information visible in screenshot]

### Step 2: [Action]
- **What I did**: [specific action]
- **What I observed**: [detailed findings]
- **Screenshot**: [describe what screenshot shows - this is what's real]
- **HTML Data** (if helpful for important data): [supporting details to help extract information visible in screenshot]

Continue for all testing steps...

Focus on storing comprehensive records in memory - another agent will use your stored detailed records for evaluation.
For memory storage: NEVER summarize / analyze / evaluate / rate EVEN IF ASKED.
"""
        )

        # Execute the website feature evaluation task
        print(f"🔍 Starting recording session")
        result = agent(website_specific_prompt)

        # Retrieve all stored observations
        if observations:
            observations_text = "\n".join([f"- {obs}" for obs in observations])
            # Return both concise result and detailed stored observations
            combined_result = f"{str(result)}\n\n## Detailed Records:\n{observations_text}"
            return combined_result
        else:
            return str(result)
        
    except Exception as e:
        error_msg = f"Strands browser tool implementation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {'status': 'error', 'error': error_msg}
