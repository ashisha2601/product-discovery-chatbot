import { FormEvent, useState } from "react";
import { sendChat, type ChatMessage, type ChatResponse, fetchProduct, type Product } from "../api";
import { ProductCard } from "../components/ProductCard";

type Bubble = {
  role: "user" | "assistant";
  content: string;
  products?: { product: Product; reason: string }[];
};

export function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    const newUserMessage: ChatMessage = { role: "user", content: trimmed };
    const newMessages = [...messages, newUserMessage];

    setMessages(newMessages);
    setBubbles((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await sendChat(newMessages);

      // Fetch product details for recommendations
      const recommendedProducts: { product: Product; reason: string }[] = [];
      for (const rec of response.recommended_products) {
        try {
          const prod = await fetchProduct(rec.product_id);
          recommendedProducts.push({ product: prod, reason: rec.reason });
        } catch {
          // Ignore missing products
        }
      }

      setBubbles((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.reply,
          products: recommendedProducts,
        },
      ]);

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.reply },
      ]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-layout">
      <div>
        <h1>Traya Hair & Scalp Assistant</h1>
        <p className="subtitle">
          Ask about hair fall, dry scalp, dandruff, or density. The assistant will
          recommend Traya products based on your concerns.
        </p>
      </div>

      <div className="chat-window">
        {bubbles.length === 0 && (
          <p className="status">
            Start by telling me about your hair or scalp concerns.
          </p>
        )}

        <div className="chat-messages">
          {bubbles.map((b, idx) => (
            <div
              key={idx}
              className={
                b.role === "user" ? "chat-bubble chat-bubble-user" : "chat-bubble chat-bubble-bot"
              }
            >
              <p>{b.content}</p>
              {b.products && b.products.length > 0 && (
                <div className="chat-products">
                  {b.products.map((p, i) => (
                    <ProductCard
                      key={`${p.product.id}-${i}`}
                      product={p.product}
                      reason={p.reason}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {error && <p className="status error">Error: {error}</p>}

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Describe your hair/scalp issue..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}


