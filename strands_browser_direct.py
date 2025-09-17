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

def main():
    """
    Create Strands agent with direct browser tool access
    """
    try:
        # Configure browser tool with AgentCore using new S3 recording browser
        # Note: Recording is enabled with S3 storage in us-east-1
        custom_browser_id = "recordingBrowserWithS3_20250916170045-Ec92oniUSi"
        session_name = "skyscanner-london-hotels"  # Define session name for proper cleanup
        browser_tool = AgentCoreBrowser(
            region='us-east-1',
            identifier=custom_browser_id,  # Your new S3 recording browser!
            session_timeout=7200
        )
        
        # Create explicit Bedrock model with EU region (matching your AWS config)
        bedrock_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",  # EU prefix to match your AWS region!
            region_name="eu-west-1"  # Your actual AWS region
        )

        # Create Strands agent with explicit EU model
        agent = Agent(
            name="AutonomousWebNavigator",
            model=bedrock_model,  # Use explicit EU region model
            tools=[browser_tool.browser],  # LLM gets direct access to browser functions
            system_prompt="""You have direct access to browser tools. Use them autonomously to complete web navigation tasks.

For the Skyscanner hotels search task:
1. Navigate to skyscanner.com
2. Find and click the Hotels link/button to reach hotels page
3. Search for London hotels (enter "London" in destination field)
4. Set check-in and check-out dates if required
5. Submit the search and analyze the results
6. Take screenshots and report what hotels you find (names, prices, ratings)

Make autonomous decisions and use browser tools directly. Be thorough in your analysis of the search results.
After completing the task, you MUST close the browser session."""
        )
        
        try:
            # Execute the main task with proper error handling
            result = agent("Navigate to Skyscanner hotels page, search for London hotels, and tell me what you find. When you're done, close the browser session.")

            return str(result)
        finally:
            # Ensure browser session is properly closed using official workaround
            # See: https://github.com/strands-agents/tools/issues/205
            try:
                print("🔧 Attempting to close browser session...")

                # Use the exact workaround from GitHub issue #205
                close_result = agent("close the browser session")
                print(f"🔧 Browser session close result: {close_result}")

            except Exception as cleanup_error:
                print(f"⚠️ Browser cleanup warning: {cleanup_error}")
                print("🔧 Relying on browser session timeout for cleanup")
        
    except Exception as e:
        error_msg = f"Strands browser tool implementation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {'status': 'error', 'error': error_msg}

if __name__ == "__main__":
    result = main()

    print(result)

    if result and "error" not in str(result).lower():
        print(f"\n🎉 SUCCESS: Strands Agent with custom browser completed!")
    else:
        print(f"❌ Error occurred")