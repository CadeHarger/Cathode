# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Set environment variable for the embedding service URL
# This should be overridden in docker-compose.yml or cloud deployment
#   ENV EMBEDDING_SERVICE_URL="http://localhost:8501"
ENV EMBEDDING_SERVICE_URL="https://us-central1-aiplatform.googleapis.com/v1/projects/819206197072/locations/us-central1/endpoints/6143915944872771584:predict" 

# Command to run the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
