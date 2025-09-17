#!/usr/bin/env python3
"""
Test script for the AgentCore browser agent using boto3
"""

import boto3
import json

def test_agent():
    # Create boto3 client for bedrock-agentcore in us-east-1
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')

    # Prepare the payload with system_prompt and user_prompt
    payload = json.dumps({
        "system_prompt": "You are a web navigation expert. Navigate websites efficiently and take screenshots to document your findings. Always close the browser session when finished.",
        "user_prompt": "Navigate to example.com, take a screenshot, and describe what you see on the homepage."
    })

    print("🚀 Testing AgentCore browser agent...")
    print(f"📋 Payload: {payload}")
    print("=" * 60)

    try:
        # Invoke the agent
        response = client.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:295180981731:runtime/agent-aV5jaHDQLm',
            runtimeSessionId='test-session-12345678901234567890123456789012345',  # Must be 33+ chars
            payload=payload,
            qualifier="DEFAULT"  # Optional
        )

        # Read and parse the response
        response_body = response['response'].read()
        response_data = json.loads(response_body)

        print("✅ Agent Response:")
        print(json.dumps(response_data, indent=2))

        # Check if the response indicates success
        if response_data.get('status') == 'success':
            print("\n🎉 SUCCESS: Browser automation completed!")
        else:
            print(f"\n❌ ERROR: {response_data.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error invoking agent: {e}")

if __name__ == "__main__":
    test_agent()