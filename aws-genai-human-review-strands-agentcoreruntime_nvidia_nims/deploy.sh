#!/bin/bash

# Unified Campaign Review System - Deployment Script

set -e

echo "🚀 Deploying Unified Campaign Review System..."

# Check if required tools are installed
command -v sam >/dev/null 2>&1 || { echo "❌ SAM CLI is required but not installed. Aborting." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm is required but not installed. Aborting." >&2; exit 1; }

# Get stack name from argument or use default
STACK_NAME=${1:-unified-campaign-review}

echo "📦 Building SAM application..."
sam build

echo "🏗️ Deploying infrastructure..."
sam deploy --stack-name $STACK_NAME --capabilities CAPABILITY_IAM --resolve-s3 --no-confirm-changeset

echo "📊 Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
AGENT_API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`CampaignOrchestratorApi`].OutputValue' --output text)
FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' --output text)
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' --output text)

echo "🔧 Configuring frontend environment..."
cat > .env << EOF
VITE_API_URL=$API_URL
VITE_AGENT_API_URL=$AGENT_API_URL
VITE_AWS_REGION=us-west-2
EOF

echo "📦 Installing frontend dependencies..."
npm install

echo "🏗️ Building frontend..."
npm run build

echo "📤 Uploading frontend to S3..."
aws s3 sync dist/ s3://$FRONTEND_BUCKET --delete

echo "✅ Deployment complete!"
echo ""
echo "🌐 Frontend URL: $CLOUDFRONT_URL"
echo "🔗 API URL: $API_URL"
echo "🤖 Agent API URL: $AGENT_API_URL"
echo ""
echo "📝 Environment file created: .env"
echo ""
echo "🎯 Your unified campaign review system is ready!"
