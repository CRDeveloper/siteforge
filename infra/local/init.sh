#!/bin/bash
# Local dev initialization — creates DynamoDB tables and test data

set -e

AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}
DYNAMODB_ENDPOINT=${DYNAMODB_ENDPOINT:-http://localhost:8000}
SITE_ID=${SITE_ID:-serenity-therapy}

echo "🚀 Initializing SiteForge local dev environment..."

# Create DynamoDB table
echo "📦 Creating DynamoDB table..."
aws dynamodb create-table \
  --endpoint-url $DYNAMODB_ENDPOINT \
  --region $AWS_REGION \
  --table-name siteforge-$SITE_ID \
  --attribute-definitions \
    AttributeName=pk,AttributeType=S \
    AttributeName=sk,AttributeType=S \
    AttributeName=email,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes \
    'IndexName=email-index,Keys=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL}' \
    'IndexName=sk-index,Keys=[{AttributeName=sk,KeyType=HASH},{AttributeName=pk,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
  2>/dev/null || echo "✓ Table already exists"

# Create LocalStack SNS topic for SES notifications
echo "📢 Creating SNS topic..."
aws sns create-topic \
  --endpoint-url http://localstack:4566 \
  --region $AWS_REGION \
  --name siteforge-$SITE_ID-ses-notifications 2>/dev/null || echo "✓ Topic already exists"

# Seed test data
echo "🌱 Seeding test data..."
aws dynamodb put-item \
  --endpoint-url $DYNAMODB_ENDPOINT \
  --region $AWS_REGION \
  --table-name siteforge-$SITE_ID \
  --item '{
    "pk": {"S": "ADMIN#admin@example.com"},
    "sk": {"S": "USER"},
    "email": {"S": "admin@example.com"},
    "firstName": {"S": "Admin"},
    "lastName": {"S": "User"},
    "role": {"S": "admin"},
    "verified": {"BOOL": true},
    "createdAt": {"N": "'$(date +%s)'"}
  }' 2>/dev/null || echo "✓ Admin user exists"

echo "✅ Local dev environment ready!"
echo "📍 API: http://localhost:3001"
echo "📍 DynamoDB: $DYNAMODB_ENDPOINT"
echo "📍 LocalStack: http://localstack:4566"
