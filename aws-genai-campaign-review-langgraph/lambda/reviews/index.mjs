import { S3Client, ListObjectsV2Command, GetObjectCommand } from '@aws-sdk/client-s3';

const s3Client = new S3Client({ region: process.env.S3_REGION || 'us-east-1' });

export const handler = async (event) => {
  console.log('Reviews event:', JSON.stringify(event, null, 2));

  try {
    // Extract campaign ID from query parameters
    const campaignId = event.queryStringParameters?.campaignId;
    
    let reviewPrefix;
    if (campaignId) {
      reviewPrefix = `campaigns/${campaignId}/reviews/`;
      console.log(`Fetching reviews for campaign: ${campaignId}`);
    } else {
      reviewPrefix = process.env.S3_REVIEW_PREFIX || 'review/';
      console.log('Fetching reviews from default path');
    }
    
    console.log(`Using prefix: ${reviewPrefix}`);
    
    // List all objects in the review prefix
    const listCommand = new ListObjectsV2Command({
      Bucket: process.env.S3_BUCKET,
      Prefix: reviewPrefix,
    });

    const listResponse = await s3Client.send(listCommand);
    const objects = listResponse.Contents || [];

    console.log(`Found ${objects.length} objects in ${reviewPrefix}`);

    // Filter for campaign_review.md files only (the persona-based review)
    const campaignReviewFiles = objects.filter(obj => 
      obj.Key && 
      obj.Key.endsWith('/campaign_review.md') &&
      obj.Key.includes('/reviews/')
    );
    
    console.log(`Found ${campaignReviewFiles.length} campaign_review.md files`);

    // Fetch content of each campaign_review.md file
    const reviews = [];
    
    for (const mdFile of campaignReviewFiles) {
      try {
        const getCommand = new GetObjectCommand({
          Bucket: process.env.S3_BUCKET,
          Key: mdFile.Key,
        });

        const getResponse = await s3Client.send(getCommand);
        const content = await streamToString(getResponse.Body);

        // Extract persona name from the key
        // e.g., "campaigns/campaign_123/reviews/persona_023/campaign_review.md" -> "persona_023"
        const keyParts = mdFile.Key.split('/');
        let personaId = 'unknown';
        let fileName = keyParts[keyParts.length - 1];
        
        if (campaignId) {
          // campaigns/{id}/reviews/{persona}/campaign_review.md
          // keyParts: ["campaigns", "campaign_123", "reviews", "persona_023", "campaign_review.md"]
          if (keyParts.length >= 5 && keyParts[2] === 'reviews') {
            personaId = keyParts[3];
          }
        } else {
          // review/{persona}/campaign_review.md
          if (keyParts.length >= 3) {
            personaId = keyParts[1];
          }
        }

        reviews.push({
          persona: personaId,
          fileName: fileName,
          key: mdFile.Key,
          content: content,
          lastModified: mdFile.LastModified,
        });

        console.log(`Fetched campaign review for persona: ${personaId}`);
      } catch (fileError) {
        console.error(`Error fetching ${mdFile.Key}:`, fileError);
      }
    }

    // Sort reviews by persona name
    reviews.sort((a, b) => a.persona.localeCompare(b.persona));

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: true,
        count: reviews.length,
        reviews: reviews,
        campaignId: campaignId,
      }),
    };
  } catch (error) {
    console.error('Error fetching reviews:', error);
    console.error('Error stack:', error.stack);
    console.error('S3_BUCKET env:', process.env.S3_BUCKET);
    console.error('S3_REGION env:', process.env.S3_REGION);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: false,
        error: error.message || 'Unknown error fetching reviews',
        errorType: error.name,
        bucket: process.env.S3_BUCKET,
        region: process.env.S3_REGION,
      }),
    };
  }
};

// Helper function to convert stream to string
async function streamToString(stream) {
  const chunks = [];
  for await (const chunk of stream) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString('utf-8');
}
