// Bedrock Agent Core Runtime API endpoint
// Format: https://<agent-alias-id>.execute-api.<region>.amazonaws.com/<stage>/invoke
const AGENT_CORE_ENDPOINT = import.meta.env.VITE_AGENT_CORE_API_URL || 'https://your-agent-alias-id.execute-api.us-west-2.amazonaws.com/prod/invoke';

/**
 * Submit campaign review to Bedrock Agent Core Runtime
 * @param campaignData - The campaign data to review
 * @returns Agent response
 */
export const submitCampaignReview = async (campaignData: string) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 45000); // 45s timeout

  try {
    // Bedrock Agent Core Runtime payload format
    const payload = {
      inputText: campaignData,
      // Optional: Add session attributes
      sessionAttributes: {},
      promptSessionAttributes: {},
    };

    const response = await fetch(AGENT_CORE_ENDPOINT, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        // Note: In production, you may need AWS Signature V4 authentication
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`Agent Core API request failed: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    // Parse Agent Core Runtime response
    return result.completion || result.output || result;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Review request timed out. Please try again.');
    }
    throw error;
  }
};
