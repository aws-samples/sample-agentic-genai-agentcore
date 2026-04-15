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
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel
from tools.revieweragent import persona_reviewer_agent
from tools.validatoragent import validator_agent
from tools.finalizeragent import finalizer_agent
from utils.s3 import read_text_from_s3
from utils.payload_store import set_campaign_id, set_bucket_name

from tools.memory_client import get_memory_client, initialize_memory
from tools.memory_hooks import ShortTermMemoryHook

# Import Bedrock Agent Core Runtime
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Initialize the App
app = BedrockAgentCoreApp()

# Initialize memory
memory_client = get_memory_client()
memory_id = initialize_memory()

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

def create_campaign_orchestrator(trace_id: str = None, session_id: str = None, actor_id: str = None) -> Agent:
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
    
    # Create memory hook if memory is initialized
    hooks = []
    if memory_id:
        hooks.append(ShortTermMemoryHook(memory_client, memory_id))

    # Create orchestrator agent with all tools
    orchestrator = Agent(
        model=bedrock_model,
        system_prompt=CAMPAIGN_ORCHESTRATOR_PROMPT,
        tools=[persona_reviewer_agent, validator_agent, finalizer_agent],
        hooks=hooks,
        state={"actor_id": actor_id, "session_id": session_id}
    )
    
    return orchestrator

# Decorate the invocation function with @app.entrypoint
@app.entrypoint
def process_campaign_review(payload):
    """Bedrock Agent Core entrypoint for campaign review orchestration"""
    try:
   
        # Generate unique session_id for this campaign review
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"campaign-{timestamp}"

        # Extract parameters from agentcore invocation payload
        campaign_id = payload.get("campaignId", "100")
        s3_key = payload.get("s3Key", "campaign_brief.md")
        bucket_name = payload.get("bucket_name", "unified-campaign-review-test")
        
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
        
        # Async processing: do the actual work
        campaign_brief_s3_path = s3_key
        
        # Create orchestrator
        orchestrator = create_campaign_orchestrator(
            session_id=session_id,
            actor_id="campaign_user"
        )
        
        # Set the campaign ID and bucket name in the payload store for tools to use
        set_campaign_id(campaign_id)
        set_bucket_name(bucket_name)
        
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
        
        # Process the request synchronously
        logger.info("Starting campaign review orchestration")
        
        # Include campaign_id in the prompt so tools can use it
        prompt_with_campaign_id = f"CAMPAIGN_ID: {campaign_id}\n\n{campaign_prompt}"
        
        # Execute the orchestration
        response = orchestrator(prompt_with_campaign_id)
        
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
    app.run()
    