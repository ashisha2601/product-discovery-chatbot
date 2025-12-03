from typing import List

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.product import Product


BASE_URL = "https://traya.health"


def _fetch_html(url: str) -> str:
    # Follow redirects because Traya may redirect old product URLs
    resp = httpx.get(url, timeout=20.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def _parse_product_page(url: str) -> Product | None:
    """
    Very simple HTML parser for a Traya product page.
    NOTE: This is intentionally lightweight and may need adjustments
    if Traya's HTML structure changes.
    """
    html = _fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        return None

    # Price (best-effort)
    price = None
    price_tag = soup.find(string=lambda s: s and "₹" in s)
    if price_tag:
        text = price_tag.strip().replace("₹", "").replace(",", "")
        try:
            price = float("".join(ch for ch in text if (ch.isdigit() or ch == ".")))
        except ValueError:
            price = None

    # Short description / tagline
    short_desc = None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        short_desc = meta_desc["content"].strip()

    # Long description and features (best-effort from paragraphs and list items)
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    lis = [li.get_text(" ", strip=True) for li in soup.find_all("li")]
    long_description = "\n".join(paragraphs) if paragraphs else None

    # Try to infer features/benefits from list items
    features_text = "\n".join(lis) if lis else None

    # Image
    image_url = None
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        image_url = og_image["content"]

    # Very simple category extraction from breadcrumbs or tags if available
    category = None
    if "shampoo" in (long_description or "").lower():
        category = "shampoo"
    elif "serum" in (long_description or "").lower():
        category = "serum"
    elif "capsule" in (long_description or "").lower():
        category = "supplement"

    product = Product(
        title=title,
        price=price,
        short_description=short_desc,
        long_description=long_description,
        features=features_text,
        image_url=image_url,
        category=category,
        source_url=url,
    )
    return product


def scrape_traya_products(db: Session, limit: int = 80) -> List[Product]:
    """
    Scrape a set of Traya products.
    This uses a simple catalogue URL; in a real project you might
    need a more sophisticated crawler or a scraping API.
    """
    # Example collection page; adjust if structure changes
    collection_url = f"{BASE_URL}/collections/all"
    html = _fetch_html(collection_url)
    soup = BeautifulSoup(html, "html.parser")

    product_links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/products/" in href:
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            if full_url not in product_links:
                product_links.append(full_url)
        if len(product_links) >= limit:
            break

    created_products: List[Product] = []
    for url in product_links:
        existing = db.query(Product).filter_by(source_url=url).first()
        if existing:
            created_products.append(existing)
            continue

        product = _parse_product_page(url)
        if product:
            db.add(product)
            created_products.append(product)

    db.commit()
    for p in created_products:
        db.refresh(p)

    return created_products


