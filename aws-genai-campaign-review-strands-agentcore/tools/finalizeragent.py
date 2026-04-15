import os
import logging
from typing import Any, Dict
from datetime import datetime

from strands import Agent
from strands.models import BedrockModel
from strands import tool
from utils.s3 import read_text_from_s3, write_text_to_s3
from utils.persona_store import get_current_persona_id
from utils.payload_store import get_campaign_id, get_bucket_name

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@tool
def finalizer_agent(
    campaign_content: str,
    persona_review: str,
    validation_report: str,
    campaign_id: str = None,
    franchise: str = "EA Sports FC",
    franchise_type: str = "Sports",
    version: str = "v1"
) -> Dict[str, Any]:
    """
    Synthesize persona review and compliance validation into final recommendations.

    Args:
        campaign_content: The original campaign content
        persona_review: The persona-based review results
        validation_report: The compliance validation results
        franchise: Franchise name (e.g., "FIFA", "Madden")
        franchise_type: "Sports" or "Entertainment"
        version: Draft version (e.g., "v0", "v1")

    Returns:
        {
            "status": "success" | "error",
            "execution_summary": str,
            "final_report": str,
            "overall_recommendation": str,
            "priority_actions": list,
            "error": str  # Only present if status is "error"
        }
    """

    try:
        logger.info(f"=" * 80)
        logger.info(f"FINALIZER AGENT INVOKED")
        logger.info(f"Franchise: {franchise} ({franchise_type})")
        logger.info(f"Version: {version}")
        logger.info(f"=" * 80)

        # System prompt for synthesizing feedback
        system_prompt = f"""You are a Senior Marketing Strategy Finalizer for Electronic Arts (EA). Your role is to synthesize persona-based feedback and compliance validation into actionable final recommendations for ad campaign optimization.

# Your Expertise
You excel at:
- Balancing authentic audience connection with corporate compliance requirements
- Prioritizing feedback based on business impact and feasibility
- Creating clear, actionable recommendations for creative teams
- Identifying synergies between persona insights and brand guidelines
- Resolving conflicts between audience appeal and compliance constraints

# Synthesis Framework
Generate a finalized campaign content that updates the original campaign content with an analysis from the persona review and compliance validation with finalized generated content that:

**Balances Competing Priorities:**
- Audience authenticity vs. legal compliance
- Creative innovation vs. brand consistency  
- Cultural relevance vs. global scalability
- Engagement optimization vs. risk mitigation

**Prioritizes Actions:**
- Critical fixes that address both persona and compliance concerns
- High-impact improvements that enhance audience connection
- Compliance requirements that cannot be compromised
- Optional enhancements that could strengthen the campaign

**Provides Strategic Context:**
- How recommendations align with EA's broader marketing objectives
- Potential impact on campaign performance and brand perception
- Implementation complexity and resource requirements
- Success metrics and evaluation criteria

# Output Requirements
Provide your final campaign content in the following structured markdown format:

# Final Campaign Content

## Campaign Overview
- **Franchise**: {franchise} ({franchise_type})
- **Version**: {version}
- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Reviewer**: Senior Marketing Strategy Finalizer

## Executive Summary
Provide a 2-3 sentence overview of the campaign's current state and primary optimization opportunities.

## Overall Recommendation: [PROCEED/REVISE/REDESIGN]
- **PROCEED**: Campaign is ready with minor adjustments
- **REVISE**: Moderate changes needed before launch
- **REDESIGN**: Significant rework required

## Priority Action Items

### Critical (Must Address Before Launch)
List 2-4 critical actions that address both persona feedback and compliance requirements:
1. **[Action Title]**
   - **Issue**: [What needs to be fixed]
   - **Persona Impact**: [How this affects audience connection]
   - **Compliance Impact**: [Legal/brand implications]
   - **Recommended Solution**: [Specific action to take]
   - **Success Metric**: [How to measure improvement]

### High Impact (Strongly Recommended)
List 2-3 high-impact improvements that would significantly enhance campaign effectiveness:
1. **[Action Title]**
   - **Opportunity**: [What could be improved]
   - **Expected Benefit**: [Anticipated positive impact]
   - **Implementation**: [How to execute]
   - **Resource Requirement**: [Time/effort needed]

### Optional Enhancements (Consider If Resources Allow)
List 1-2 additional improvements that could further optimize the campaign:
1. **[Enhancement Title]**
   - **Potential Value**: [Why this could help]
   - **Implementation**: [How to execute]

## Persona-Compliance Alignment Analysis

### Areas of Synergy
Identify where persona feedback and compliance validation align:
- [Specific area where both reviews support the same direction]
- [How this alignment strengthens the recommendation]

### Areas of Tension
Identify where persona feedback conflicts with compliance requirements:
- [Specific conflict between audience appeal and compliance]
- [Recommended resolution approach]
- [Rationale for the chosen balance]

## Finalized Campaign Content

Generate an updated campaign that incorporates content from all sections above - Executive Summary, Priority Action Items and Persona-Compliance Alignment Analysis into the original content."""

        logger.info("Finalizer system prompt constructed successfully")

        # Create Bedrock model instance
        region=os.getenv("AWS_REGION", "us-west-2")
        #region = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-west-2"))
        model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        logger.info(f"Creating Bedrock model: {model_id}")
        
        try:
            bedrock_model = BedrockModel(
                model_id=model_id,
                region_name=region,
                temperature=0.4,  # Balanced temperature for strategic synthesis
                max_tokens=6144
            )
        except Exception as e:
            logger.error(f"Failed to create Bedrock model: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to initialize Bedrock model: {str(e)}",
                "execution_summary": "Failed to initialize AI model for synthesis"
            }

        # Create Agent with synthesis system prompt
        logger.info("Creating finalizer agent")
        try:
            finalizer_agent_instance = Agent(
                model=bedrock_model,
                system_prompt=system_prompt,
                tools=[]
            )
        except Exception as e:
            logger.error(f"Failed to create finalizer agent: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to create finalizer agent: {str(e)}",
                "execution_summary": "Failed to initialize finalizer agent"
            }

        # Invoke agent to generate final synthesis
        logger.info("Invoking agent to generate final synthesis")
        user_prompt = f"""Generate final campaign content that incorporates findings, actions and recommendations from the persona review and validation report in the original content:

<campaign_content>
{campaign_content}
</campaign_content>

<persona_review>
{persona_review}
</persona_review>

<validation_report>
{validation_report}
</validation_report>

Provide your comprehensive synthesis following the structured format specified in your instructions. Focus on updating the original content from the persona and validation reviews with the goal to balance audience authenticity with compliance requirements while maximizing campaign effectiveness for EA."""

        try:
            response = finalizer_agent_instance(user_prompt)
            
            # Handle different response formats
            if hasattr(response, 'content'):
                response_text = response.content
            elif hasattr(response, 'message'):
                response_text = response.message.get('content', [{}])[0].get('text', str(response.message))
            else:
                response_text = str(response)
            
            if not response_text:
                logger.error("No text content in model response")
                return {
                    "status": "error",
                    "error": "Synthesis failed: no content in model response",
                    "execution_summary": "Failed to generate final synthesis: no content returned"
                }
            
            logger.info(f"Final synthesis generated successfully ({len(response_text)} characters)")
            
        except Exception as e:
            logger.error(f"Bedrock model invocation failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Synthesis failed: {str(e)}",
                "execution_summary": f"Failed to generate final synthesis: {str(e)}"
            }

        # Retrieve persona_id from in-memory store
        #persona_id = get_persona_id()
        # Retrieve persona_id from in-memory store
        persona_id = get_current_persona_id()

        # Save final report to S3 if persona_id is available
        if persona_id:
            try:
                bucket_name = get_bucket_name()
                logger.info(f"Bucket name in finalizer: {bucket_name}")
                if bucket_name:
                    current_campaign_id = campaign_id or get_campaign_id()
                    if current_campaign_id:
                        final_s3_key = f"campaigns/{current_campaign_id}/reviews/{persona_id}/final_campaign.md"
                    else:
                        final_s3_key = f"final/{persona_id}/final_campaign.md"
                    logger.info(f"Saving final report to S3: {final_s3_key}")
                    
                    write_text_to_s3(
                        bucket_name=bucket_name,
                        key=final_s3_key,
                        text_content=response_text,
                        content_type="text/markdown"
                    )
                    logger.info(f"Successfully saved final report to S3")
                else:
                    logger.warning("CAMPAIGN_BUCKET environment variable not set, skipping S3 save")
            except Exception as e:
                logger.warning(f"Failed to save final report to S3: {str(e)}")
                # Don't fail the entire operation if S3 save fails

        # Parse response to extract key information
        overall_recommendation = "REVISE"  # Would be parsed from response in production
        priority_actions = [
            "Address persona feedback on cultural representation",
            "Resolve compliance issues with product claims",
            "Optimize messaging for target demographic"
        ]  # Would be parsed from response in production

        execution_summary = f"Completed campaign optimization synthesis for {franchise} {version}. Overall recommendation: {overall_recommendation}."
        
        logger.info(f"Finalizer agent completed successfully")
        
        return {
            "status": "success",
            "execution_summary": execution_summary,
            "final_report": response_text,
            "overall_recommendation": overall_recommendation,
            "priority_actions": priority_actions,
            "persona_id": persona_id,
        }

    except Exception as e:
        logger.error(f"Unexpected error in finalizer agent: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": f"Finalizer agent failed: {str(e)}",
            "execution_summary": f"Unexpected error during campaign finalization: {str(e)}",
        }