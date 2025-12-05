import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchProduct, type Product } from "../api";

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!id) return;
      try {
        const data = await fetchProduct(Number(id));
        setProduct(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return <p className="status">Loading product...</p>;
  }

  if (error) {
    return <p className="status error">Failed to load product: {error}</p>;
  }

  if (!product) {
    return <p className="status error">Product not found.</p>;
  }

  const showPriceAsUnknown =
    product.price == null || product.price === 0;

  return (
    <div>
      <Link to="/" className="back-link">
        ← Back to products
      </Link>

      <div className="detail-layout">
        {product.image_url && (
          <img
            src={product.image_url}
            alt={product.title}
            className="detail-image"
          />
        )}

        <div className="detail-body">
          <h1>{product.title}</h1>
          {showPriceAsUnknown ? (
            <p className="detail-price">
              Price: N/A – please check the Traya site for the latest price
            </p>
          ) : (
            <p className="detail-price">₹{product.price!.toFixed(2)}</p>
          )}
          {product.category && (
            <p className="detail-category">Category: {product.category}</p>
          )}

          {product.short_description && (
            <>
              <h2>Summary</h2>
              <p>{product.short_description}</p>
            </>
          )}

          {product.features && (
            <>
              <h2>Key benefits / features</h2>
              <p style={{ whiteSpace: "pre-line" }}>{product.features}</p>
            </>
          )}

          {product.long_description && (
            <>
              <h2>Details</h2>
              <p style={{ whiteSpace: "pre-line" }}>{product.long_description}</p>
            </>
          )}

          {product.source_url && (
            <p className="detail-source">
              Original page:{" "}
              <a href={product.source_url} target="_blank" rel="noreferrer">
                Traya.health
              </a>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}


