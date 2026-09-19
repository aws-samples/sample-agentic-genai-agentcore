#!/bin/bash
# Build a Docker image via CodeBuild and wait for completion.
# Args: <project_name> <region> <repo_name> <image_tag> <repo_url>
set -e

PROJECT_NAME="$1"
REGION="$2"
REPO_NAME="$3"
IMAGE_TAG="$4"
REPO_URL="$5"

echo "=============================================="
echo "Building image: $REPO_URL:$IMAGE_TAG"
echo "  CodeBuild project: $PROJECT_NAME"
echo "  Region:            $REGION"
echo "=============================================="

BUILD_ID=$(aws codebuild start-build \
  --project-name "$PROJECT_NAME" \
  --region "$REGION" \
  --query 'build.id' --output text)

echo "Started build: $BUILD_ID"
echo "Waiting for build to complete..."

while true; do
  STATUS=$(aws codebuild batch-get-builds \
    --ids "$BUILD_ID" \
    --region "$REGION" \
    --query 'builds[0].buildStatus' --output text)

  case "$STATUS" in
    SUCCEEDED)
      echo "✅ Build succeeded"
      break
      ;;
    FAILED|FAULT|STOPPED|TIMED_OUT)
      echo "❌ Build $STATUS"
      aws codebuild batch-get-builds --ids "$BUILD_ID" --region "$REGION" \
        --query 'builds[0].phases[?phaseStatus==`FAILED`]' || true
      exit 1
      ;;
    IN_PROGRESS)
      echo "  ... still building"
      sleep 15
      ;;
    *)
      echo "  ... status: $STATUS"
      sleep 10
      ;;
  esac
done

# Verify image exists
aws ecr describe-images \
  --repository-name "$REPO_NAME" \
  --image-ids "imageTag=$IMAGE_TAG" \
  --region "$REGION" > /dev/null

echo "✅ Image verified in ECR: $REPO_URL:$IMAGE_TAG"
