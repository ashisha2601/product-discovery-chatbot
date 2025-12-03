from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import run_rag_chat

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """
    Chat endpoint powered by the RAG pipeline over Traya products.
    """
    return run_rag_chat(db=db, messages=payload.messages)



