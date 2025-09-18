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
    return f"nova-pro-test-{timestamp}-{random_id}"
REGION = 'eu-central-1'

# Prompt constants
SYSTEM_PROMPT = """
You are a web navigation expert. When you load a page, immediately look for and
handle any modal dialogs, cookie banners, or privacy notices by clicking
accept/allow buttons. Always take screenshots before and after major actions.
Navigate websites efficiently and document your findings. Always close the
browser session when finished.
""".strip()

USER_PROMPT = """
Follow these steps in order:

1. Navigate to Skyscanner website (https://www.skyscanner.de)

2. IMMEDIATELY look for cookie/privacy modal dialog and click the accept button.
   Common button texts: 'Accept All', 'Accept Cookies', 'I Accept', 'Allow All',
   'Continue'. This is CRITICAL - the site won't work without accepting cookies.

3. Check if the site is in English. If not, look for language selector (usually
   in top banner or footer) and change to English.

4. Look for Hotels section/tab and click on it.

5. Search for hotels in London by entering 'London' in the destination field.

6. Describe what you found and close the browser session.
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