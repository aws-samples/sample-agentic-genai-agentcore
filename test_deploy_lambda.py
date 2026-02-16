#!/usr/bin/env python3
"""
Test script for the deploy_agentcore Lambda function

This script demonstrates how to invoke the Lambda function
for different actions: deploy, status, invoke, delete
"""

import json
import boto3
import time

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-west-2')

# Lambda function name (update after deployment)
LAMBDA_FUNCTION_NAME = 'DeployAgentCoreFunction'


def invoke_lambda(payload):
    """Invoke the Lambda function with a payload"""
    print(f"\n📤 Invoking Lambda with action: {payload.get('action')}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    print(f"\n📥 Response:")
    print(json.dumps(result, indent=2))
    
    return result


def test_deploy():
    """Test deploying a new agent"""
    print("\n" + "=" * 70)
    print("TEST 1: Deploy Agent to Agent Core Runtime")
    print("=" * 70)
    
    payload = {
        'action': 'deploy',
        'agent_name': 'campaign_review_agent',
        'region': 'us-west-2',
        'test_payload': {
            'campaignId': 'test-lambda-001',
            's3Key': 'campaigns/test-lambda-001/campaign_brief.md'
        }
    }
    
    result = invoke_lambda(payload)
    
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        print(f"\n✅ Deployment successful!")
        print(f"   Agent ID: {body.get('agent_id')}")
        print(f"   Agent ARN: {body.get('agent_arn')}")
        return body
    else:
        print(f"\n❌ Deployment failed!")
        return None


def test_status(agent_id):
    """Test getting agent status"""
    print("\n" + "=" * 70)
    print("TEST 2: Get Agent Status")
    print("=" * 70)
    
    payload = {
        'action': 'status',
        'agent_id': agent_id,
        'region': 'us-west-2'
    }
    
    result = invoke_lambda(payload)
    
    if result.get('statusCode') == 200:
        print(f"\n✅ Status retrieved successfully!")
        return result
    else:
        print(f"\n❌ Status check failed!")
        return None


def test_invoke(agent_arn):
    """Test invoking the agent"""
    print("\n" + "=" * 70)
    print("TEST 3: Invoke Agent")
    print("=" * 70)
    
    payload = {
        'action': 'invoke',
        'agent_arn': agent_arn,
        'region': 'us-west-2',
        'payload': {
            'campaignId': '100',
            's3Key': 'campaign_brief.md'
        }
    }
    
    result = invoke_lambda(payload)
    
    if result.get('statusCode') == 200:
        print(f"\n✅ Invocation successful!")
        return result
    else:
        print(f"\n❌ Invocation failed!")
        return None


def test_delete(agent_id, ecr_repo_name):
    """Test deleting the agent"""
    print("\n" + "=" * 70)
    print("TEST 4: Delete Agent")
    print("=" * 70)
    
    # Confirm deletion
    response = input(f"\n⚠️  Delete agent {agent_id}? (yes/no): ")
    if response.lower() != 'yes':
        print("Deletion cancelled.")
        return None
    
    payload = {
        'action': 'delete',
        'agent_id': agent_id,
        'ecr_repo_name': ecr_repo_name,
        'region': 'us-west-2'
    }
    
    result = invoke_lambda(payload)
    
    if result.get('statusCode') == 200:
        print(f"\n✅ Deletion successful!")
        return result
    else:
        print(f"\n❌ Deletion failed!")
        return None


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 Deploy Agent Core Lambda Function - Test Suite")
    print("=" * 70)
    
    # Test 1: Deploy
    deploy_result = test_deploy()
    if not deploy_result:
        print("\n❌ Deployment failed. Stopping tests.")
        return
    
    agent_id = deploy_result.get('agent_id')
    agent_arn = deploy_result.get('agent_arn')
    ecr_uri = deploy_result.get('ecr_uri')
    ecr_repo_name = ecr_uri.split('/')[-1] if ecr_uri else None
    
    # Wait a bit for agent to stabilize
    print("\n⏳ Waiting 10 seconds for agent to stabilize...")
    time.sleep(10)
    
    # Test 2: Status
    test_status(agent_id)
    
    # Test 3: Invoke
    test_invoke(agent_arn)
    
    # Test 4: Delete (optional)
    test_delete(agent_id, ecr_repo_name)
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
