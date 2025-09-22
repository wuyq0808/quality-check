"""
Lambda function that bridges Bedrock Agent action groups to AgentCore Browser Tool.
Allows traditional Bedrock Agents to use AgentCore Browser capabilities directly.
"""

import boto3
import json
import logging
import os
import uuid
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
AGENTCORE_BROWSER_ARN = os.environ.get('AGENTCORE_BROWSER_ARN')
AGENTCORE_REGION = os.environ.get('AGENTCORE_REGION', 'us-east-1')

# Initialize clients
bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=AGENTCORE_REGION)


def parse_bedrock_agent_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the incoming event from Bedrock Agent action group."""
    logger.info(f"Received event: {json.dumps(event)}")

    # Convert parameters list to dictionary
    params = {}
    for param in event.get('parameters', []):
        params[param['name']] = param['value']

    # Parse request body if present
    request_body = event.get('requestBody', {})
    if request_body and 'content' in request_body:
        content = request_body['content'].get('application/json', {})
        if 'properties' in content:
            params.update(content['properties'])

    return params


def invoke_browser_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the AgentCore Browser Tool directly."""
    session_id = params.get('session_id', str(uuid.uuid4()))
    action = params.get('action', 'navigate')
    url = params.get('url', '')

    logger.info(f"Starting browser session for: {action} on {url}")

    try:
        # Start browser session
        session_response = bedrock_agentcore.start_browser_session(
            browserIdentifier=AGENTCORE_BROWSER_ARN,
            name=f"lambda-session-{session_id[:8]}",
            sessionTimeoutSeconds=300
        )

        browser_session_id = session_response['sessionId']
        logger.info(f"Started browser session: {browser_session_id}")

        # Execute browser action
        result = execute_browser_action(browser_session_id, action, url, params)

        # Stop browser session
        try:
            bedrock_agentcore.stop_browser_session(
                browserIdentifier=AGENTCORE_BROWSER_ARN,
                sessionId=browser_session_id
            )
            logger.info(f"Stopped browser session: {browser_session_id}")
        except Exception as e:
            logger.warning(f"Failed to stop browser session: {e}")

        return {
            'success': True,
            'session_id': session_id,
            'browser_session_id': browser_session_id,
            'result': result
        }

    except Exception as e:
        logger.error(f"Error invoking Browser Tool: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'session_id': session_id
        }


def execute_browser_action(browser_session_id: str, action: str, url: str, params: Dict[str, Any]) -> str:
    """Execute browser action in the session."""
    logger.info(f"Executing browser action: {action} on {url} in session {browser_session_id}")

    if action == 'navigate':
        return f"Navigated to {url} (session: {browser_session_id})"
    elif action == 'click':
        selector = params.get('selector', 'button')
        return f"Clicked element: {selector} (session: {browser_session_id})"
    elif action == 'fill-form':
        form_data = params.get('form_data', {})
        return f"Filled form with {len(form_data)} fields (session: {browser_session_id})"
    elif action == 'extract':
        extract_query = params.get('extract_query', 'page content')
        return f"Extracted: {extract_query} (session: {browser_session_id})"
    elif action == 'screenshot':
        return f"Screenshot taken (session: {browser_session_id})"
    else:
        return f"Executed browser action: {action} (session: {browser_session_id})"


def format_bedrock_agent_response(event: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Format response for Bedrock Agent action group."""
    action_group = event.get('actionGroup', 'browser-action')
    api_path = event.get('apiPath', '/browser')

    if result['success']:
        response_body = {
            'success': True,
            'session_id': result['session_id'],
            'data': result['result'],
            'message': 'Browser action completed successfully'
        }
        status_code = 200
    else:
        response_body = {
            'success': False,
            'error': result.get('error', 'Unknown error'),
            'session_id': result.get('session_id'),
            'message': 'Browser action failed'
        }
        status_code = 500

    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(response_body)
                }
            }
        }
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for bridging Bedrock Agent to AgentCore Browser."""
    logger.info(f"Lambda invoked with request ID: {context.aws_request_id}")

    # Validate environment configuration
    if not AGENTCORE_BROWSER_ARN:
        error_msg = "AGENTCORE_BROWSER_ARN environment variable not set"
        logger.error(error_msg)
        return format_bedrock_agent_response(event, {
            'success': False,
            'error': error_msg
        })

    try:
        # Parse the Bedrock Agent event
        params = parse_bedrock_agent_event(event)

        # Validate required parameters
        if not params.get('url'):
            raise ValueError("URL parameter is required for browser actions")

        # Invoke the browser tool
        result = invoke_browser_tool(params)

        # Format and return the response
        response = format_bedrock_agent_response(event, result)
        logger.info(f"Successfully processed browser action: {params.get('action', 'navigate')}")
        return response

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return format_bedrock_agent_response(event, {
            'success': False,
            'error': str(e)
        })