#!/bin/bash

# Lambda deployment script for Bedrock Agent to AgentCore Browser Tool bridge

# Configuration
LAMBDA_NAME="bedrock-agent-browser-bridge"
RUNTIME="python3.11"
TIMEOUT=300
MEMORY_SIZE=512
REGION="us-east-1"
ZIP_FILE="lambda_deployment.zip"

echo "Creating deployment package..."

# Create a temporary directory for the package
rm -rf package/
mkdir package

# Install dependencies
pip install -r requirements.txt -t package/ --platform manylinux2014_x86_64 --only-binary=:all:

# Copy the Lambda function
cp lambda_function.py package/

# Create the zip file
cd package
zip -r ../${ZIP_FILE} . -x "*.pyc" -x "__pycache__/*"
cd ..

# Clean up
rm -rf package/

echo "Deployment package created: ${ZIP_FILE}"
echo ""
echo "To deploy the Lambda function, run:"
echo ""
echo "aws lambda create-function \\"
echo "  --function-name ${LAMBDA_NAME} \\"
echo "  --runtime ${RUNTIME} \\"
echo "  --role arn:aws:iam::ACCOUNT_ID:role/YOUR_LAMBDA_ROLE \\"
echo "  --handler lambda_function.lambda_handler \\"
echo "  --timeout ${TIMEOUT} \\"
echo "  --memory-size ${MEMORY_SIZE} \\"
echo "  --environment Variables={AGENTCORE_BROWSER_ARN=YOUR_BROWSER_ID,AGENTCORE_REGION=${REGION}} \\"
echo "  --zip-file fileb://${ZIP_FILE} \\"
echo "  --region ${REGION}"
echo ""
echo "Or to update an existing function:"
echo ""
echo "aws lambda update-function-code \\"
echo "  --function-name ${LAMBDA_NAME} \\"
echo "  --zip-file fileb://${ZIP_FILE} \\"
echo "  --region ${REGION}"