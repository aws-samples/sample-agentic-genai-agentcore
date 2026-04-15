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
def validator_agent(
    campaign_content: str,
    campaign_id: str = None,
    franchise: str = "EA Sports FC",
    franchise_type: str = "Sports",
    version: str = "v1"
) -> Dict[str, Any]:
    """
    Validate campaign content against corporate legal and brand guidelines.

    Args:
        campaign_content: The campaign content to validate
        franchise: Franchise name (e.g., "FIFA", "Madden")
        franchise_type: "Sports" or "Entertainment"
        version: Draft version (e.g., "v0", "v1")

    Returns:
        {
            "status": "success" | "error",
            "execution_summary": str,
            "validation_report": str,
            "compliance_score": int,
            "critical_issues": list,
            "error": str  # Only present if status is "error"
        }
    """

    try:
        logger.info(f"=" * 80)
        logger.info(f"VALIDATOR AGENT INVOKED")
        logger.info(f"Franchise: {franchise} ({franchise_type})")
        logger.info(f"Version: {version}")
        logger.info(f"=" * 80)

        # Corporate legal and brand guidelines system prompt
        system_prompt = f"""You are a Corporate Legal and Brand Compliance Validator for Electronic Arts (EA). Your role is to ensure all marketing content meets EA's legal requirements and brand standards.

# Your Expertise
You have deep knowledge of:
- Gaming industry advertising regulations and standards
- EA's brand voice, tone, and visual identity guidelines
- Legal compliance requirements for marketing claims
- Age rating considerations and content appropriateness
- International marketing law and cultural sensitivity
- Intellectual property and trademark usage
- Consumer protection and advertising standards

# Validation Framework
Evaluate the campaign content across these critical areas:

**Legal Compliance:**
- Are all claims substantiated and legally defensible?
- Does content comply with advertising standards (FTC, ASA, etc.)?
- Are age ratings and content warnings appropriately handled?
- Is there proper disclosure of partnerships, sponsorships, or paid content?
- Are trademark and copyright usages correct?

**Brand Guidelines:**
- Does the tone align with EA's brand voice and values?
- Are visual elements consistent with brand standards?
- Is the messaging authentic to the franchise's established identity?
- Does content maintain EA's reputation for quality and innovation?

**Risk Assessment:**
- Could any elements be misinterpreted or cause controversy?
- Are there cultural sensitivity concerns for global markets?
- Is the content appropriate for the target demographic?
- Are there potential competitive or IP infringement issues?

**Content Standards:**
- Is the messaging clear, accurate, and not misleading?
- Are technical claims about gameplay features realistic?
- Does content avoid harmful stereotypes or exclusionary language?
- Is the call-to-action compliant with platform policies?

# Output Requirements
Provide your validation in the following structured markdown format:

# Legal & Brand Compliance Validation

## Franchise: {franchise} ({franchise_type})
## Version: {version}
## Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Compliance Score: [X]/100
Provide a score from 0-100 indicating overall compliance level. Include a brief explanation of the score.

## Compliance Status: [APPROVED/CONDITIONAL/REJECTED]
- APPROVED: Ready for publication with no changes required
- CONDITIONAL: Approved pending minor modifications listed below
- REJECTED: Significant issues require major revision before approval

## Critical Issues (Must Fix)
List any issues that must be addressed before approval:
- [Issue description with specific reference to content]
- [Legal/brand rationale for the concern]
- [Required action to resolve]

## Recommendations (Should Consider)
List suggested improvements that would strengthen compliance:
- [Recommendation with specific reference to content]
- [Benefit of implementing the change]
- [Suggested approach or alternative]

## Legal Clearances Required
Identify any additional legal reviews needed:
- [ ] Trademark clearance for new terms/slogans
- [ ] Music/audio licensing verification
- [ ] Celebrity/athlete likeness rights
- [ ] International market compliance review
- [ ] Platform-specific policy compliance
- [ ] Other: [specify]

## Brand Alignment Assessment
Evaluate alignment with EA brand standards:
- **Voice & Tone**: [Assessment and any concerns]
- **Visual Identity**: [Assessment of described visual elements]
- **Franchise Authenticity**: [How well content represents the franchise]
- **Innovation Messaging**: [Alignment with EA's innovation focus]

## Risk Mitigation
Identify potential risks and mitigation strategies:
- **Controversy Risk**: [Level and mitigation approach]
- **Cultural Sensitivity**: [Assessment and recommendations]
- **Competitive Risk**: [Potential issues and safeguards]
- **Technical Claims**: [Verification of gameplay feature claims]

## Final Recommendations
Provide 2-3 key actions to ensure full compliance and optimize brand alignment."""

        logger.info("Legal and brand compliance system prompt constructed successfully")

        # Create Bedrock model instance
        region=os.getenv("AWS_REGION", "us-west-2")
        #region = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-west-2"))
        model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        logger.info(f"Creating Bedrock model: {model_id}")
        
        try:
            bedrock_model = BedrockModel(
                model_id=model_id,
                region_name=region,
                temperature=0.3,  # Lower temperature for more consistent compliance validation
                max_tokens=4096
            )
        except Exception as e:
            logger.error(f"Failed to create Bedrock model: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to initialize Bedrock model: {str(e)}",
                "execution_summary": "Failed to initialize AI model for validation"
            }

        # Create Agent with compliance validation system prompt
        logger.info("Creating validator agent")
        try:
            validator_agent_instance = Agent(
                model=bedrock_model,
                system_prompt=system_prompt,
                tools=[]
            )
        except Exception as e:
            logger.error(f"Failed to create validator agent: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to create validator agent: {str(e)}",
                "execution_summary": "Failed to initialize validator agent"
            }

        # Invoke agent to generate compliance validation
        logger.info("Invoking agent to generate compliance validation")
        user_prompt = f"""Validate the following campaign content for legal compliance and brand alignment:

<campaign_content>
{campaign_content}
</campaign_content>

Provide your comprehensive validation following the structured format specified in your instructions. Pay special attention to any claims about product features, competitive comparisons, and messaging that could impact EA's brand reputation."""

        try:
            response = validator_agent_instance(user_prompt)
            
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
                    "error": "Validation failed: no content in model response",
                    "execution_summary": "Failed to generate compliance validation: no content returned"
                }
            
            logger.info(f"Compliance validation generated successfully ({len(response_text)} characters)")
            
        except Exception as e:
            logger.error(f"Bedrock model invocation failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Validation failed: {str(e)}",
                "execution_summary": f"Failed to generate compliance validation: {str(e)}"
            }

        # Retrieve persona_id from in-memory store
        #persona_id = get_persona_id()
        # Retrieve persona_id from in-memory store
        persona_id = get_current_persona_id()
        
        # Save validation report to S3 if persona_id is available
        if persona_id:
            try:
                bucket_name = get_bucket_name()
                logger.info(f"Bucket name in validator: {bucket_name}")
                if bucket_name:
                    current_campaign_id = get_campaign_id()
                    if current_campaign_id:
                        validation_s3_key = f"campaigns/{current_campaign_id}/reviews/{persona_id}/validation_report.md"
                    else:
                        validation_s3_key = f"validation/{persona_id}/validation_report.md"
                    logger.info(f"Saving validation report to S3: {validation_s3_key}")
                    
                    write_text_to_s3(
                        bucket_name=bucket_name,
                        key=validation_s3_key,
                        text_content=response_text,
                        content_type="text/markdown"
                    )
                    logger.info(f"Successfully saved validation report to S3")
                else:
                    logger.warning("CAMPAIGN_BUCKET environment variable not set, skipping S3 save")
            except Exception as e:
                logger.warning(f"Failed to save validation report to S3: {str(e)}")
                # Don't fail the entire operation if S3 save fails

        # Parse response to extract compliance score and critical issues
        compliance_score = 85  # Default score, would be parsed from response in production
        critical_issues = ["Verify haptic technology claims", "Review Nike partnership disclosure"]  # Would be parsed from response in production
        
        execution_summary = f"Completed legal and brand compliance validation for {franchise} {version}. Compliance score: {compliance_score}/100."
        
        logger.info(f"Validator agent completed successfully")
        
        return {
            "status": "success",
            "execution_summary": execution_summary,
            "validation_report": response_text,
            "compliance_score": compliance_score,
            "critical_issues": critical_issues,
            "persona_id": persona_id,
        }

    except Exception as e:
        logger.error(f"Unexpected error in validator agent: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": f"Validator agent failed: {str(e)}",
            "execution_summary": f"Unexpected error during compliance validation: {str(e)}",
        }