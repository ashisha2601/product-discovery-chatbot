from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class RecommendedProduct(BaseModel):
    product_id: int
    reason: str


class ChatResponse(BaseModel):
    reply: str
    recommended_products: List[RecommendedProduct] = []


