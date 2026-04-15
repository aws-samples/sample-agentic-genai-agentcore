import json
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SSM_PARAM = os.environ.get('AGENT_ARN_PARAM', '/agentcore/campaign-review/agent-arn')
FUNCTION_NAME = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
REGION = os.environ.get('AWS_REGION', 'us-west-2')

ssm = boto3.client('ssm', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
agentcore = boto3.client('bedrock-agentcore', region_name=REGION)


def get_agent_arn():
    resp = ssm.get_parameter(Name=SSM_PARAM)
    return resp['Parameter']['Value']


def invoke_agentcore(agent_arn, payload):
    """Invoke AgentCore Runtime and return response text."""
    logger.info(f"Invoking AgentCore: {agent_arn}")
    response = agentcore.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        payload=json.dumps(payload)
    )

    content_type = response.get("contentType", "")
    if "text/event-stream" in content_type:
        lines = []
        for line in response["response"].iter_lines(chunk_size=1):
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    decoded = decoded[6:]
                lines.append(decoded)
        return "\n".join(lines)
    else:
        events = []
        for event in response.get("response", []):
            events.append(event.decode("utf-8"))
        return events[0] if events else ""


def handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")

    # Async worker mode — invoked by self with InvocationType='Event'
    if event.get("_async"):
        payload = event["_async"]
        try:
            agent_arn = get_agent_arn()
            result = invoke_agentcore(agent_arn, payload)
            logger.info(f"AgentCore completed for campaign {payload.get('campaignId')}: {len(result)} chars")
        except Exception as e:
            logger.error(f"AgentCore invocation failed: {e}", exc_info=True)
        return

    # Sync mode — API Gateway request, return 202 immediately
    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        campaign_id = body.get('campaignId')
        s3_key = body.get('s3Key')
        bucket_name = body.get('bucket_name', os.environ.get('CAMPAIGN_BUCKET', ''))

        if not campaign_id or not s3_key:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing campaignId or s3Key'})
            }

        # Fire async self-invocation
        async_payload = {
            '_async': {
                'campaignId': campaign_id,
                's3Key': s3_key,
                'bucket_name': bucket_name
            }
        }
        lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType='Event',
            Payload=json.dumps(async_payload)
        )
        logger.info(f"Async invocation triggered for campaign {campaign_id}")

        return {
            'statusCode': 202,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Campaign review started',
                'status': 'processing',
                'campaign_id': campaign_id
            })
        }

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
