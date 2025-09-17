#!/usr/bin/env python3
"""
Strands Agent for AgentCore Runtime Deployment
Configurable system and user prompts for browser automation
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from strands import Agent
from strands.models import BedrockModel
from strands_tools.browser import AgentCoreBrowser

try:
    from bedrock_agentcore import BedrockAgentCoreApp
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False
    print("⚠️ AgentCore SDK not available - running in local mode")

class ConfigurableBrowserAgent:
    """Strands browser agent with configurable prompts"""

    def __init__(self,
                 custom_browser_id: str = "recordingBrowserWithS3_20250916170045-Ec92oniUSi",
                 region: str = "us-east-1",
                 model_region: str = "eu-west-1"):
        self.custom_browser_id = custom_browser_id
        self.region = region
        self.model_region = model_region

    def create_agent(self, system_prompt: str) -> Agent:
        """Create Strands agent with custom system prompt"""

        # Configure browser tool
        browser_tool = AgentCoreBrowser(
            region=self.region,
            identifier=self.custom_browser_id,
            session_timeout=7200
        )

        # Create Bedrock model
        bedrock_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name=self.model_region
        )

        # Create Strands agent
        agent = Agent(
            name="ConfigurableBrowserAgent",
            model=bedrock_model,
            tools=[browser_tool.browser],
            system_prompt=system_prompt
        )

        return agent

    def execute_task(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Execute browser automation task with custom prompts"""
        try:
            agent = self.create_agent(system_prompt)

            try:
                result = agent(user_prompt)
                return {
                    'status': 'success',
                    'result': str(result),
                    'timestamp': datetime.now().isoformat()
                }
            finally:
                # Cleanup browser session
                try:
                    print("🔧 Closing browser session...")
                    close_result = agent("close the browser session")
                    print(f"🔧 Browser session closed: {close_result}")
                except Exception as cleanup_error:
                    print(f"⚠️ Browser cleanup warning: {cleanup_error}")

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Initialize agent
browser_agent = ConfigurableBrowserAgent()

def main_task(system_prompt: Optional[str] = None, user_prompt: Optional[str] = None):
    """Main execution function with configurable prompts"""
    if not system_prompt:
        return {
            'status': 'error',
            'error': 'system_prompt is required',
            'timestamp': datetime.now().isoformat()
        }

    if not user_prompt:
        return {
            'status': 'error',
            'error': 'user_prompt is required',
            'timestamp': datetime.now().isoformat()
        }

    print(f"🤖 System Prompt: {system_prompt[:100]}...")
    print(f"👤 User Prompt: {user_prompt}")
    print("=" * 50)

    result = browser_agent.execute_task(system_prompt, user_prompt)
    return result

# AgentCore Runtime Integration
if AGENTCORE_AVAILABLE:
    app = BedrockAgentCoreApp()

    @app.entrypoint
    def agentcore_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
        """AgentCore runtime entrypoint with request handling"""
        try:
            # Extract prompts directly from payload
            system_prompt = payload.get('system_prompt')
            user_prompt = payload.get('user_prompt')

            print(f"🔍 Received payload: {payload}")
            print(f"🤖 System prompt: {system_prompt}")
            print(f"👤 User prompt: {user_prompt}")

            # Execute task
            result = main_task(system_prompt, user_prompt)

            return result

        except Exception as e:
            error_response = {
                'status': 'error',
                'error': f"AgentCore handler error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
            return error_response

# Local execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Configurable Strands Browser Agent')
    parser.add_argument('--system-prompt', type=str, help='Custom system prompt')
    parser.add_argument('--user-prompt', type=str, help='Custom user prompt')

    args = parser.parse_args()

    result = main_task(args.system_prompt, args.user_prompt)

    print("\n" + "=" * 50)
    print("🎯 EXECUTION RESULT:")
    print(json.dumps(result, indent=2))

    if result.get('status') == 'success':
        print("\n🎉 SUCCESS: Browser automation completed!")
    else:
        print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")