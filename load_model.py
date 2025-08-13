import os
from sentence_transformers import SentenceTransformer
from typing import Optional


def load_finetuned_model(model_path: Optional[str] = None) -> SentenceTransformer:
    """
    Load the finetuned SentenceTransformer model.
    
    Args:
        model_path: Path to the finetuned model. If None, defaults to epoch_1 from training output.
    
    Returns:
        SentenceTransformer: The loaded finetuned model
    """
    if model_path is None:
        # Default to the epoch 1 model from training
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "mpnet_lyrics_lora", "epoch_1")
    
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
        print(f"   Embedding dimension: {test_embedding.shape[1]}")
        
        return model
        
    except Exception as e:
        raise RuntimeError(f"Failed to load finetuned model from {model_path}: {e}")


def get_model_info(model: SentenceTransformer) -> dict:
    """
    Get information about the loaded model.
    
    Args:
        model: The SentenceTransformer model
        
    Returns:
        dict: Model information including embedding dimension
    """
    try:
        # Test encoding to get dimension
        test_embedding = model.encode("test", convert_to_tensor=False)
        return {
            "embedding_dimension": test_embedding.shape[1],
            "model_type": type(model).__name__,
            "is_finetuned": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "model_type": type(model).__name__,
            "is_finetuned": True
        }


def is_finetuned_model_available() -> bool:
    """
    Check if the finetuned model is available.
    
    Returns:
        bool: True if the finetuned model exists and can be loaded
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "mpnet_lyrics_lora", "epoch_1")
        return os.path.exists(model_path)
    except Exception:
        return False


def get_finetuned_model_path() -> Optional[str]:
    """
    Get the path to the finetuned model if it exists.
    
    Returns:
        Optional[str]: Path to the finetuned model, or None if not found
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "mpnet_lyrics_lora", "epoch_1")
        if os.path.exists(model_path):
            return model_path
        return None
    except Exception:
        return None


if __name__ == "__main__":
    # Test loading the model
    print("🔍 Checking finetuned model availability...")
    
    if is_finetuned_model_available():
        print("✅ Finetuned model found!")
        model_path = get_finetuned_model_path()
        print(f"   Path: {model_path}")
        
        try:
            print("\n🚀 Loading finetuned model...")
            model = load_finetuned_model()
            info = get_model_info(model)
            print(f"\n📊 Model info: {info}")
            print("\n🎯 Model is ready to use!")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
    else:
        print("❌ Finetuned model not found")
        print("   Expected location: mpnet_lyrics_lora/epoch_1/")
        print("   Please run the training script first to generate the finetuned model")
