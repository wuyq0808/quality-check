#!/usr/bin/env python3
"""
Configure S3 Recording for Existing AgentCore Browser
This script creates the IAM role and S3 bucket needed for recording
"""

import boto3
import uuid
import json
from datetime import datetime

# Your browser details
BROWSER_ID = "recordingBrowser_20250916165837-WBY6Xam3ew"
REGION = "us-east-1"
S3_BUCKET_NAME = f"agentcore-recordings-{uuid.uuid4().hex[:8]}"
S3_PREFIX = "browser-sessions"

def get_account_id():
    """Get current AWS account ID"""
    try:
        sts_client = boto3.client('sts')
        return sts_client.get_caller_identity()['Account']
    except Exception as e:
        print(f"❌ Error getting account ID: {e}")
        return None

def create_s3_bucket(bucket_name, region=REGION):
    """Create S3 bucket for recordings"""
    try:
        s3_client = boto3.client('s3', region_name=region)

        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ S3 bucket {bucket_name} already exists")
            return True
        except:
            pass

        # Create bucket (us-east-1 doesn't need LocationConstraint)
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )

        print(f"✅ Created S3 bucket: {bucket_name}")
        return True

    except Exception as e:
        print(f"❌ Error creating S3 bucket: {e}")
        return False

def create_iam_role_for_recording(bucket_name, account_id):
    """Create IAM role with S3 permissions for AgentCore recording"""
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

        # S3 permissions policy
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockAgentCoreS3RecordingPolicy",
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:ListMultipartUploadParts",
                        "s3:AbortMultipartUpload"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}/*"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "aws:ResourceAccount": account_id
                        }
                    }
                }
            ]
        }

        role_name = f"AgentCoreRecordingRole_{uuid.uuid4().hex[:8]}"
        policy_name = "AgentCoreS3RecordingPolicy"

        # Create role
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for AgentCore Browser S3 recording"
        )

        role_arn = role_response['Role']['Arn']
        print(f"✅ Created IAM role: {role_name}")
        print(f"🔗 Role ARN: {role_arn}")

        # Create and attach policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(s3_policy)
        )

        print(f"✅ Attached S3 policy to role")
        return role_arn

    except Exception as e:
        print(f"❌ Error creating IAM role: {e}")
        return None

def check_browser_details(browser_id, region):
    """Check current browser configuration"""
    try:
        cp_client = boto3.client('bedrock-agentcore-control', region_name=region)
        response = cp_client.get_browser(browserId=browser_id)

        print(f"📋 Current Browser Configuration:")
        print(f"Name: {response['name']}")
        print(f"Status: {response['status']}")
        print(f"Created: {response['createdAt']}")

        if 'recording' in response:
            print(f"Recording Enabled: {response['recording'].get('enabled', False)}")
        else:
            print("Recording: Not configured")

        return response

    except Exception as e:
        print(f"❌ Error getting browser details: {e}")
        return None

def main():
    print("🎯 Setup S3 Recording for AgentCore Browser")
    print("=" * 60)
    print(f"Browser ID: {BROWSER_ID}")
    print(f"Region: {REGION}")
    print(f"S3 Bucket: {S3_BUCKET_NAME}")
    print(f"S3 Prefix: {S3_PREFIX}")
    print("=" * 60)

    # Step 1: Get account ID
    print("\n1️⃣  Getting AWS Account ID...")
    account_id = get_account_id()
    if not account_id:
        return
    print(f"✅ Account ID: {account_id}")

    # Step 2: Check current browser
    print(f"\n2️⃣  Checking browser configuration...")
    browser_details = check_browser_details(BROWSER_ID, REGION)
    if not browser_details:
        return

    # Step 3: Create S3 bucket
    print(f"\n3️⃣  Creating S3 bucket...")
    if not create_s3_bucket(S3_BUCKET_NAME, REGION):
        return

    # Step 4: Create IAM role
    print(f"\n4️⃣  Creating IAM role with S3 permissions...")
    role_arn = create_iam_role_for_recording(S3_BUCKET_NAME, account_id)
    if not role_arn:
        return

    # Step 5: Provide manual instructions for updating browser
    print(f"\n5️⃣  Manual Update Required:")
    print("⚠️  AWS doesn't currently support updating browser recording via API.")
    print("You'll need to use AWS CLI to recreate the browser with recording:")

    cli_command = f"""
aws bedrock-agentcore-control create-browser \\
  --region {REGION} \\
  --name "recordingBrowserWithS3_{datetime.now().strftime('%Y%m%d%H%M%S')}" \\
  --description "Browser with S3 recording enabled" \\
  --network-configuration '{{"networkMode": "PUBLIC"}}' \\
  --execution-role-arn "{role_arn}" \\
  --recording '{{"enabled": true, "s3Location": {{"bucket": "{S3_BUCKET_NAME}", "prefix": "{S3_PREFIX}"}}}}' \\
  --client-token "{uuid.uuid4()}"
"""

    print("📋 CLI Command:")
    print(cli_command)

    # Save configuration
    config = {
        'browser_id': BROWSER_ID,
        'new_browser_name': f"recordingBrowserWithS3_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'region': REGION,
        's3_bucket': S3_BUCKET_NAME,
        's3_prefix': S3_PREFIX,
        'role_arn': role_arn,
        'account_id': account_id,
        'cli_command': cli_command.strip()
    }

    print(f"\n💾 Configuration saved to recording_config.json")
    with open('recording_config.json', 'w') as f:
        json.dump(config, f, indent=2, default=str)

    print(f"\n🎉 Setup Complete!")
    print("Next steps:")
    print("1. Run the CLI command above to create a new browser with recording")
    print("2. Update your code to use the new browser identifier")
    print("3. Test recording by starting browser sessions")

if __name__ == "__main__":
    main()