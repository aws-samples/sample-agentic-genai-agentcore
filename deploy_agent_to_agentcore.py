#!/usr/bin/env python3
"""
Deploy and invoke agent.py to Bedrock Agent Core Runtime

This script uses the bedrock_agentcore_starter_toolkit to:
1. Configure the Agent Core Runtime deployment
2. Launch the agent to Agent Core Runtime
3. Invoke the agent with a test payload

Based on: https://github.com/awslabs/amazon-bedrock-agentcore-samples
"""

import json
import time
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

def configure_agent_runtime():
    """
    Configure the Agent Core Runtime deployment
    
    This generates the Dockerfile and prepares the deployment configuration
    """
    print("\n" + "=" * 70)
    print("📋 Step 1: Configuring Agent Core Runtime")
    print("=" * 70)
    
    # Initialize boto session
    boto_session = Session()
    region = boto_session.region_name
    print(f"Region: {region}")
    
    # Initialize Runtime
    agentcore_runtime = Runtime()
    
    # Agent configuration
    agent_name = "campaign_review_agent"
    
    print(f"\n🔧 Configuring agent: {agent_name}")
    print(f"   Entrypoint: agent.py")
    print(f"   Requirements: requirements.txt")
    
    # Configure the runtime
    response = agentcore_runtime.configure(
        entrypoint="agent.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region="us-west-2",
        agent_name=agent_name
    )
    
    print("\n✅ Configuration complete!")
    print(f"Response: {response}")
    
    return agentcore_runtime, region


def launch_agent_runtime(agentcore_runtime):
    """
    Launch the agent to Agent Core Runtime
    
    This creates the ECR repository, builds the Docker image,
    pushes it to ECR, and creates the Agent Core Runtime
    """
    print("\n" + "=" * 70)
    print("🚀 Step 2: Launching Agent to Agent Core Runtime")
    print("=" * 70)
    
    print("\n📦 Building and pushing Docker image...")
    print("   This may take several minutes...")
    
    # Launch the agent
    launch_result = agentcore_runtime.launch()
    
    print("\n✅ Launch complete!")
    print(f"   Agent ID: {launch_result.agent_id}")
    print(f"   Agent ARN: {launch_result.agent_arn}")
    print(f"   ECR URI: {launch_result.ecr_uri}")
    
    return launch_result


def wait_for_agent_ready(agentcore_runtime):
    """
    Wait for the Agent Core Runtime to be ready
    """
    print("\n" + "=" * 70)
    print("⏳ Step 3: Waiting for Agent Core Runtime to be ready")
    print("=" * 70)
    
    end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
    
    status_response = agentcore_runtime.status()
    status = status_response.endpoint['status']
    
    print(f"\nInitial status: {status}")
    
    while status not in end_status:
        print(f"   Status: {status} - waiting...")
        time.sleep(10)
        status_response = agentcore_runtime.status()
        status = status_response.endpoint['status']
    
    if status == 'READY':
        print(f"\n✅ Agent Core Runtime is READY!")
    else:
        print(f"\n❌ Agent Core Runtime failed with status: {status}")
        return False
    
    return True


def invoke_agent_with_toolkit(agentcore_runtime):
    """
    Invoke the agent using the starter toolkit
    """
    print("\n" + "=" * 70)
    print("🎯 Step 4: Invoking Agent with Starter Toolkit")
    print("=" * 70)
    
    # Prepare payload matching agent.py's expected format
    payload = {
        "campaignId": "test-campaign-001",
        "s3Key": "campaigns/test-campaign-001/campaign_brief.md"
    }
    
    print(f"\n📤 Sending payload:")
    print(json.dumps(payload, indent=2))
    
    # Invoke the agent
    invoke_response = agentcore_runtime.invoke(payload)
    
    print("\n✅ Invocation complete!")
    print(f"\n📥 Response:")
    print(json.dumps(invoke_response, indent=2))
    
    return invoke_response


def invoke_agent_with_boto3(launch_result, region):
    """
    Invoke the agent using boto3 directly
    
    This demonstrates how to invoke the agent from your application code
    """
    print("\n" + "=" * 70)
    print("🎯 Step 5: Invoking Agent with boto3")
    print("=" * 70)
    
    import boto3
    
    agent_arn = launch_result.agent_arn
    
    # Initialize boto3 client
    agentcore_client = boto3.client(
        'bedrock-agentcore',
        region_name=region
    )
    
    # Prepare payload
    payload = {
        "campaignId": "test-campaign-002",
        "s3Key": "campaigns/test-campaign-002/campaign_brief.md"
    }
    
    print(f"\n📤 Sending payload:")
    print(json.dumps(payload, indent=2))
    
    # Invoke the agent
    boto3_response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        payload=json.dumps(payload)
    )
    
    print("\n✅ Invocation complete!")
    print(f"Content Type: {boto3_response.get('contentType', 'unknown')}")
    
    # Process response based on content type
    if "text/event-stream" in boto3_response.get("contentType", ""):
        print("\n📥 Streaming response:")
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    print(line)
                    content.append(line)
        
        full_response = "\n".join(content)
        print(f"\n📦 Full response:")
        print(full_response)
        return full_response
    else:
        print("\n📥 Non-streaming response:")
        try:
            events = []
            for event in boto3_response.get("response", []):
                events.append(event)
            
            if events:
                response_text = events[0].decode("utf-8")
                print(response_text)
                return json.loads(response_text)
        except Exception as e:
            print(f"Error reading response: {e}")
            return None


def cleanup_resources(launch_result, region):
    """
    Clean up the Agent Core Runtime and ECR repository
    
    WARNING: This will delete the agent and container image!
    """
    print("\n" + "=" * 70)
    print("🧹 Cleanup: Deleting Agent Core Runtime and ECR Repository")
    print("=" * 70)
    
    import boto3
    
    # Confirm cleanup
    response = input("\n⚠️  Are you sure you want to delete the agent? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled.")
        return
    
    # Initialize clients
    agentcore_control_client = boto3.client(
        'bedrock-agentcore-control',
        region_name=region
    )
    ecr_client = boto3.client(
        'ecr',
        region_name=region
    )
    
    # Delete Agent Core Runtime
    print(f"\n🗑️  Deleting Agent Core Runtime: {launch_result.agent_id}")
    runtime_delete_response = agentcore_control_client.delete_agent_runtime(
        agentRuntimeId=launch_result.agent_id
    )
    print(f"   Status: {runtime_delete_response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
    
    # Delete ECR repository
    ecr_repo_name = launch_result.ecr_uri.split('/')[1]
    print(f"\n🗑️  Deleting ECR repository: {ecr_repo_name}")
    ecr_delete_response = ecr_client.delete_repository(
        repositoryName=ecr_repo_name,
        force=True
    )
    print(f"   Status: {ecr_delete_response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
    
    print("\n✅ Cleanup complete!")


def main():
    """
    Main execution flow
    """
    print("\n" + "=" * 70)
    print("🎯 Campaign Review Agent - Agent Core Runtime Deployment")
    print("=" * 70)
    
    try:
        # Step 1: Configure
        agentcore_runtime, region = configure_agent_runtime()
        
        # Step 2: Launch
        launch_result = launch_agent_runtime(agentcore_runtime)
        
        # Step 3: Wait for ready
        if not wait_for_agent_ready(agentcore_runtime):
            print("\n❌ Agent failed to become ready. Exiting.")
            return 1
        
        # Step 4: Invoke with toolkit
        invoke_agent_with_toolkit(agentcore_runtime)
        
        # Step 5: Invoke with boto3
        invoke_agent_with_boto3(launch_result, region)
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 Deployment Summary")
        print("=" * 70)
        print(f"\n✅ Agent successfully deployed and tested!")
        print(f"\n📋 Agent Details:")
        print(f"   Agent ID: {launch_result.agent_id}")
        print(f"   Agent ARN: {launch_result.agent_arn}")
        print(f"   ECR URI: {launch_result.ecr_uri}")
        print(f"   Region: {region}")
        
        print(f"\n💡 To invoke from your application:")
        print(f"""
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='{region}')
response = client.invoke_agent_runtime(
    agentRuntimeArn='{launch_result.agent_arn}',
    qualifier='DEFAULT',
    payload=json.dumps({{
        'campaignId': 'your-campaign-id',
        's3Key': 'campaigns/your-campaign-id/campaign_brief.md'
    }})
)
""")
        
        # Optional cleanup
        print("\n" + "=" * 70)
        cleanup_resources(launch_result, region)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
