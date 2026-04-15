#!/usr/bin/env python3
"""
# 🎯 Ad Campaign Review Orchestrator Agent

A LangGraph-based orchestrator that coordinates persona-based review, compliance validation, 
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
from typing import Annotated, TypedDict, Sequence

from utils.s3 import read_text_from_s3, write_text_to_s3

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain_aws import ChatBedrock
from opentelemetry import baggage 
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.instrumentation import auto_instrumentation
from datetime import datetime

# Get tracer lazily (after auto_instrumentation.initialize() runs)
_tracer = None
def get_tracer():
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("campaign-review-orchestrator")
    return _tracer

# Import the agent functions
from tools.revieweragent import persona_reviewer_agent
from tools.validatoragent import validator_agent
from tools.finalizeragent import finalizer_agent

# Import memory components
from langgraph_hooks import MemoryHook, HookManager, create_hooked_node

# Import LangGraph hooks
from langgraph_hooks import (
    HookManager,
    LoggingHook,
    MemoryHook,
    MetricsHook,
    create_hooked_node
)


# Global variable to store current campaign_id for tools
_current_campaign_id = None
_instrumentation_initialized = False

def set_current_campaign_id(campaign_id: str):
    """Set the current campaign ID for use by agent tools"""
    global _current_campaign_id
    _current_campaign_id = campaign_id

def get_current_campaign_id() -> str:
    """Get the current campaign ID"""
    global _current_campaign_id
    return _current_campaign_id

def set_session_context(session_id: str):
    """Set session context for OpenTelemetry"""
    ctx = baggage.set_baggage("session.id", session_id)
    return otel_context.attach(ctx)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
LOGGER = logger  # Alias for consistency

# Define the state for the LangGraph workflow
class CampaignState(TypedDict):
    """State for the campaign review workflow"""
    campaign_content: str
    campaign_id: str
    franchise: str
    franchise_type: str
    version: str
    persona_review: str
    validation_report: str
    final_report: str
    messages: Sequence[BaseMessage]
    error: str

# Define the orchestrator system prompt for ad campaign review
CAMPAIGN_ORCHESTRATOR_PROMPT = """
You are the EA Campaign Review Orchestrator, responsible for coordinating comprehensive review of advertising campaigns for Electronic Arts gaming franchises. Your role is to manage the end-to-end review process that ensures campaigns are both authentic to target audiences and compliant with corporate standards.

# Your Mission
Orchestrate a multi-stage review process for ad campaigns that:
1. Evaluates content from diverse human perspectives (persona-based review)
2. Validates legal compliance and brand guideline adherence
3. Synthesizes feedback into actionable optimization recommendations

# Orchestration Protocol

The workflow follows this sequence:

1. **Initiate Persona Review**
   - Review campaign content from authentic human persona perspectives
   - Capture persona insights and demographic feedback
   - Note any cultural or representation concerns

2. **Conduct Compliance Validation**
   - Validate legal and brand guideline compliance
   - Identify legal and brand guideline issues
   - Document compliance score and critical fixes needed

3. **Synthesize Final Recommendations**
   - Combine original content, persona review, and validation results
   - Summarize key findings from the persona review and the validation 
   - Highlight critical actions and recommendations
   - Generate final campaign content that incorporates these findings

# Campaign Context
You are currently reviewing ad campaigns for EA's gaming franchises, with a focus on new sneaker product launches that require authentic audience connection while maintaining EA's brand standards and legal compliance.

# Response Format
Always provide:
- Executive summary of review findings
- Key insights from persona and compliance perspectives
- Priority recommendations with clear rationale
- Implementation guidance and success metrics

Remember: Your goal is to ensure campaigns resonate authentically with target audiences while meeting all corporate standards and legal requirements."""

# Define workflow nodes
def persona_review_node(state: CampaignState) -> CampaignState:
    """Node that performs persona-based review"""
    with get_tracer().start_as_current_span("persona_review_node", attributes={
        "node.type": "persona_review",
        "campaign.id": state.get("campaign_id", ""),
    }):
        logger.info("Executing persona review node")
        
        result = persona_reviewer_agent(
            campaign_content=state["campaign_content"],
            campaign_id=state.get("campaign_id"),
            franchise=state.get("franchise", "EA Sports FC"),
            franchise_type=state.get("franchise_type", "Sports"),
            version=state.get("version", "v1")
        )
        
        if result["status"] == "success":
            state["persona_review"] = result["persona_review"]
            state["messages"].append(AIMessage(content=f"Persona review completed: {result['execution_summary']}"))
        else:
            state["error"] = result.get("error", "Persona review failed")
            state["messages"].append(AIMessage(content=f"Persona review failed: {state['error']}"))
        
        return state

def validation_node(state: CampaignState) -> CampaignState:
    """Node that performs compliance validation"""
    with get_tracer().start_as_current_span("validation_node", attributes={
        "node.type": "validation",
        "campaign.id": state.get("campaign_id", ""),
    }):
        logger.info("Executing validation node")
        
        result = validator_agent(
            campaign_content=state["campaign_content"],
            campaign_id=state.get("campaign_id"),
            franchise=state.get("franchise", "EA Sports FC"),
            franchise_type=state.get("franchise_type", "Sports"),
            version=state.get("version", "v1")
        )
        
        if result["status"] == "success":
            state["validation_report"] = result["validation_report"]
            state["messages"].append(AIMessage(content=f"Validation completed: {result['execution_summary']}"))
        else:
            state["error"] = result.get("error", "Validation failed")
            state["messages"].append(AIMessage(content=f"Validation failed: {state['error']}"))
        
        return state

def finalizer_node(state: CampaignState) -> CampaignState:
    """Node that synthesizes final recommendations"""
    with get_tracer().start_as_current_span("finalizer_node", attributes={
        "node.type": "finalizer",
        "campaign.id": state.get("campaign_id", ""),
    }):
        logger.info("Executing finalizer node")
        
        # Check if we have the required inputs
        if not state.get("persona_review") or not state.get("validation_report"):
            state["error"] = "Missing persona review or validation report"
            state["messages"].append(AIMessage(content=f"Finalization failed: {state['error']}"))
            return state
        
        result = finalizer_agent(
            campaign_content=state["campaign_content"],
            persona_review=state["persona_review"],
            validation_report=state["validation_report"],
            campaign_id=state.get("campaign_id"),
            franchise=state.get("franchise", "EA Sports FC"),
            franchise_type=state.get("franchise_type", "Sports"),
            version=state.get("version", "v1")
        )
        
        if result["status"] == "success":
            state["final_report"] = result["final_report"]
            state["messages"].append(AIMessage(content=f"Finalization completed: {result['execution_summary']}"))
        else:
            state["error"] = result.get("error", "Finalization failed")
            state["messages"].append(AIMessage(content=f"Finalization failed: {state['error']}"))
        
        return state

def should_continue(state: CampaignState) -> str:
    """Determine if workflow should continue or end"""
    if state.get("error"):
        return END
    
    # Check which stage we're at based on what's been completed
    if not state.get("persona_review"):
        return "persona_review"
    elif not state.get("validation_report"):
        return "validation"
    elif not state.get("final_report"):
        return "finalizer"
    else:
        return END

def create_campaign_orchestrator(
    session_id: str,
    actor_id: str = "campaign_user",
    memory_client=None,
    memory_id: str = None
) -> tuple:
    """
    Create the campaign review orchestrator workflow using LangGraph
    
    Args:
        session_id: Unique session identifier
        actor_id: User/actor identifier
        memory_client: Optional AWS Bedrock AgentCore Memory client
        memory_id: Optional memory store identifier
    
    Returns:
        Tuple of (compiled_workflow, hook_manager)
    """
    
    # Create hook manager
    hook_manager = HookManager()
    
    # Add memory hook if memory is configured
    if memory_client and memory_id:
        logger.info(f"[{session_id}] Enabling AgentCore Memory integration")
        hook_manager.add_hook(MemoryHook(
            memory_client=memory_client,
            memory_id=memory_id,
            session_id=session_id
        ))
    else:
        logger.info(f"[{session_id}] Running without AgentCore Memory")
    
    # Create the workflow graph
    workflow = StateGraph(CampaignState)
    
    # Wrap nodes with hooks
    hooked_persona_review = create_hooked_node(
        persona_review_node, "persona_review", hook_manager
    )
    hooked_validation = create_hooked_node(
        validation_node, "validation", hook_manager
    )
    hooked_finalizer = create_hooked_node(
        finalizer_node, "finalizer", hook_manager
    )
    
    # Add hooked nodes to workflow
    workflow.add_node("persona_review", hooked_persona_review)
    workflow.add_node("validation", hooked_validation)
    workflow.add_node("finalizer", hooked_finalizer)
    
    # Define the workflow edges
    workflow.set_entry_point("persona_review")
    workflow.add_edge("persona_review", "validation")
    workflow.add_edge("validation", "finalizer")
    workflow.add_edge("finalizer", END)
    
    # Compile the workflow
    app = workflow.compile()
    
    return app, hook_manager

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
        
        # Initialize OTEL auto-instrumentation (once per cold start)
        global _instrumentation_initialized
        if not _instrumentation_initialized:
            auto_instrumentation.initialize()
            logger.info("Auto instrumentation initialized")
            _instrumentation_initialized = True
    
        # Generate unique session_id for this campaign review
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"campaign-{timestamp}"

        context_token = set_session_context(session_id)
        
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
        with get_tracer().start_as_current_span("campaign_review_workflow", attributes={
            "campaign.id": campaign_id,
            "session.id": session_id,
        }) as parent_span:
            campaign_brief_s3_path = s3_key
            
            # Initialize memory if available (optional)
            memory_client = None
            memory_id = None
            try:
                from tools.memory_client import get_memory_client, initialize_memory
                memory_client = get_memory_client()
                memory_id = initialize_memory()
                logger.info(f"[{session_id}] AgentCore Memory initialized: {memory_id}")
            except ImportError:
                logger.info(f"[{session_id}] AgentCore Memory not available (optional)")
            except Exception as e:
                logger.warning(f"[{session_id}] Failed to initialize memory: {e}")
            
            orchestrator, hook_manager = create_campaign_orchestrator(
                session_id=session_id,
                actor_id="campaign_user",
                memory_client=memory_client,
                memory_id=memory_id
            )
            
            set_current_campaign_id(campaign_id)
            
            status_key = f"campaigns/{campaign_id}/status.json"
            status_data = {
                "status": "processing",
                "stage": "reading_brief",
                "timestamp": context.aws_request_id if context else "local",
                "campaign_id": campaign_id
            }
            write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
            
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
            
            status_data["stage"] = "generating_reviews"
            write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
            
            logger.info("Starting campaign review orchestration")
            
            initial_state = {
                "campaign_content": campaign_prompt,
                "campaign_id": campaign_id,
                "franchise": "EA Sports FC",
                "franchise_type": "Sports",
                "version": "v1",
                "persona_review": "",
                "validation_report": "",
                "final_report": "",
                "messages": [HumanMessage(content=f"Review campaign for {campaign_id}")],
                "error": ""
            }
            
            hook_manager.on_workflow_start(initial_state)
            
            try:
                final_state = orchestrator.invoke(initial_state)
                hook_manager.on_workflow_end(final_state)
            except Exception as e:
                hook_manager.on_error(e, initial_state)
                raise
            
            status_data["stage"] = "complete"
            status_data["status"] = "completed"
            write_text_to_s3(bucket_name, status_key, json.dumps(status_data))
            
            logger.info("Campaign review orchestration completed successfully")
            
            if final_state.get("error"):
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Campaign review failed: {final_state["error"]}',
                        'status': 'failed',
                        'campaign_id': campaign_id
                    })
                }
            
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
                    'results': final_state.get("final_report", ""),
                    'persona_review': final_state.get("persona_review", ""),
                    'validation_report': final_state.get("validation_report", "")
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
    finally:
        if context_token:
            otel_context.detach(context_token)
            LOGGER.info(f"Session context detached")

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