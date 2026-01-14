#!/usr/bin/env python3
"""
# 🎯 Ad Campaign Review Orchestrator Agent

A specialized Strands agent that orchestrates persona-based review, compliance validation, 
and final synthesis for EA ad campaigns.

## What This Example Shows
This orchestrator coordinates three specialized agents:
1. Reviewer Agent: Provides persona-based feedback on campaign content
2. Validator Agent: Ensures legal compliance and brand guideline adherence  
3. Finalizer Agent: Synthesizes feedback into actionable recommendations

"""

import os
import json
import logging
import boto3
from strands import Agent
from strands.models import BedrockModel
from tools.revieweragent import persona_reviewer_agent
from tools.validatoragent import validator_agent
from tools.finalizeragent import finalizer_agent
from utils.s3 import read_text_from_s3, write_text_to_s3

# Global variable to store current campaign_id for tools
_current_campaign_id = None

def set_current_campaign_id(campaign_id: str):
    """Set the current campaign ID for use by agent tools"""
    global _current_campaign_id
    _current_campaign_id = campaign_id

def get_current_campaign_id() -> str:
    """Get the current campaign ID"""
    global _current_campaign_id
    return _current_campaign_id

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Force rebuild timestamp: 2026-01-11 22:15

# Define the orchestrator system prompt for ad campaign review
CAMPAIGN_ORCHESTRATOR_PROMPT = """
You are the EA Campaign Review Orchestrator, responsible for coordinating comprehensive review of advertising campaigns for Electronic Arts gaming franchises. Your role is to manage the end-to-end review process that ensures campaigns are both authentic to target audiences and compliant with corporate standards.

# Your Mission
Orchestrate a multi-stage review process for ad campaigns that:
1. Evaluates content from diverse human perspectives (persona-based review)
2. Validates legal compliance and brand guideline adherence
3. Synthesizes feedback into actionable optimization recommendations

# Available Tools
You have access to three specialized agents:

**persona_reviewer_agent**: Reviews content from authentic human persona perspectives
- Provides demographic-specific feedback on cultural relevance and authenticity
- Evaluates emotional connection and representation quality
- Identifies potential alienation or engagement opportunities
- Returns persona details, review content, and resonance scoring

**validator_agent**: Validates legal compliance and brand guidelines
- Ensures adherence to advertising standards and regulations
- Validates brand voice, tone, and visual identity alignment
- Assesses risk factors and competitive considerations
- Returns compliance scoring and critical issue identification

**finalizer_agent**: Synthesizes all feedback into final recommendations
- Balances persona insights with compliance requirements
- Prioritizes actions based on business impact and feasibility
- Creates implementation roadmap with success metrics
- Returns overall recommendation and priority action items

# Orchestration Protocol

When reviewing an ad campaign, follow this sequence:

1. **Initiate Persona Review**
   - Call persona_reviewer_agent with campaign content
   - Capture persona insights and demographic feedback
   - Note any cultural or representation concerns

2. **Conduct Compliance Validation**
   - Call validator_agent with same campaign content
   - Identify legal and brand guideline issues
   - Document compliance score and critical fixes needed

3. **Synthesize Final Recommendations**
   - Call finalizer_agent with original content, persona review, and validation results
   - Summarize key findings from the persona review and the validation 
   - Highlight critical actions and recommendations
   - Generate final campaign content that incorporates these findings, actions and recommendations in the original content


# Campaign Context
You are currently reviewing ad campaigns for EA's gaming franchises, with a focus on new sneaker product launches that require authentic audience connection while maintaining EA's brand standards and legal compliance.

# Response Format
Always provide:
- Executive summary of review findings
- Key insights from persona and compliance perspectives
- Priority recommendations with clear rationale
- Implementation guidance and success metrics

Remember: Your goal is to ensure campaigns resonate authentically with target audiences while meeting all corporate standards and legal requirements."""

def create_campaign_orchestrator() -> Agent:
    """Create the campaign review orchestrator agent"""
    
    # Create Bedrock model for orchestrator
    region=os.getenv("AWS_REGION", "us-west-2")
    #region = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-west-2"))
    model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    
    bedrock_model = BedrockModel(
        model_id=model_id,
        region_name=region,
        temperature=0.5,
        max_tokens=4096
    )
    
    # Create orchestrator agent with all tools
    orchestrator = Agent(
        model=bedrock_model,
        system_prompt=CAMPAIGN_ORCHESTRATOR_PROMPT,
        tools=[persona_reviewer_agent, validator_agent, finalizer_agent],
    )
    
    return orchestrator

# Example usage and Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler for campaign review orchestration"""
    try:
        # Log the incoming event for debugging
        logger.info(f"Received event: {event}")
        
        # Handle CORS preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token',
                    'Access-Control-Max-Age': '86400'
                },
                'body': ''
            }
        
        # Handle API Gateway event structure
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Check if this is an async processing request (internal invocation)
        is_async_processing = body.get('_async_processing', False)
            
        # Extract parameters from event body - now requires campaignId and s3Key
        campaign_id = body.get('campaignId')
        s3_key = body.get('s3Key')
        
        if not campaign_id or not s3_key:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters: campaignId and s3Key'
                })
            }

        bucket_name = os.environ.get("CAMPAIGN_BUCKET")
        
        # If not async processing, invoke self asynchronously and return immediately
        if not is_async_processing:
            lambda_client = boto3.client('lambda')
            async_payload = {
                'campaignId': campaign_id,
                's3Key': s3_key,
                '_async_processing': True
            }
            lambda_client.invoke(
                FunctionName=context.function_name,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(async_payload)
            )
            
            # Write initial status
            status_key = f"campaigns/{campaign_id}/status.json"
            status_data = {
                "status": "processing",
                "stage": "queued",
                "campaign_id": campaign_id
            }
            write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
            
            return {
                'statusCode': 202,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Campaign review started',
                    'status': 'processing',
                    'campaign_id': campaign_id
                })
            }
        
        # Async processing: do the actual work
        campaign_brief_s3_path = s3_key
        
        # Create orchestrator
        orchestrator = create_campaign_orchestrator()
        
        # Set the current campaign ID for tools to use
        set_current_campaign_id(campaign_id)
        
        # Write status: processing
        status_key = f"campaigns/{campaign_id}/status.json"
        status_data = {
            "status": "processing",
            "stage": "reading_brief",
            "timestamp": context.aws_request_id if context else "local",
            "campaign_id": campaign_id
        }
        write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
        
        # Read content brief from S3
        logger.info(f"Reading campaign brief from S3: {campaign_brief_s3_path}")
        try:
            campaign_prompt = read_text_from_s3(bucket_name=bucket_name, key=campaign_brief_s3_path)
            logger.info(f"Successfully read content brief ({len(campaign_prompt)} characters)")
        except FileNotFoundError as e:
            logger.error(f"Content brief not found at S3 path: {campaign_brief_s3_path}")
            return {
                "status": "error",
                "error": f"Content brief not found at {campaign_brief_s3_path}",
            }
        except PermissionError as e:
            logger.error(f"Access denied reading content brief from S3: {str(e)}")
            return {
                "status": "error",
                "error": f"Access denied reading content brief from S3",
            }
        except Exception as e:
            logger.error(f"Failed to read content brief from S3: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to read content brief: {str(e)}",
            }
        
        # Update status: generating reviews
        status_data["stage"] = "generating_reviews"
        write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
        
        # Process the request synchronously
        logger.info("Starting campaign review orchestration")
        
        # Include campaign_id in the prompt so tools can use it
        prompt_with_campaign_id = f"CAMPAIGN_ID: {campaign_id}\n\n{campaign_prompt}"
        
        # Execute the orchestration
        response = orchestrator(prompt_with_campaign_id)
        
        # Update status: complete
        status_data["stage"] = "complete"
        status_data["status"] = "completed"
        write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
        
        logger.info("Campaign review orchestration completed successfully")
        
        # Return the orchestration results
        
        # Extract response content based on Strands response structure
        if hasattr(response, 'content'):
            response_content = response.content
        elif hasattr(response, 'message'):
            response_content = response.message.get('content', [{}])[0].get('text', str(response.message))
        else:
            response_content = str(response)
            
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Campaign review completed successfully',
                'status': 'completed',
                'campaign_id': campaign_id,
                'results': response_content,
                'usage': {
                    'input_tokens': getattr(response, 'input_tokens', 0) if hasattr(response, 'usage') else 0,
                    'output_tokens': getattr(response, 'output_tokens', 0) if hasattr(response, 'usage') else 0
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Campaign review orchestration failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Campaign review failed: {str(e)}',
                'type': type(e).__name__
            })
        }

if __name__ == "__main__":
    print("\n🎯 EA Campaign Review Orchestrator 🎯\n")
    print("Orchestrating comprehensive ad campaign review...")
    print("This will coordinate persona feedback, compliance validation, and final synthesis.")
    
    # Demo execution
    demo_event = {
        'franchise': 'EA Sports FC',
        'franchise_type': 'Sports',
        'version': 'v1'
    }
    
    try:
        result = lambda_handler(demo_event, None)
        print(f"\nDemo Result: {result}")
    except Exception as e:
        print(f"\nDemo failed: {str(e)}")
        print("Note: This demo requires proper AWS credentials and S3/DynamoDB setup.")