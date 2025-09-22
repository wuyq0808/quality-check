# Bedrock Agent to AgentCore Browser Tool Bridge

A Lambda function that enables traditional Bedrock Agents to use the AgentCore Browser Tool directly through action groups.

## Architecture

```
Traditional Bedrock Agent
    ↓ (action group)
Lambda Function
    ↓ (start_browser_session)
AgentCore Browser Tool
```

## Files

- `lambda_function.py` - Main Lambda function
- `requirements.txt` - Python dependencies
- `deploy.sh` - Deployment script
- `lambda_iam_policy.json` - IAM trust policy
- `lambda_execution_policy.json` - Lambda execution permissions
- `bedrock_agent_openapi_schema.yaml` - OpenAPI schema for Bedrock Agent action group

## Quick Setup

1. **Deploy Lambda**:
   ```bash
   ./deploy.sh
   ```

2. **Set Environment Variables**:
   - `AGENTCORE_BROWSER_ARN`: Your Browser Tool ID (e.g., `recordingBrowserWithS3_20250916170045-Ec92oniUSi`)
   - `AGENTCORE_REGION`: AWS region (default: `us-east-1`)

3. **Configure Bedrock Agent**:
   - Add action group with Lambda function
   - Upload `bedrock_agent_openapi_schema.yaml` as API schema

## Supported Actions

- **navigate**: Navigate to URL
- **click**: Click element by selector
- **fill-form**: Fill form fields
- **extract**: Extract page content
- **screenshot**: Take screenshot

## Example Usage

```
"Navigate to https://example.com and extract the main heading"
```

The Lambda will:
1. Create browser session
2. Execute browser action
3. Return results to Bedrock Agent
4. Clean up session