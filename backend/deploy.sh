#!/bin/bash

# Cathode API Deployment Script for Google Cloud
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="cathode-api"

echo "🚀 Deploying Cathode API to Google Cloud..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy using Cloud Build
echo "🏗️  Building and deploying with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Deployment successful!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🏥 Health check: $SERVICE_URL/health"
echo "📊 API docs: $SERVICE_URL/docs"

# Test the health endpoint
echo ""
echo "🩺 Testing health endpoint..."
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed. Service might still be starting up."
    echo "   Check logs with: gcloud run logs tail $SERVICE_NAME --region=$REGION"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Set environment variables (API keys) in Cloud Run console"
echo "2. Upload your data files to the container or use Cloud Storage"
echo "3. Monitor logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
