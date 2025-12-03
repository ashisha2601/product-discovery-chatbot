from sqlalchemy import Column, Float, Integer, String, Text

from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    price = Column(Float, nullable=True)
    short_description = Column(Text, nullable=True)
    long_description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # simple text/JSON string for now
    image_url = Column(String(512), nullable=True)
    category = Column(String(128), nullable=True)
    source_url = Column(String(512), nullable=True)


