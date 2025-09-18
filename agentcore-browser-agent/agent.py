#!/usr/bin/env python3
"""
AgentCore Browser Agent - Minimal Working Version
"""

import json
from datetime import datetime, timezone
from strands import Agent
from strands.models import BedrockModel
from strands_tools.browser import AgentCoreBrowser
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Initialize AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """AgentCore runtime entrypoint"""
    try:
        # Parse prompt payload
        prompt = payload.get('prompt', '')
        parsed = json.loads(prompt) if isinstance(prompt, str) else prompt
        system_prompt = parsed.get('system_prompt')
        user_prompt = parsed.get('user_prompt')

        if not system_prompt or not user_prompt:
            return {
                'message': 'Error: system_prompt and user_prompt are required',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'model': 'browser-agent'
            }

        # Create browser tool
        browser_tool = AgentCoreBrowser(
            region="eu-central-1",
            identifier="recordingBrowserWithS3_20250917220421_EuCentral1-okm4kGdorG",
            session_timeout=7200
        )

        # Create model
        bedrock_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="eu-central-1"
        )

        # Create agent
        agent = Agent(
            name="BrowserAgent",
            model=bedrock_model,
            tools=[browser_tool.browser],
            system_prompt=system_prompt
        )

        # Execute task
        result = agent(user_prompt)

        return {
            'message': result.message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model': 'browser-agent'
        }

    except Exception as e:
        return {
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model': 'browser-agent'
        }

if __name__ == "__main__":
    app.run()