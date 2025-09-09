# Cathode API Deployment Guide

This guide covers deploying the Cathode Playlist API to Google Cloud using Docker containers.

## Overview

The application now features:
- **Preloaded Data**: All embeddings and metadata are loaded into memory on startup
- **FAISS Index**: Fast vector similarity search using Facebook AI Similarity Search
- **Optimized Performance**: No more loading data per request - everything is ready at startup
- **Health Checks**: Built-in health monitoring for production deployment

## Prerequisites

1. **Google Cloud CLI**: Install and authenticate
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Docker**: For local testing (optional)
   ```bash
   # Install Docker Desktop or Docker Engine
   ```

3. **Environment Variables**: Set up your API keys
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   export SPOTIFY_CLIENT_ID="your-spotify-client-id"
   export SPOTIFY_CLIENT_SECRET="your-spotify-client-secret"
   export PROJECT_ID="your-gcp-project-id"
   ```

## Local Development with Docker

### Build and Run Locally

```bash
# Build the Docker image
docker build -t cathode-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e SPOTIFY_CLIENT_ID="$SPOTIFY_CLIENT_ID" \
  -e SPOTIFY_CLIENT_SECRET="$SPOTIFY_CLIENT_SECRET" \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/models:/app/models:ro \
  cathode-api
```

### Using Docker Compose

```bash
# Create .env file with your API keys
cat > .env << EOF
GEMINI_API_KEY=your-gemini-api-key
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
EOF

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Google Cloud Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Run the deployment script
./deploy.sh
```

### Option 2: Manual Deployment

1. **Enable APIs**:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

2. **Build and Deploy**:
   ```bash
   # Build with Cloud Build
   gcloud builds submit --config cloudbuild.yaml
   
   # Or build and deploy manually
   docker build -t gcr.io/$PROJECT_ID/cathode-api .
   docker push gcr.io/$PROJECT_ID/cathode-api
   
   gcloud run deploy cathode-api \
     --image gcr.io/$PROJECT_ID/cathode-api \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --port 8000 \
     --memory 4Gi \
     --cpu 2 \
     --max-instances 10
   ```

3. **Set Environment Variables**:
   ```bash
   gcloud run services update cathode-api \
     --region us-central1 \
     --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY,SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID,SPOTIFY_CLIENT_SECRET=$SPOTIFY_CLIENT_SECRET"
   ```

## Data Management

### Including Data in Container

The current setup expects data files in the `data/` directory:
- `embeddings_chunk_*.npy` - Precomputed embeddings
- `other_columns_chunk_*.pkl` or `other_columns_chunk_*.csv` - Song metadata
- `models/` - Fine-tuned model files

### Alternative: Cloud Storage (Recommended for Production)

For large datasets, consider using Google Cloud Storage:

1. **Upload data to Cloud Storage**:
   ```bash
   gsutil -m cp -r data/ gs://your-bucket/cathode-data/
   gsutil -m cp -r models/ gs://your-bucket/cathode-models/
   ```

2. **Modify Dockerfile to download data on startup**:
   ```dockerfile
   # Add to Dockerfile before CMD
   RUN pip install google-cloud-storage
   COPY download_data.py .
   RUN python download_data.py
   ```

## Performance Optimization

### Startup Time
- **Cold Start**: ~30-60 seconds (loading embeddings + building FAISS index)
- **Warm Requests**: ~50-200ms (using preloaded data)

### Memory Usage
- **Base Application**: ~500MB
- **Embeddings**: ~2-8GB (depending on dataset size)
- **FAISS Index**: ~1-4GB
- **Total**: Recommend 4-8GB memory allocation

### Scaling Configuration

```yaml
# cloudbuild.yaml - adjust these settings
--memory=4Gi          # Increase for larger datasets
--cpu=2               # Increase for faster startup
--max-instances=10    # Scale based on expected traffic
--timeout=300         # Allow time for startup
```

## Monitoring and Debugging

### Health Checks

The API includes several health endpoints:
- `GET /health` - Detailed health status with timestamp
- `GET /` - Simple health check

### Logging

```bash
# View real-time logs
gcloud run logs tail cathode-api --region=us-central1

# View recent logs
gcloud run logs read cathode-api --region=us-central1 --limit=100
```

### Common Issues

1. **Out of Memory**: Increase memory allocation in Cloud Run
2. **Slow Startup**: Normal for first request; consider keeping one instance warm
3. **API Key Errors**: Check environment variables are set correctly

### Debugging Locally

```bash
# Run with debug logging
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e SPOTIFY_CLIENT_ID="$SPOTIFY_CLIENT_ID" \
  -e SPOTIFY_CLIENT_SECRET="$SPOTIFY_CLIENT_SECRET" \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/models:/app/models:ro \
  cathode-api
```

## API Usage

Once deployed, your API will be available at:
- **Health**: `https://your-service-url/health`
- **Docs**: `https://your-service-url/docs`
- **Create Playlist**: `POST https://your-service-url/api/playlist`

Example request:
```bash
curl -X POST "https://your-service-url/api/playlist" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I feel excited and energetic, ready to take on the world",
    "filters": {
      "genres": ["pop", "rock"],
      "exploration_level": "medium"
    }
  }'
```

## Cost Optimization

### Cloud Run Pricing
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests

### Recommendations
- Use minimum instances = 0 for development
- Use minimum instances = 1 for production (avoid cold starts)
- Monitor usage and adjust memory/CPU allocation
- Consider Cloud Run Jobs for batch processing

## Security

1. **API Keys**: Store in Google Secret Manager for production
2. **Authentication**: Add authentication for production use
3. **Network**: Consider VPC connector for private networks
4. **CORS**: Update allowed origins for production domains

## Next Steps

1. Set up monitoring with Google Cloud Monitoring
2. Configure alerts for high error rates or latency
3. Set up CI/CD pipeline with GitHub Actions
4. Consider using Cloud Build triggers for automatic deployment
5. Implement caching for frequently requested playlists
