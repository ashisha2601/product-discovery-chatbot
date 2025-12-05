import { Link } from "react-router-dom";
import type { Product } from "../api";

interface Props {
  product: Product;
  reason?: string;
}

export function ProductCard({ product, reason }: Props) {
  const showPriceAsUnknown =
    product.price == null || product.price === 0;

  return (
    <div className="card">
      {product.image_url && (
        <img src={product.image_url} alt={product.title} className="card-image" />
      )}
      <div className="card-body">
        <h3 className="card-title">{product.title}</h3>
        {showPriceAsUnknown ? (
          <p className="card-price">Price: N/A – see Traya site for latest price</p>
        ) : (
          <p className="card-price">₹{product.price!.toFixed(2)}</p>
        )}
        {product.category && (
          <p className="card-category">{product.category}</p>
        )}
        {reason && <p className="card-reason">{reason}</p>}
        <Link to={`/products/${product.id}`} className="card-link">
          View details
        </Link>
      </div>
    </div>
  );
}


