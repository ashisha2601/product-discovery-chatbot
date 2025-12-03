from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db, Base, engine
from app.models.product import Product
from app.schemas.product import ProductRead


# Ensure tables exist (simple for assignment; in production use migrations)
Base.metadata.create_all(bind=engine)

router = APIRouter()


@router.get("/", response_model=List[ProductRead])
def list_products(db: Session = Depends(get_db)) -> List[ProductRead]:
    products = db.query(Product).all()
    return products


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


