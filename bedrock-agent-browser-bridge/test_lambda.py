#!/usr/bin/env python3
"""
Minimal test for Lambda function.
"""

import sys
from unittest.mock import Mock

sys.path.insert(0, '.')
from lambda_function import lambda_handler

def create_mock_context():
    """Create a mock Lambda context."""
    context = Mock()
    context.aws_request_id = "test-request-123"
    return context

def test_lambda():
    """Test Lambda handler."""
    event = {
        "action": {
            "type": "init_session",
            "session_name": "test-session-001",
            "description": "Test browser session"
        }
    }

    context = create_mock_context()
    response = lambda_handler(event, context)
    print(f"Response: {response}")

if __name__ == "__main__":
    test_lambda()