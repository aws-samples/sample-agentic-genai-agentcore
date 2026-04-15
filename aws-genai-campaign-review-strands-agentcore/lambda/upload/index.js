const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

const s3Client = new S3Client({ region: process.env.S3_REGION || 'us-west-2' });

exports.handler = async (event) => {
  console.log('Upload event:', JSON.stringify(event, null, 2));

  try {
    // Parse the incoming request
    const contentType = event.headers['content-type'] || event.headers['Content-Type'] || '';
    
    if (!contentType.includes('multipart/form-data')) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          success: false,
          error: 'Content-Type must be multipart/form-data',
        }),
      };
    }

    // Parse multipart form data
    const boundary = contentType.split('boundary=')[1];
    if (!boundary) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          success: false,
          error: 'Missing boundary in Content-Type',
        }),
      };
    }

    // Decode base64 body if needed
    const body = event.isBase64Encoded 
      ? Buffer.from(event.body, 'base64')
      : Buffer.from(event.body);

    // Parse multipart data
    const parts = parseMultipart(body, boundary);
    const filePart = parts.find(p => p.name === 'file');
    const keyPart = parts.find(p => p.name === 'key');

    if (!filePart || !filePart.data) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          success: false,
          error: 'No file provided in request',
        }),
      };
    }

    // Use custom key if provided, otherwise generate one
    let key;
    if (keyPart && keyPart.data) {
      key = keyPart.data.toString('utf-8');
    } else {
      // Generate S3 key (fallback)
      const timestamp = Date.now();
      const filename = filePart.filename || 'unknown';
      key = `${process.env.S3_PREFIX || 'data/'}${timestamp}-${filename}`;
    }

    // Upload to S3
    const command = new PutObjectCommand({
      Bucket: process.env.S3_BUCKET,
      Key: key,
      Body: filePart.data,
      ContentType: filePart.contentType || 'application/octet-stream',
    });

    await s3Client.send(command);

    const url = `https://${process.env.S3_BUCKET}.s3.${process.env.S3_REGION}.amazonaws.com/${key}`;

    console.log(`File uploaded successfully: ${url}`);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: true,
        key,
        url,
        filename: filePart.filename || 'unknown',
        size: filePart.data.length,
      }),
    };
  } catch (error) {
    console.error('Upload error:', error);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: false,
        error: error.message || 'Unknown upload error',
      }),
    };
  }
};

// Helper function to parse multipart form data
function parseMultipart(buffer, boundary) {
  const parts = [];
  const boundaryBuffer = Buffer.from(`--${boundary}`);
  const endBoundary = Buffer.from(`--${boundary}--`);
  
  let position = 0;
  
  while (position < buffer.length) {
    // Find next boundary
    const boundaryIndex = buffer.indexOf(boundaryBuffer, position);
    if (boundaryIndex === -1) break;
    
    // Check if this is the end boundary
    const isEndBoundary = buffer.indexOf(endBoundary, boundaryIndex) === boundaryIndex;
    if (isEndBoundary) break;
    
    // Move past the boundary and CRLF
    position = boundaryIndex + boundaryBuffer.length;
    if (buffer[position] === 13 && buffer[position + 1] === 10) {
      position += 2;
    }
    
    // Find the end of headers (double CRLF)
    const headersEnd = buffer.indexOf(Buffer.from('\r\n\r\n'), position);
    if (headersEnd === -1) break;
    
    // Parse headers
    const headersBuffer = buffer.slice(position, headersEnd);
    const headers = headersBuffer.toString('utf-8');
    
    // Extract name and filename from Content-Disposition
    const dispositionMatch = headers.match(/Content-Disposition: form-data; name="([^"]+)"(?:; filename="([^"]+)")?/i);
    const contentTypeMatch = headers.match(/Content-Type: ([^\r\n]+)/i);
    
    if (dispositionMatch) {
      const name = dispositionMatch[1];
      const filename = dispositionMatch[2];
      const contentType = contentTypeMatch ? contentTypeMatch[1] : null;
      
      // Find the start of data (after headers)
      const dataStart = headersEnd + 4; // +4 for \r\n\r\n
      
      // Find the next boundary
      const nextBoundary = buffer.indexOf(boundaryBuffer, dataStart);
      const dataEnd = nextBoundary !== -1 ? nextBoundary - 2 : buffer.length; // -2 for \r\n before boundary
      
      const data = buffer.slice(dataStart, dataEnd);
      
      parts.push({
        name,
        filename,
        contentType,
        data,
      });
      
      position = dataEnd;
    } else {
      position = headersEnd + 4;
    }
  }
  
  return parts;
}
