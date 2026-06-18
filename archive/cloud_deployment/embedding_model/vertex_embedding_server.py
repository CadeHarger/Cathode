from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
from typing import Optional


def load_finetuned_model(model_path: Optional[str] = None) -> SentenceTransformer:

    if model_path is None:
        # Default to the epoch 1 model from training
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "finetuned_model")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Finetuned model not found at {model_path}. "
            "Please ensure the model has been trained and saved, or provide a valid model_path."
        )
    
    print(f"Loading finetuned model from: {model_path}")
    
    try:
        # Load the finetuned model
        model = SentenceTransformer(model_path)
        print(f"✅ Successfully loaded finetuned model")
        print(f"   Model info: {type(model).__name__}")
        
        # Verify the model can encode text
        test_embedding = model.encode("test", convert_to_tensor=False)
        # Handle both 1D and 2D embedding shapes
        if test_embedding.ndim == 1:
            embedding_dim = test_embedding.shape[0]
        else:
            embedding_dim = test_embedding.shape[1]
        print(f"   Embedding dimension: {embedding_dim}")
        
        return model
        
    except Exception as e:
        raise RuntimeError(f"Failed to load finetuned model from {model_path}: {e}")


app = FastAPI()
model: SentenceTransformer = load_finetuned_model()


class Input(BaseModel):
    sentences: list[str]


@app.post("/predict")
def predict(input: Input):
    embeddings = model.encode(
        input.sentences,
        convert_to_tensor=False,
        normalize_embeddings=True,
    ).tolist()
    return {"embeddings": embeddings}


@app.get("/health")
def health():
    try:
        # Prefer library method when available
        if hasattr(model, "get_sentence_embedding_dimension"):
            dim = model.get_sentence_embedding_dimension()
        else:
            dim = len(model.encode("health_check", convert_to_tensor=False))
    except Exception:
        dim = None
    return {
        "status": "healthy",
        "service": "Embedding Model Server",
        "embedding_dimension": dim,
    }
