# Cathode API Docker Deployment

This directory contains the configuration to run the Cathode API and its associated embedding model as separate Docker containers.

## Prerequisites

- Docker and Docker Compose installed.
- A `.env` file in the `backend/cloud_deployment` directory with the following variables:
  ```
  GEMINI_API_KEY=your_gemini_api_key
  SPOTIFY_CLIENT_ID=your_spotify_client_id
  SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
  ```

## Services

There are two services defined in the `docker-compose.yml` file:

1.  **`embedding_model`**: This service builds and runs the fine-tuned sentence transformer model, exposing a `/predict` endpoint for generating embeddings. It runs on port `8501`.
2.  **`cathode_api`**: This is the main FastAPI application that serves the playlist generation logic. It depends on the `embedding_model` service and communicates with it to get embeddings for user queries. It runs on port `8000`.

## How to Run

1.  Navigate to the `backend/cloud_deployment` directory.
2.  Make sure you have a `.env` file with the necessary API keys.
3.  Run the following command to build and start the services:

    ```bash
    docker-compose up --build
    ```

    The `--build` flag is only necessary the first time or when you make changes to the code or Dockerfiles.

4.  The Cathode API will be available at `http://localhost:8000`.
5.  The embedding model's health check will be at `http://localhost:8501/health`.

## Stopping the Services

To stop the running containers, press `Ctrl+C` in the terminal where `docker-compose up` is running, or run the following command from the `backend/cloud_deployment` directory:

```bash
docker-compose down
```
