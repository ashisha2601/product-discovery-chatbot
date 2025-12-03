from typing import Optional

from pydantic import BaseModel, HttpUrl


class ProductBase(BaseModel):
    title: str
    price: Optional[float] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    features: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    category: Optional[str] = None
    source_url: Optional[HttpUrl] = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    class Config:
        from_attributes = True


