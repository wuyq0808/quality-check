#!/usr/bin/env python3
"""
Create AWS AgentCore Browser with S3 Recording Configuration
This script creates a new custom browser in us-east-1 with S3 recording enabled
"""

import boto3
import uuid
import json
from datetime import datetime

def create_browser_with_s3_recording():
    """
    Create a new AgentCore Browser with S3 recording enabled in us-east-1
    """
    try:
        # Initialize the bedrock-agentcore-control client for us-east-1
        cp_client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')

        # Generate a unique browser name (must match pattern [a-zA-Z][a-zA-Z0-9_]{0,47})
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        browser_name = f"recordingBrowser_{timestamp}"

        # S3 bucket configuration for us-east-1
        s3_bucket_name = f"agentcore-recordings-{uuid.uuid4().hex[:8]}"
        s3_prefix = "browser-sessions"

        print(f"🚀 Creating AgentCore Browser: {browser_name}")
        print(f"📦 S3 Bucket: {s3_bucket_name}")
        print(f"📁 S3 Prefix: {s3_prefix}")
        print(f"🌍 Region: us-east-1")
        print("=" * 60)

        # Create the browser with S3 recording configuration
        # Note: For S3 recording, we need an IAM execution role. Let's try without it first
        create_params = {
            "name": browser_name,
            "description": f"Custom browser with S3 recording created on {datetime.now().isoformat()}",
            "networkConfiguration": {
                "networkMode": "PUBLIC"
            },
            "clientToken": str(uuid.uuid4())
        }

        # Try with recording first - might require executionRoleArn
        try:
            create_params["recording"] = {
                "enabled": True,
                "s3Location": {
                    "bucket": s3_bucket_name,
                    "prefix": s3_prefix
                }
            }
            response = cp_client.create_browser(**create_params)
        except Exception as recording_error:
            print(f"⚠️  Recording requires IAM role. Creating browser without recording first...")
            print(f"Recording error: {str(recording_error)}")

            # Try without recording
            del create_params["recording"]
            response = cp_client.create_browser(**create_params)

        print("✅ Browser created successfully!")
        print("\n📋 Browser Details:")
        print("-" * 40)
        print(f"Browser ID: {response['browserId']}")
        print(f"Browser ARN: {response['browserArn']}")
        print(f"Name: {response['name']}")
        print(f"Status: {response['status']}")
        print(f"Created At: {response['createdAt']}")

        if 'recording' in response:
            recording = response['recording']
            print(f"\n🎥 Recording Configuration:")
            print(f"Enabled: {recording.get('enabled', False)}")
            if 's3Location' in recording:
                s3_location = recording['s3Location']
                print(f"S3 Bucket: {s3_location.get('bucket', 'N/A')}")
                print(f"S3 Prefix: {s3_location.get('prefix', 'N/A')}")

        # Return the configuration for use in your code
        browser_config = {
            'browser_id': response['browserId'],
            'browser_arn': response['browserArn'],
            'name': response['name'],
            'region': 'us-east-1',
            's3_bucket': s3_bucket_name,
            's3_prefix': s3_prefix,
            'recording_enabled': True
        }

        print(f"\n🔧 Use this identifier in your code:")
        print(f"identifier='{response['browserId']}'")

        print(f"\n💾 Configuration saved to browser_config.json")
        with open('browser_config.json', 'w') as f:
            json.dump(browser_config, f, indent=2, default=str)

        return browser_config

    except Exception as e:
        print(f"❌ Error creating browser: {str(e)}")

        # If execution role is missing, provide helpful guidance
        if "executionRoleArn" in str(e) or "role" in str(e).lower():
            print("\n⚠️  IAM Role Required:")
            print("You need to create an IAM role with S3 permissions.")
            print("Here's the IAM policy you need:")

            iam_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "BedrockAgentCoreS3RecordingPolicy",
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:ListMultipartUploadParts",
                            "s3:AbortMultipartUpload",
                            "s3:CreateBucket"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{s3_bucket_name}",
                            f"arn:aws:s3:::{s3_bucket_name}/*"
                        ]
                    }
                ]
            }

            print("\n📄 IAM Policy JSON:")
            print(json.dumps(iam_policy, indent=2))

        return None

def create_s3_bucket_if_needed(bucket_name, region='us-east-1'):
    """
    Create S3 bucket if it doesn't exist
    """
    try:
        s3_client = boto3.client('s3', region_name=region)

        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ S3 bucket {bucket_name} already exists")
            return True
        except:
            pass

        # Create bucket
        if region == 'us-east-1':
            # us-east-1 doesn't require LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )

        print(f"✅ Created S3 bucket: {bucket_name}")
        return True

    except Exception as e:
        print(f"❌ Error creating S3 bucket: {str(e)}")
        return False

def create_iam_role_for_recording():
    """
    Create IAM role for AgentCore S3 recording
    """
    try:
        iam_client = boto3.client('iam')

        # Trust policy for Bedrock AgentCore
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        role_name = f"AgentCoreS3RecordingRole-{uuid.uuid4().hex[:8]}"

        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for AgentCore Browser S3 recording"
        )

        print(f"✅ Created IAM role: {role_name}")
        return response['Role']['Arn']

    except Exception as e:
        print(f"❌ Error creating IAM role: {str(e)}")
        return None

if __name__ == "__main__":
    print("🎯 AWS AgentCore Browser Creator with S3 Recording")
    print("=" * 60)

    # Step 1: Create IAM role (optional - you might want to do this manually)
    print("\n1️⃣  Checking IAM role setup...")
    # role_arn = create_iam_role_for_recording()

    # Step 2: Create browser with recording
    print("\n2️⃣  Creating browser with S3 recording...")
    config = create_browser_with_s3_recording()

    if config:
        print(f"\n🎉 SUCCESS!")
        print(f"Your new browser identifier: {config['browser_id']}")
        print(f"Ready to use in region: {config['region']}")
        print(f"S3 recordings will be stored in: {config['s3_bucket']}/{config['s3_prefix']}")

        print(f"\n📝 Next steps:")
        print("1. Create the S3 bucket manually or run create_s3_bucket_if_needed()")
        print("2. Create IAM role with S3 permissions")
        print("3. Update your browser configuration to use this identifier")

        print(f"\n🔄 Example usage in your code:")
        print(f"""
browser_tool = AgentCoreBrowser(
    region='us-east-1',
    identifier='{config['browser_id']}',
    session_timeout=7200
)""")