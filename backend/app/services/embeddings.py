from typing import List

from openai import OpenAI

from app.core.config import get_settings


settings = get_settings()
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)

EMBEDDING_MODEL = "text-embedding-3-small"


def embed_text(text: str) -> List[float]:
    """
    Generate a single embedding vector for the given text.
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


