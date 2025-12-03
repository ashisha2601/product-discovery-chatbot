from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductRead
from app.services.rag import index_all_products
from app.services.scraper_traya import scrape_traya_products

router = APIRouter()


@router.post("/scrape-traya", response_model=List[ProductRead])
def scrape_traya(db: Session = Depends(get_db)) -> List[ProductRead]:
    """
    Scrape products from Traya.health and store them in the database.
    Returns the list of products in the database after scraping.
    """
    scrape_traya_products(db=db)
    products = db.query(Product).all()
    return products


@router.post("/build-index", response_model=int)
def build_index(db: Session = Depends(get_db)) -> int:
    """
    Build or refresh the vector index over all products.
    Returns the number of indexed products.
    """
    return index_all_products(db=db)



