#!/usr/bin/env python3
"""
Test script for the AgentCore browser agent using boto3
"""

import boto3
import json
import uuid
import datetime

# Configuration constants
AGENT_RUNTIME_ARN = 'arn:aws:bedrock-agentcore:eu-central-1:295180981731:runtime/agent-ASfqOr83Ry'
# Generate random session ID (33+ chars required)
def generate_session_id():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    random_id = str(uuid.uuid4()).replace('-', '')[:12]
    return f"test-session-{timestamp}-{random_id}"
REGION = 'eu-central-1'

# Prompt constants
SYSTEM_PROMPT = """
You are a web navigation expert. 
""".strip()

USER_PROMPT = """
Follow these steps in order:

1. Navigate to Skyscanner website (https://www.skyscanner.de)

2. Accept Cookies

3. Change language to English
""".strip()

def test_agent():
    # Generate fresh session ID for this test run
    session_id = generate_session_id()
    print(f"🔑 Generated session ID: {session_id}")

    # Create boto3 client for bedrock-agentcore
    client = boto3.client('bedrock-agentcore', region_name=REGION)

    # Prepare the payload - AgentCore expects "prompt" key with JSON string
    prompt_data = {
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": USER_PROMPT
    }
    payload = json.dumps({
        "prompt": json.dumps(prompt_data)
    })

    print("🚀 Testing AgentCore browser agent...")
    print(f"📋 Payload: {payload}")
    print("=" * 60)

    try:
        # Invoke the agent
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT"
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