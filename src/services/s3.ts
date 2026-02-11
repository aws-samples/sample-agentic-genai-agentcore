// Backend API endpoint for S3 uploads
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';
const UPLOAD_API_URL = `${API_BASE_URL}/upload`;

export interface UploadResult {
  success: boolean;
  key?: string;
  url?: string;
  campaignId?: string;
  error?: string;
}

/**
 * Generate a unique campaign ID based on timestamp
 * @returns Campaign ID string
 */
export const generateCampaignId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `campaign_${timestamp}_${random}`;
};

/**
 * Upload a file to S3 via the backend server with campaign ID structure
 * @param file - The File object to upload
 * @param campaignId - Optional campaign ID, will generate if not provided
 * @returns Upload result with S3 key, URL, and campaign ID
 */
export const uploadFileToS3 = async (file: File, campaignId?: string): Promise<UploadResult> => {
  try {
    const currentCampaignId = campaignId || generateCampaignId();
    const campaignKey = `campaigns/${currentCampaignId}/campaign_brief.md`;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('key', campaignKey); // Specify the S3 key path

    const response = await fetch(UPLOAD_API_URL, {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      return {
        success: false,
        error: result.error || `Upload failed with status ${response.status}`,
      };
    }

    return {
      success: true,
      key: result.key,
      url: result.url,
      campaignId: currentCampaignId,
    };
  } catch (error) {
    console.error('S3 upload error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown upload error',
    };
  }
};

/**
 * Get the S3 URL for a given key
 * @param key - The S3 object key
 * @returns The full S3 URL
 */
export const getS3Url = (key: string): string => {
  return `https://blogs-s3-akshay.s3.us-east-1.amazonaws.com/${key}`;
};

// Backend API endpoint for fetching reviews
const REVIEWS_API_URL = `${API_BASE_URL}/reviews`;

export interface PersonaReview {
  persona: string;
  fileName: string;
  key: string;
  content: string;
  lastModified: string;
}

export interface ReviewsResult {
  success: boolean;
  count?: number;
  reviews?: PersonaReview[];
  error?: string;
}

/**
 * Fetch all persona reviews from S3 via the backend server
 * @param campaignId - Optional campaign ID to fetch reviews for specific campaign
 * @returns Array of persona reviews
 */
export const fetchReviews = async (campaignId?: string): Promise<ReviewsResult> => {
  try {
    const url = campaignId 
      ? `${REVIEWS_API_URL}?campaignId=${encodeURIComponent(campaignId)}`
      : REVIEWS_API_URL;
      
    const response = await fetch(url, {
      method: 'GET',
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      return {
        success: false,
        error: result.error || `Failed to fetch reviews with status ${response.status}`,
      };
    }

    return {
      success: true,
      count: result.count,
      reviews: result.reviews,
    };
  } catch (error) {
    console.error('Error fetching reviews:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error fetching reviews',
    };
  }
};

// Bedrock Agent Core Runtime API integration
// Format: https://<agent-alias-id>.execute-api.<region>.amazonaws.com/<stage>/invoke
// Example: https://abc123xyz.execute-api.us-west-2.amazonaws.com/prod/invoke
const AGENT_CORE_API_URL = import.meta.env.VITE_AGENT_CORE_API_URL || 'https://your-agent-alias-id.execute-api.us-west-2.amazonaws.com/prod/invoke';

export interface AgentApiResult {
  success: boolean;
  message?: string;
  status?: string;
  campaign_id?: string;
  results?: string;
  error?: string;
}

/**
 * Call the Bedrock Agent Core Runtime API to process a campaign
 * @param campaignId - The campaign ID
 * @param s3Key - The S3 key of the uploaded file
 * @returns Agent API result
 */
export const callAgentAPI = async (campaignId: string, s3Key: string): Promise<AgentApiResult> => {
  try {
    // Bedrock Agent Core Runtime expects a specific payload format
    const payload = {
      inputText: JSON.stringify({
        campaignId,
        s3Key,
      }),
      // Optional: Add session attributes if needed
      sessionAttributes: {
        campaignId,
      },
      // Optional: Add prompt session attributes for additional context
      promptSessionAttributes: {},
    };

    const response = await fetch(AGENT_CORE_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Note: In production, you may need to add AWS Signature V4 authentication
        // or use AWS Amplify for automatic credential management
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || `Agent Core API failed with status ${response.status}`,
      };
    }

    // Parse Agent Core Runtime response format
    // The response structure may vary based on your agent configuration
    const agentResponse = result.completion || result.output || result;
    
    return {
      success: true,
      message: agentResponse.message || 'Campaign review started',
      status: agentResponse.status || 'processing',
      campaign_id: agentResponse.campaign_id || campaignId,
      results: agentResponse.results,
    };
  } catch (error) {
    console.error('Agent Core API error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown agent API error',
    };
  }
};

export interface StatusResult {
  success: boolean;
  status?: string;
  stage?: string;
  timestamp?: string;
  error?: string;
}

/**
 * Poll the status of a campaign processing
 * @param campaignId - The campaign ID to check status for
 * @returns Status result
 */
export const pollCampaignStatus = async (campaignId: string): Promise<StatusResult> => {
  try {
    const statusUrl = `${API_BASE_URL}/status/${campaignId}`;
    const response = await fetch(statusUrl, {
      method: 'GET',
    });

    const result = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || `Status check failed with status ${response.status}`,
      };
    }

    return {
      success: true,
      status: result.status,
      stage: result.stage,
      timestamp: result.timestamp,
    };
  } catch (error) {
    console.error('Status polling error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown status polling error',
    };
  }
};
