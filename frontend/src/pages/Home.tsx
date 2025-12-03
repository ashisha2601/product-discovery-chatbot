import { useEffect, useState } from "react";
import { fetchProducts, type Product } from "../api";
import { ProductCard } from "../components/ProductCard";

export function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchProducts();
        setProducts(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <p className="status">Loading products...</p>;
  }

  if (error) {
    return <p className="status error">Failed to load products: {error}</p>;
  }

  return (
    <div>
      <h1>Traya Products</h1>
      <p className="subtitle">
        Browse all scraped Traya.health products. Click any card to see details.
      </p>
      <div className="grid">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}


