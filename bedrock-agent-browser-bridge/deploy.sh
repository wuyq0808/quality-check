#!/bin/bash

# AWS Lambda Deployment Script for Bedrock Agent Browser Bridge
# This script packages the Lambda function with dependencies

set -e

FUNCTION_NAME="bedrock-agent-browser-bridge"
REGION="eu-west-1"
RUNTIME="python3.11"

echo "🚀 Deploying Bedrock Agent Browser Bridge Lambda Function"
echo "=================================================="

# Create deployment package directory
echo "📦 Creating deployment package..."
rm -rf deployment_package
mkdir -p deployment_package

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt -t deployment_package/

# Copy Strands Tools source code
echo "🔧 Copying Strands Tools source..."
cp -r /Users/yongqiwu/code/tools/src/strands_tools deployment_package/

# Copy Lambda function code
echo "📄 Copying Lambda function code..."
cp lambda_function.py deployment_package/

# Create deployment zip
echo "🗜️  Creating deployment zip..."
cd deployment_package
zip -r ../lambda_deployment.zip .
cd ..

# Deploy to AWS Lambda (uncomment to deploy)
# echo "☁️  Deploying to AWS Lambda..."
# aws lambda update-function-code \
#     --function-name $FUNCTION_NAME \
#     --zip-file fileb://lambda_deployment.zip \
#     --region $REGION

echo "✅ Deployment package created: lambda_deployment.zip"
echo ""
echo "🔧 Environment variables needed:"
echo "   AGENTCORE_BROWSER_ARN=<your-browser-arn>"
echo "   AGENTCORE_REGION=eu-west-1"
echo "   BROWSER_IDENTIFIER=<your-browser-identifier>"
echo "   SESSION_TIMEOUT=3600"
echo ""
echo "📋 IAM Permissions required:"
echo "   - bedrock-agentcore:StartBrowserSession"
echo "   - bedrock-agentcore:StopBrowserSession"
echo "   - bedrock-agentcore:GetBrowserSession"
echo ""
echo "🎯 Ready for deployment!"