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


def ensure_iam_role(region, account_id):
    """
    Ensure IAM execution role exists with proper trust policy and permissions
    Based on deploy.sh create_iam_role function
    Also handles existing roles with random suffixes from previous deployments
    """
    logger.info("Ensuring IAM execution role exists...")
    
    iam_client = boto3.client('iam', region_name=region)
    role_name = f"AmazonBedrockAgentCoreSDKRuntime-{region}"
    role_arn = None
    
    # First, check if there's an existing role with random suffix from previous toolkit runs
    try:
        paginator = iam_client.get_paginator('list_roles')
        role_prefix = f"AmazonBedrockAgentCoreSDKRuntime-{region}-"
        
        for page in paginator.paginate():
            for role in page['Roles']:
                if role['RoleName'].startswith(role_prefix):
                    existing_role_name = role['RoleName']
                    logger.info(f"Found existing role with random suffix: {existing_role_name}")
                    
                    # Add ECR permissions to this existing role
                    ecr_policy = {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Action": [
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchGetImage",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchCheckLayerAvailability"
                            ],
                            "Resource": "*"
                        }]
                    }
                    
                    iam_client.put_role_policy(
                        RoleName=existing_role_name,
                        PolicyName="AgentCoreECRAccess",
                        PolicyDocument=json.dumps(ecr_policy)
                    )
                    logger.info(f"Added ECR permissions to existing role: {existing_role_name}")
                    
                    # Add Memory permissions
                    memory_policy = {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Action": [
                                "bedrock-agentcore:ListMemories",
                                "bedrock-agentcore:GetMemory",
                                "bedrock-agentcore:CreateMemory",
                                "bedrock-agentcore:UpdateMemory",
                                "bedrock-agentcore:DeleteMemory",
                                "bedrock-agentcore:ListEvents",
                                "bedrock-agentcore:GetEvent",
                                "bedrock-agentcore:CreateEvent",
                                "bedrock-agentcore:DeleteEvent"
                            ],
                            "Resource": "*"
                        }]
                    }
                    
                    iam_client.put_role_policy(
                        RoleName=existing_role_name,
                        PolicyName="AgentCoreMemoryAccess",
                        PolicyDocument=json.dumps(memory_policy)
                    )
                    logger.info(f"Added Memory permissions to existing role: {existing_role_name}")
                    
                    # Add S3 permissions for campaign bucket access
                    campaign_bucket = os.environ.get('CAMPAIGN_BUCKET', 'unified-campaign-review-test')
                    s3_policy = {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket",
                                "s3:CreateBucket",
                                "s3:PutLifecycleConfiguration"
                            ],
                            "Resource": [
                                "arn:aws:s3:::bedrock-agentcore-*",
                                "arn:aws:s3:::bedrock-agentcore-*/*",
                                f"arn:aws:s3:::{campaign_bucket}",
                                f"arn:aws:s3:::{campaign_bucket}/*"
                            ]
                        }]
                    }
                    
                    iam_client.put_role_policy(
                        RoleName=existing_role_name,
                        PolicyName="AgentCoreS3Access",
                        PolicyDocument=json.dumps(s3_policy)
                    )
                    logger.info(f"Added S3 permissions to existing role: {existing_role_name} for bucket: {campaign_bucket}")
                    
                    # Add DynamoDB permissions for PersonaTable access
                    dynamodb_policy = {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Action": [
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan",
                                "dynamodb:BatchGetItem",
                                "dynamodb:BatchWriteItem",
                                "dynamodb:DescribeTable"
                            ],
                            "Resource": [
                                f"arn:aws:dynamodb:{region}:{account_id}:table/PersonaTable",
                                f"arn:aws:dynamodb:{region}:{account_id}:table/PersonaTable/*"
                            ]
                        }]
                    }
                    
                    iam_client.put_role_policy(
                        RoleName=existing_role_name,
                        PolicyName="AgentCoreDynamoDBAccess",
                        PolicyDocument=json.dumps(dynamodb_policy)
                    )
                    logger.info(f"Added DynamoDB permissions to existing role: {existing_role_name}")
                    
                    role_arn = role['Arn']
                    role_name = existing_role_name
                    break
            if role_arn:
                break
    except Exception as e:
        logger.warning(f"Could not search for existing roles: {str(e)}")
    
    # If no existing role found, check for or create the standard role
    if not role_arn:
        try:
            # Check if standard role exists
            role_response = iam_client.get_role(RoleName=role_name)
            logger.info(f"IAM Role exists: {role_name}")
            role_arn = role_response['Role']['Arn']
        except iam_client.exceptions.NoSuchEntityException:
            # Create role with trust policy for bedrock-agentcore service
            logger.info(f"Creating IAM Role: {role_name}")
            
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }
            
            create_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Execution role for Bedrock Agent Core Runtime"
            )
            role_arn = create_response['Role']['Arn']
            logger.info(f"Created IAM Role: {role_name}")
            
            # Attach AmazonBedrockFullAccess policy
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
            )
            logger.info("Attached AmazonBedrockFullAccess policy")
        
        # Add/Update ECR permissions (required for AgentCore to pull container images)
        ecr_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchCheckLayerAvailability"
                ],
                "Resource": "*"
            }]
        }
        
        try:
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="AgentCoreECRAccess",
                PolicyDocument=json.dumps(ecr_policy)
            )
            logger.info("Added ECR permissions to role")
        except Exception as e:
            logger.warning(f"Could not add ECR policy: {str(e)}")
        
        # Add Memory permissions
        memory_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:ListMemories",
                    "bedrock-agentcore:GetMemory",
                    "bedrock-agentcore:CreateMemory",
                    "bedrock-agentcore:UpdateMemory",
                    "bedrock-agentcore:DeleteMemory",
                    "bedrock-agentcore:ListEvents",
                    "bedrock-agentcore:GetEvent",
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:DeleteEvent"
                ],
                "Resource": "*"
            }]
        }
        
        try:
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="AgentCoreMemoryAccess",
                PolicyDocument=json.dumps(memory_policy)
            )
            logger.info("Added Memory permissions to role")
        except Exception as e:
            logger.warning(f"Could not add Memory policy: {str(e)}")
        
        # Add S3 permissions for campaign bucket access
        campaign_bucket = os.environ.get('CAMPAIGN_BUCKET', 'unified-campaign-review-test')
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket",
                    "s3:CreateBucket",
                    "s3:PutLifecycleConfiguration"
                ],
                "Resource": [
                    "arn:aws:s3:::bedrock-agentcore-*",
                    "arn:aws:s3:::bedrock-agentcore-*/*",
                    f"arn:aws:s3:::{campaign_bucket}",
                    f"arn:aws:s3:::{campaign_bucket}/*"
                ]
            }]
        }
        
        try:
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="AgentCoreS3Access",
                PolicyDocument=json.dumps(s3_policy)
            )
            logger.info(f"Added S3 permissions to role for bucket: {campaign_bucket}")
        except Exception as e:
            logger.warning(f"Could not add S3 policy: {str(e)}")
        
        # Add DynamoDB permissions for PersonaTable access
        dynamodb_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:BatchGetItem",
                    "dynamodb:BatchWriteItem",
                    "dynamodb:DescribeTable"
                ],
                "Resource": [
                    f"arn:aws:dynamodb:{region}:{account_id}:table/PersonaTable",
                    f"arn:aws:dynamodb:{region}:{account_id}:table/PersonaTable/*"
                ]
            }]
        }
        
        try:
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="AgentCoreDynamoDBAccess",
                PolicyDocument=json.dumps(dynamodb_policy)
            )
            logger.info("Added DynamoDB permissions to role")
        except Exception as e:
            logger.warning(f"Could not add DynamoDB policy: {str(e)}")
    
    # Wait for IAM to propagate
    logger.info("Waiting 10 seconds for IAM to propagate...")
    time.sleep(10)
    
    return role_arn


def ensure_s3_bucket(region, account_id):
    """
    Ensure S3 bucket exists for CodeBuild sources
    Based on deploy.sh create_s3_bucket function
    """
    logger.info("Ensuring S3 bucket exists...")
    
    s3_client = boto3.client('s3', region_name=region)
    bucket_name = f"bedrock-agentcore-codebuild-sources-{account_id}-{region}"
    
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"S3 Bucket exists: {bucket_name}")
    except:
        logger.info(f"Creating S3 Bucket: {bucket_name}")
        try:
            if region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            logger.info(f"Created S3 Bucket: {bucket_name}")
        except Exception as e:
            logger.warning(f"Could not create bucket: {str(e)}")
    
    return f"s3://{bucket_name}"


def configure_agent_runtime(agent_name, region, account_id):
    """
    Configure the Agent Core Runtime deployment
    """
    logger.info(f"Configuring Agent Core Runtime: {agent_name}")
    
    # Ensure IAM role and S3 bucket exist first
    role_arn = ensure_iam_role(region, account_id)
    s3_path = ensure_s3_bucket(region, account_id)
    
    # Change to /tmp directory (writable in Lambda)
    import os
    import shutil
    
    # Create working directory in /tmp
    work_dir = f"/tmp/agent-deploy-{agent_name}"
    os.makedirs(work_dir, exist_ok=True)
    
    # Copy agent files to /tmp
    shutil.copy("/var/task/agent.py", work_dir)
    shutil.copy("/var/task/requirements.txt", work_dir)
    shutil.copytree("/var/task/tools", f"{work_dir}/tools", dirs_exist_ok=True)
    shutil.copytree("/var/task/utils", f"{work_dir}/utils", dirs_exist_ok=True)
    
    # Change to working directory
    original_dir = os.getcwd()
    os.chdir(work_dir)
    
    try:
        agentcore_runtime = Runtime()
        
        response = agentcore_runtime.configure(
            entrypoint="agent.py",
            auto_create_execution_role=False,  # We created it manually
            execution_role=role_arn,  # Use the role we created
            auto_create_ecr=True,
            auto_create_s3=False,  # We created it manually
            s3_path=s3_path,  # Use the bucket we created
            requirements_file="requirements.txt",
            region=region,
            memory_mode='STM_ONLY',
            agent_name=agent_name
        )
        
        logger.info(f"Configuration complete: {response}")
        
        # Modify the generated Dockerfile to use opentelemetry-instrument
        dockerfile_path = os.path.join(work_dir, "Dockerfile")
        if os.path.exists(dockerfile_path):
            logger.info("Reading generated Dockerfile")
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
            
            # Print the original generated Dockerfile
            logger.info("=" * 80)
            logger.info("ORIGINAL GENERATED DOCKERFILE:")
            logger.info("=" * 80)
            logger.info(dockerfile_content)
            logger.info("=" * 80)
            
            # Replace the CMD line to use opentelemetry-instrument
            # The toolkit generates: CMD ["python", "agent.py"]
            # We want: CMD ["opentelemetry-instrument", "python", "agent.py"]
            modified_content = dockerfile_content.replace(
                'CMD ["python", "agent.py"]',
                'CMD ["opentelemetry-instrument", "python", "agent.py"]'
            )
            
            # Also handle if it's in a different format
            modified_content = modified_content.replace(
                'CMD python agent.py',
                'CMD opentelemetry-instrument python agent.py'
            )
            
            # Check if modification was made
            if modified_content != dockerfile_content:
                with open(dockerfile_path, 'w') as f:
                    f.write(modified_content)
                logger.info("Dockerfile modified successfully")
                logger.info("=" * 80)
                logger.info("MODIFIED DOCKERFILE:")
                logger.info("=" * 80)
                logger.info(modified_content)
                logger.info("=" * 80)
            else:
                logger.warning("No CMD line found to modify in Dockerfile")
        else:
            logger.warning(f"Dockerfile not found at {dockerfile_path}")


        
        return agentcore_runtime
    finally:
        # Change back to original directory
        os.chdir(original_dir)


def launch_agent_runtime(agentcore_runtime, auto_update=True):
    """
    Launch the agent to Agent Core Runtime
    """
    logger.info("Launching Agent to Agent Core Runtime")
    
    launch_result = agentcore_runtime.launch(auto_update_on_conflict=auto_update)
    
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
        
        # Get account ID
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        
        logger.info(f"Action: {action}, Agent: {agent_name}, Region: {region}, Account: {account_id}")
        
        # Handle different actions
        if action == 'deploy':
            # Deploy new agent
            agentcore_runtime = configure_agent_runtime(agent_name, region, account_id)
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
            
            # Write Agent ARN to SSM for ReviewCampaignFunction to read
            try:
                ssm_client = boto3.client('ssm', region_name=region)
                ssm_client.put_parameter(
                    Name='/agentcore/campaign-review/agent-arn',
                    Value=launch_result.agent_arn,
                    Type='String',
                    Overwrite=True
                )
                logger.info(f"Wrote Agent ARN to SSM: {launch_result.agent_arn}")
            except Exception as e:
                logger.warning(f"Failed to write Agent ARN to SSM: {e}")

            # Test invocation
            test_payload = body.get('test_payload', {
                'campaignId': '100',
                's3Key': 'campaign_brief.md',
                'bucket_name': 'genai-campaign-agentcore-unifiedbucket-h0hmnuit36hc'
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
