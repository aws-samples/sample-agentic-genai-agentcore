import os
import logging
import random
from typing import Any, Dict
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from strands import Agent
from strands.models.openai import OpenAIModel
from strands import tool
from utils.s3 import read_text_from_s3, write_text_to_s3
from utils.persona_store import set_current_persona_id

def get_current_campaign_id():
    """Get the current campaign ID from orchestrator"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        # Import using importlib to avoid lambda keyword conflict
        import importlib.util
        spec = importlib.util.spec_from_file_location("orchestrator", os.path.join(os.path.dirname(os.path.dirname(__file__)), "lambda", "orchestrator.py"))
        orchestrator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orchestrator_module)
        return orchestrator_module.get_current_campaign_id()
    except:
        return None

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@tool
def persona_reviewer_agent(
    campaign_content: str,
    campaign_id: str = None,
    franchise: str = "EA Sports FC",
    franchise_type: str = "Sports",
    version: str = "v1"
) -> Dict[str, Any]:
    """
    Review campaign content from a diverse human persona perspective.

    Args:
        campaign_content: The campaign content to review
        franchise: Franchise name (e.g., "FIFA", "Madden")
        franchise_type: "Sports" or "Entertainment"
        version: Draft version (e.g., "v0", "v1")

    Returns:
        {
            "status": "success" | "error",
            "execution_summary": str,
            "persona_review": str,
            "persona_details": dict,
            "resonance_score": int,
            "error": str  # Only present if status is "error"
        }
    """

    try:
        logger.info(f"=" * 80)
        logger.info(f"PERSONA REVIEWER AGENT INVOKED")
        logger.info(f"Franchise: {franchise} ({franchise_type})")
        logger.info(f"Version: {version}")
        logger.info(f"=" * 80)

        # Query DynamoDB to retrieve a random persona record
        try:
            # Initialize DynamoDB client
            region = os.getenv("AWS_REGION", "us-west-2")
            bucket_name = os.environ.get("CAMPAIGN_BUCKET")
            dynamodb = boto3.client('dynamodb', region_name=region)
            
            # Generate a random persona_id between 001 and 040
            random_id = random.randint(1, 40)
            persona_id = f"persona_{random_id:03d}"
            
            # Store persona_id in memory for other agents to access
            set_current_persona_id(persona_id)
            
            logger.info(f"Querying DynamoDB for persona: {persona_id}")
            
            # Query DynamoDB for the specific persona
            response = dynamodb.get_item(
                TableName='PersonaTable',
                Key={
                    'persona_id': {'S': persona_id}
                }
            )
            
            if 'Item' not in response:
                logger.warning(f"Persona {persona_id} not found in DynamoDB, using fallback")
                # Fallback persona if DynamoDB query fails
                persona = {
                    "persona_id": "persona_fallback",
                    "age": 28,
                    "gender": "Female",
                    "ethnicity": "Hispanic",
                    "national_origin": "Mexico",
                    "country_of_residence": "USA",
                    "income_level": "Medium",
                    "profession": "Software Developer"
                }
            else:
                # Parse DynamoDB response and populate persona struct
                item = response['Item']
                persona = {
                    "persona_id": item['persona_id']['S'],
                    "age": int(item['age']['N']),
                    "gender": item['gender']['S'],
                    "ethnicity": item['ethnicity']['S'],
                    "national_origin": item['national_origin']['S'],
                    "country_of_residence": item['country_of_residence']['S'],
                    "income_level": item['income_level']['S'],
                    "profession": item['profession']['S']
                }
                logger.info(f"Successfully retrieved persona: {persona['persona_id']}")
                
        except ClientError as e:
            logger.error(f"DynamoDB query failed: {str(e)}")
            # Fallback persona if DynamoDB is unavailable
            persona = {
                "persona_id": "persona_fallback",
                "age": 28,
                "gender": "Female",
                "ethnicity": "Hispanic",
                "national_origin": "Mexico",
                "country_of_residence": "USA",
                "income_level": "Medium",
                "profession": "Software Developer"
            }
        except Exception as e:
            logger.error(f"Unexpected error querying DynamoDB: {str(e)}")
            # Fallback persona for any other errors
            persona = {
                "persona_id": "persona_fallback",
                "age": 28,
                "gender": "Female",
                "ethnicity": "Hispanic",
                "national_origin": "Mexico",
                "country_of_residence": "USA",
                "income_level": "Medium",
                "profession": "Software Developer"
            }
        
        age = persona["age"]
        gender = persona["gender"]
        ethnicity = persona["ethnicity"]
        national_origin = persona["national_origin"]
        country_of_residence = persona["country_of_residence"]
        income_level = persona["income_level"]
        profession = persona["profession"]

        logger.info(f"Using persona: {age}yo {gender} {profession} from {national_origin}")

        # Construct persona-based system prompt
        system_prompt = f"""You are reviewing content as a {age}-year-old {gender} {profession} from {national_origin}, currently living in {country_of_residence}. Your ethnicity is {ethnicity} and your income level is {income_level}.

# Your Role
Evaluate the campaign content from YOUR authentic perspective as this specific person. You are not an external reviewer - you ARE this persona. Think about how this content would land with someone who has your exact demographic profile, cultural background, life experiences, and worldview.

# Evaluation Framework
When reviewing the content, deeply consider:

**Cultural & Demographic Relevance:**
- Does this content acknowledge or reflect your cultural background and identity?
- Are there cultural references, imagery, or language that resonate with or alienate someone from your background?
- Does the content make assumptions about your demographic that feel accurate or stereotypical?

**Lifestyle & Economic Factors:**
- Given your profession ({profession}) and income level ({income_level}), is this content relevant to your daily life?
- Are the products, services, or experiences featured accessible and appealing to someone in your economic situation?
- Does the content understand the priorities and concerns of someone with your lifestyle?

**Authenticity & Representation:**
- If this content features people, do you see yourself represented authentically?
- Does the messaging feel like it was created WITH your demographic in mind, or just targeted AT you?
- Are there elements that feel tone-deaf or disconnected from your lived experience?

**Emotional & Personal Connection:**
- What specific elements make you feel seen, understood, or valued?
- What elements make you feel excluded, misunderstood, or stereotyped?
- Would you share this content with others in your community? Why or why not?

# Output Requirements
Provide your review in the following structured markdown format. Be specific, honest, and authentic in your feedback:

# Persona-Based Review

## Persona Profile
- Age: {age}
- Gender: {gender}
- Ethnicity: {ethnicity}
- National Origin: {national_origin}
- Country of Residence: {country_of_residence}
- Income Level: {income_level}
- Profession: {profession}

## Content Resonance Score: [X]/10
Provide a score from 1-10 indicating how well this content resonates with you as this persona. Include a brief 1-2 sentence explanation of your score.

## What Resonates
Identify 2-3 specific elements that appeal to you as this persona. For each element:
- Quote or reference the specific content element
- Explain WHY it resonates from your demographic perspective
- Describe the emotional or practical connection it creates

## Concerns & Gaps
Identify 2-3 specific elements that may not resonate or could be problematic for you as this persona. For each concern:
- Quote or reference the specific content element
- Explain WHY it doesn't work from your demographic perspective
- Describe potential negative reactions or missed opportunities

## Recommendations
Provide 2-3 specific, actionable suggestions for improving the content's appeal to your demographic. Each recommendation should:
- Address a specific gap or concern identified above
- Suggest concrete changes to messaging, imagery, tone, or approach
- Explain how the change would better connect with someone like you

Remember: You are providing authentic feedback as this persona would experience the content. Be honest about what works and what doesn't from your unique demographic perspective."""

        logger.info("Persona-based system prompt constructed successfully")

        # Create OpenAI-compatible model instance
        logger.info("Creating OpenAI-compatible model: openai/gpt-oss-120b")
        
        try:
            openai_model = OpenAIModel(
                client_args={
                    "base_url": os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1"),
                    "api_key": os.getenv("OPENAI_API_KEY"),
                },
                model_id="openai/gpt-oss-120b",
                params={
                    "max_tokens": 4096,
                    "temperature": 0.7,
                },
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI model: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to initialize OpenAI model: {str(e)}",
                "execution_summary": "Failed to initialize AI model for review generation",
                "persona_details": persona,
            }

        # Create Agent with persona-based system prompt
        logger.info("Creating persona reviewer agent")
        try:
            persona_agent = Agent(
                model=openai_model,
                system_prompt=system_prompt,
                tools=[]
            )
        except Exception as e:
            logger.error(f"Failed to create persona agent: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to create persona agent: {str(e)}",
                "execution_summary": "Failed to initialize persona reviewer agent",
                "persona_details": persona,
            }

        # Invoke agent to generate persona-based review
        logger.info("Invoking agent to generate persona-based review")
        user_prompt = f"""Review the following campaign content from your perspective as the persona described above:

<campaign_content>
{campaign_content}
</campaign_content>

Provide your honest, authentic feedback following the structured format specified in your instructions."""

        try:
            response = persona_agent(user_prompt)
            
            # Handle different response formats - filter out reasoningContent
            if hasattr(response, 'message') and isinstance(response.message.get('content'), list):
                response_text = ''.join(
                    block.get('text', '') for block in response.message['content'] if 'text' in block
                )
            elif hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            if not response_text:
                logger.error("No text content in model response")
                return {
                    "status": "error",
                    "error": "Review generation failed: no content in model response",
                    "execution_summary": "Failed to generate persona review: no content returned",
                    "persona_details": persona,
                }
            
            logger.info(f"Persona review generated successfully ({len(response_text)} characters)")
            
        except Exception as e:
            logger.error(f"Bedrock model invocation failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Review generation failed: {str(e)}",
                "execution_summary": f"Failed to generate persona review: {str(e)}",
                "persona_details": persona,
            }

        # Save review to S3 at campaigns/{campaign_id}/reviews/{persona_id}/campaign_review.md
        current_campaign_id = campaign_id or get_current_campaign_id()
        if current_campaign_id:
            review_s3_key = f"campaigns/{current_campaign_id}/reviews/{persona['persona_id']}/campaign_review.md"
        else:
            review_s3_key = f"review/{persona['persona_id']}/campaign_review.md"
        logger.info(f"Saving persona review to S3: {review_s3_key}")
        
        try:
            write_text_to_s3(
                bucket_name=bucket_name,
                key=review_s3_key,
                text_content=response_text,
                content_type="text/markdown"
            )
            logger.info(f"Successfully saved persona review to S3")
        except PermissionError as e:
            logger.error(f"Access denied writing persona review to S3: {str(e)}")
            return {
                "status": "error",
                "error": f"Access denied saving persona review to S3",
                "execution_summary": "Failed to save persona review: access denied",
                "persona_details": persona,
            }
        except Exception as e:
            logger.error(f"Failed to save persona review to S3: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to save persona review: {str(e)}",
                "execution_summary": f"Failed to save persona review to S3: {str(e)}",
                "persona_details": persona,
            }

        # Parse response to extract resonance score
        resonance_score = 7  # Default score, would be parsed from response in production
        
        execution_summary = f"Completed persona-based review from perspective of {age}yo {gender} {profession} from {national_origin}."
        
        logger.info(f"Persona reviewer agent completed successfully")
        
        return {
            "status": "success",
            "execution_summary": execution_summary,
            "persona_review": response_text,
            "persona_details": persona,
            "resonance_score": resonance_score,
        }

    except Exception as e:
        logger.error(f"Unexpected error in persona reviewer agent: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": f"Persona reviewer agent failed: {str(e)}",
            "execution_summary": f"Unexpected error during persona review: {str(e)}",
        }
