import os
from sentence_transformers import SentenceTransformer
from typing import Optional

from paths import get_finetuned_model_path as _default_model_path


def load_finetuned_model(model_path: Optional[str] = None) -> SentenceTransformer:
    """
    Load the finetuned SentenceTransformer model.

    Args:
        model_path: Path to the finetuned model. If None, defaults to epoch_1 from training output.

    Returns:
        SentenceTransformer: The loaded finetuned model
    """
    if model_path is None:
        model_path = _default_model_path()

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Finetuned model not found at {model_path}. "
            "Please ensure the model has been trained and saved, or provide a valid model_path."
        )

    print(f"Loading finetuned model from: {model_path}")

    try:
        model = SentenceTransformer(model_path)
        print("✅ Finetuned model loaded successfully")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load finetuned model from {model_path}: {e}")


def get_model_info(model: SentenceTransformer) -> dict:
    """Get information about the loaded model."""
    try:
        return {
            "max_seq_length": model.max_seq_length,
            "embedding_dimension": model.get_sentence_embedding_dimension(),
            "model_type": type(model).__name__,
            "is_finetuned": True,
        }
    except Exception as e:
        return {
            "error": str(e),
            "model_type": type(model).__name__,
            "is_finetuned": True,
        }


def is_finetuned_model_available() -> bool:
    """Check if the finetuned model is available."""
    try:
        return os.path.exists(_default_model_path())
    except Exception:
        return False


def get_finetuned_model_path() -> Optional[str]:
    """Get the path to the finetuned model if it exists."""
    path = _default_model_path()
    return path if os.path.exists(path) else None


if __name__ == "__main__":
    print("Checking finetuned model availability...")

    if is_finetuned_model_available():
        print("Finetuned model found!")
        print(f"   Path: {get_finetuned_model_path()}")

        try:
            print("\nLoading finetuned model...")
            model = load_finetuned_model()
            info = get_model_info(model)
            print(f"\nModel info: {info}")
        except Exception as e:
            print(f"Error loading model: {e}")
    else:
        print("Finetuned model not found")
        print("   Expected location: models/mpnet_lyrics_lora/epoch_1/")
        print("   Run modify/finetune_embeds.py to generate the finetuned model")
