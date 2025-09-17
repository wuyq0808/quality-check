# AgentCore Browser Agent

A configurable Strands browser automation agent deployable to AWS Bedrock AgentCore Runtime.

## Features

- **Configurable Prompts**: Custom system and user prompts via API or command line
- **Browser Automation**: Uses AgentCore Browser for web navigation
- **AgentCore Runtime Ready**: Deployed with `@app.entrypoint` decorator
- **Error Handling**: Structured error responses and browser session cleanup
- **Local Testing**: Works locally with command-line arguments

## Project Structure

```
agentcore-browser-agent/
├── agent.py           # Main agent script
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Local Usage

```bash
# With custom prompts
python agent.py --system-prompt "You are a web expert" --user-prompt "Navigate to example.com"

# Both prompts are required
python agent.py --system-prompt "Your role" --user-prompt "Your task"
```

## AgentCore Deployment

### 1. Configure
```bash
cd agentcore-browser-agent
agentcore configure -e agent.py
```

### 2. Deploy
```bash
agentcore launch
```

### 3. Test
```bash
agentcore invoke '{"system_prompt": "You are a web navigation expert", "user_prompt": "Navigate to example.com and describe what you see"}'
```

## API Request Format

When deployed to AgentCore, send requests with:

```json
{
  "system_prompt": "You are a browser automation expert...",
  "user_prompt": "Navigate to google.com and search for AI agents"
}
```

## Response Format

```json
{
  "status": "success",
  "result": "Navigation completed successfully...",
  "timestamp": "2025-09-17T18:12:06.938155"
}
```

Or for errors:

```json
{
  "status": "error",
  "error": "system_prompt is required",
  "timestamp": "2025-09-17T18:12:06.938155"
}
```

## Configuration

- **Browser ID**: Uses custom recording browser with S3 storage
- **Model**: Claude Sonnet 4 in EU region
- **Browser Region**: us-east-1
- **Session Timeout**: 7200 seconds (2 hours)

## Requirements

- Python 3.10+
- AWS credentials configured
- AgentCore starter toolkit installed
- Strands Agents and tools