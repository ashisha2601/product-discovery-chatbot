const DEFAULT_BASE_URL = "http://127.0.0.1:8001";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL;

export interface Product {
  id: number;
  title: string;
  price?: number | null;
  short_description?: string | null;
  long_description?: string | null;
  features?: string | null;
  image_url?: string | null;
  category?: string | null;
  source_url?: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface RecommendedProduct {
  product_id: number;
  reason: string;
}

export interface ChatResponse {
  reply: string;
  recommended_products: RecommendedProduct[];
}

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch(`${API_BASE_URL}/products`);
  if (!res.ok) {
    throw new Error("Failed to fetch products");
  }
  return res.json();
}

export async function fetchProduct(id: number): Promise<Product> {
  const res = await fetch(`${API_BASE_URL}/products/${id}`);
  if (!res.ok) {
    throw new Error("Failed to fetch product");
  }
  return res.json();
}

export async function sendChat(
  messages: ChatMessage[]
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) {
    throw new Error("Chat request failed");
  }
  return res.json();
}


