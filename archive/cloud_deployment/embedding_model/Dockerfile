# Minimal image for the embedding server
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Copy and install dependencies (build context is embedding_model folder)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy server code from current context
COPY . /app/cloud_deployment/embedding_model/

# Copy finetuned model (must exist in build context at ./finetuned_model)
COPY finetuned_model/ /app/cloud_deployment/embedding_model/finetuned_model/

EXPOSE 8080

CMD ["uvicorn", "cloud_deployment.embedding_model.vertex_embedding_server:app", "--host", "0.0.0.0", "--port", "8001"]
