# AgentCore Browser Agent Setup

## Development Environment
- Use agentcore_env: `source agentcore_env/bin/activate`
- Working directory: `/Users/yongqiwu/code/quality-check/agentcore-browser-agent/`

## Deploy Agent
```bash
cd agentcore-browser-agent
source ../agentcore_env/bin/activate
agentcore launch
```

## Test Agent
```bash
cd agentcore-browser-agent
source ../agentcore_env/bin/activate
python3 test_agent.py
```

## Agent Configuration
- Region: eu-central-1
- Model: eu.anthropic.claude-sonnet-4-20250514-v1:0
- Browser: recordingBrowserWithS3_20250917220421_EuCentral1-okm4kGdorG
- Agent ARN: arn:aws:bedrock-agentcore:eu-central-1:295180981731:runtime/agent-ASfqOr83Ry