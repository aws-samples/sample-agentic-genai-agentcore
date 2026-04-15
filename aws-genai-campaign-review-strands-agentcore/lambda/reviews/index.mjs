import { S3Client, ListObjectsV2Command, GetObjectCommand } from '@aws-sdk/client-s3';

const s3Client = new S3Client({ region: process.env.S3_REGION || 'us-west-2' });

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

    // Filter for .md files only
    const mdFiles = objects.filter(obj => obj.Key && obj.Key.endsWith('.md'));
    
    console.log(`Found ${mdFiles.length} .md files`);

    // Fetch content of each .md file
    const reviews = [];
    
    for (const mdFile of mdFiles) {
      try {
        const getCommand = new GetObjectCommand({
          Bucket: process.env.S3_BUCKET,
          Key: mdFile.Key,
        });

        const getResponse = await s3Client.send(getCommand);
        const content = await streamToString(getResponse.Body);

        // Extract folder name (persona name) from the key
        // e.g., "campaigns/123/reviews/persona1/campaign_review.md" -> "persona1"
        // or "review/persona1/campaign_review.md" -> "persona1"
        const keyParts = mdFile.Key.split('/');
        let folderName = 'unknown';
        let fileName = keyParts[keyParts.length - 1];
        
        if (campaignId) {
          // campaigns/{id}/reviews/{persona}/file.md
          folderName = keyParts.length >= 4 ? keyParts[3] : 'unknown';
        } else {
          // review/{persona}/file.md
          folderName = keyParts.length >= 2 ? keyParts[1] : 'unknown';
        }

        reviews.push({
          persona: folderName,
          fileName: fileName,
          key: mdFile.Key,
          content: content,
          lastModified: mdFile.LastModified,
        });

        console.log(`Fetched review: ${mdFile.Key}`);
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
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: false,
        error: error.message || 'Unknown error fetching reviews',
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
