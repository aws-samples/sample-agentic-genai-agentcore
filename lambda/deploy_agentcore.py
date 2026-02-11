#!/usr/bin/env python3
"""
Lambda function to deploy and manage Agent Core Runtime

This Lambda function handles:
- Deploying agent.py to Agent Core Runtime
- Checking agent status
- Invoking the agent
- Cleaning up resources

Trigger via API Gateway or EventBridge
"""

import json
import os
import time
import logging
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto session
boto_session = Session()


def configure_agent_runtime(agent_name, region):
    """
    Configure the Agent Core Runtime deployment
    """
    logger.info(f"Configuring Agent Core Runtime: {agent_name}")
    
    agentcore_runtime = Runtime()
    
    response = agentcore_runtime.configure(
        entrypoint="agent.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name=agent_name
    )
    
    logger.info(f"Configuration complete: {response}")
    return agentcore_runtime


def launch_agent_runtime(agentcore_runtime):
    """
    Launch the agent to Agent Core Runtime
    """
    logger.info("Launching Agent to Agent Core Runtime")
    
    launch_result = agentcore_runtime.launch()
    
    logger.info(f"Launch complete - Agent ID: {launch_result.agent_id}")
    logger.info(f"Agent ARN: {launch_result.agent_arn}")
    logger.info(f"ECR URI: {launch_result.ecr_uri}")
    
    return launch_result


def wait_for_agent_ready(agentcore_runtime, max_wait_seconds=600):
    """
    Wait for the Agent Core Runtime to be ready
    """
    logger.info("Waiting for Agent Core Runtime to be ready")
    
    end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
    start_time = time.time()
    
    status_response = agentcore_runtime.status()
    status = status_response.endpoint['status']
    
    logger.info(f"Initial status: {status}")
    
    while status not in end_status:
        if time.time() - start_time > max_wait_seconds:
            logger.error(f"Timeout waiting for agent to be ready. Current status: {status}")
            return False, status
        
        logger.info(f"Status: {status} - waiting...")
        time.sleep(10)
        
        status_response = agentcore_runtime.status()
        status = status_response.endpoint['status']
    
    if status == 'READY':
        logger.info("Agent Core Runtime is READY!")
        return True, status
    else:
        logger.error(f"Agent Core Runtime failed with status: {status}")
        return False, status


def invoke_agent_runtime(agentcore_runtime, payload):
    """
    Invoke the agent using the starter toolkit
    """
    logger.info(f"Invoking agent with payload: {json.dumps(payload)}")
    
    invoke_response = agentcore_runtime.invoke(payload)
    
    logger.info("Invocation complete")
    return invoke_response


def invoke_agent_with_boto3(agent_arn, region, payload):
    """
    Invoke the agent using boto3 directly
    """
    logger.info(f"Invoking agent via boto3: {agent_arn}")
    
    agentcore_client = boto3.client('bedrock-agentcore', region_name=region)
    
    boto3_response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        payload=json.dumps(payload)
    )
    
    logger.info("Boto3 invocation complete")
    
    # Process response
    if "text/event-stream" in boto3_response.get("contentType", ""):
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    content.append(line)
        return "\n".join(content)
    else:
        events = []
        for event in boto3_response.get("response", []):
            events.append(event.decode("utf-8"))
        return events[0] if events else None


def get_agent_status(agent_id, region):
    """
    Get the status of an existing agent
    """
    logger.info(f"Getting status for agent: {agent_id}")
    
    agentcore_control_client = boto3.client(
        'bedrock-agentcore-control',
        region_name=region
    )
    
    response = agentcore_control_client.describe_agent_runtime(
        agentRuntimeId=agent_id
    )
    
    return response


def delete_agent_runtime(agent_id, ecr_repo_name, region):
    """
    Delete Agent Core Runtime and ECR repository
    """
    logger.info(f"Deleting Agent Core Runtime: {agent_id}")
    
    agentcore_control_client = boto3.client(
        'bedrock-agentcore-control',
        region_name=region
    )
    ecr_client = boto3.client('ecr', region_name=region)
    
    # Delete Agent Core Runtime
    runtime_delete_response = agentcore_control_client.delete_agent_runtime(
        agentRuntimeId=agent_id
    )
    logger.info(f"Agent deleted: {runtime_delete_response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
    
    # Delete ECR repository
    if ecr_repo_name:
        ecr_delete_response = ecr_client.delete_repository(
            repositoryName=ecr_repo_name,
            force=True
        )
        logger.info(f"ECR repo deleted: {ecr_delete_response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
    
    return {
        'agent_deleted': True,
        'ecr_deleted': bool(ecr_repo_name)
    }


def lambda_handler(event, context):
    """
    AWS Lambda handler for Agent Core Runtime management
    
    Event structure:
    {
        "action": "deploy|status|invoke|delete",
        "agent_name": "campaign_review_agent",
        "agent_id": "abc123",  # For status/invoke/delete
        "agent_arn": "arn:...",  # For invoke
        "ecr_repo_name": "repo-name",  # For delete
        "payload": {...}  # For invoke
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse event
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        action = body.get('action', 'deploy')
        agent_name = body.get('agent_name', 'campaign_review_agent')
        region = body.get('region', os.environ.get('AWS_REGION', 'us-west-2'))
        
        logger.info(f"Action: {action}, Agent: {agent_name}, Region: {region}")
        
        # Handle different actions
        if action == 'deploy':
            # Deploy new agent
            agentcore_runtime = configure_agent_runtime(agent_name, region)
            launch_result = launch_agent_runtime(agentcore_runtime)
            
            # Wait for ready (with timeout)
            is_ready, status = wait_for_agent_ready(agentcore_runtime, max_wait_seconds=300)
            
            if not is_ready:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'success': False,
                        'error': f'Agent failed to become ready. Status: {status}',
                        'agent_id': launch_result.agent_id,
                        'agent_arn': launch_result.agent_arn
                    })
                }
            
            # Test invocation
            test_payload = body.get('test_payload', {
                'campaignId': 'test-lambda-deploy',
                's3Key': 'campaigns/test-lambda-deploy/campaign_brief.md'
            })
            
            try:
                invoke_response = invoke_agent_runtime(agentcore_runtime, test_payload)
            except Exception as e:
                logger.warning(f"Test invocation failed: {str(e)}")
                invoke_response = None
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'action': 'deploy',
                    'agent_id': launch_result.agent_id,
                    'agent_arn': launch_result.agent_arn,
                    'ecr_uri': launch_result.ecr_uri,
                    'status': status,
                    'test_invocation': invoke_response
                })
            }
        
        elif action == 'status':
            # Get agent status
            agent_id = body.get('agent_id')
            if not agent_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'agent_id required for status action'
                    })
                }
            
            status_response = get_agent_status(agent_id, region)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'action': 'status',
                    'agent_id': agent_id,
                    'status': status_response
                })
            }
        
        elif action == 'invoke':
            # Invoke agent
            agent_arn = body.get('agent_arn')
            payload = body.get('payload', {})
            
            if not agent_arn:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'agent_arn required for invoke action'
                    })
                }
            
            invoke_response = invoke_agent_with_boto3(agent_arn, region, payload)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'action': 'invoke',
                    'agent_arn': agent_arn,
                    'response': invoke_response
                })
            }
        
        elif action == 'delete':
            # Delete agent
            agent_id = body.get('agent_id')
            ecr_repo_name = body.get('ecr_repo_name')
            
            if not agent_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'agent_id required for delete action'
                    })
                }
            
            delete_response = delete_agent_runtime(agent_id, ecr_repo_name, region)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'action': 'delete',
                    'agent_id': agent_id,
                    'deleted': delete_response
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Unknown action: {action}. Valid actions: deploy, status, invoke, delete'
                })
            }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            })
        }


# For local testing
if __name__ == "__main__":
    # Test deploy action
    test_event = {
        'action': 'deploy',
        'agent_name': 'campaign_review_agent',
        'region': 'us-west-2'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
