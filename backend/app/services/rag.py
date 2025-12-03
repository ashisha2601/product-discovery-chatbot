import json
from typing import List, Tuple

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.product import Product
from app.schemas.chat import ChatMessage, ChatResponse, RecommendedProduct
from app.services.embeddings import embed_text
from app.services.vectorstore import index_products, query_products
from app.services.safety import search_duckduckgo_side_effects


settings = get_settings()
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)

# When using Groq's OpenAI-compatible API, use one of their chat models.
# You can change this to any supported model name from your provider.
CHAT_MODEL = "llama-3.1-8b-instant"


def is_side_effect_question(text: str) -> bool:
    """
    Heuristic intent detection for safety / side‑effect questions.
    """
    t = text.lower()
    keywords = [
        "side effect",
        "side-effect",
        "side effects",
        "is it safe",
        "safe to use",
        "harmful",
        "allergy",
        "allergic",
        "contraindication",
        "interaction",
    ]
    return any(k in t for k in keywords)


def is_closing_message(text: str) -> bool:
    """
    Detect simple \"no more help\" / closing messages so we can just thank the
    user instead of recommending new products.
    """
    t = text.strip().lower()
    closers = [
        "no",
        "no thank you",
        "no thanks",
        "that's all",
        "that is all",
        "im fine",
        "i'm fine",
        "all good",
        "ok thanks",
        "okay thanks",
        "thank you",
        "thanks",
        "thankyou",
    ]
    return any(t == c or t.endswith(c) for c in closers)

def build_product_text(product: Product) -> str:
    """
    Build a rich text representation of a product for embeddings & context.
    """
    parts = [
        f"Title: {product.title}",
    ]
    if product.category:
        parts.append(f"Category: {product.category}")
    if product.price is not None:
        parts.append(f"Price: {product.price}")
    if product.short_description:
        parts.append(f"Short description: {product.short_description}")
    if product.features:
        parts.append(f"Key benefits and features: {product.features}")
    if product.long_description:
        parts.append(f"Details: {product.long_description}")
    return "\n".join(parts)


def index_all_products(db: Session) -> int:
    """
    Index all products from the database into the vector store.
    Returns the number of indexed items.
    """
    products: List[Product] = db.query(Product).all()
    items: List[Tuple[int, str, dict]] = []
    for p in products:
        text = build_product_text(p)
        # Chroma metadata values must be str/int/float/bool, not None
        metadata = {
            "product_id": p.id,
            "title": p.title,
        }
        if p.category is not None:
            metadata["category"] = p.category
        items.append((p.id, text, metadata))

    index_products(items)
    return len(items)


def retrieve_candidate_products(db: Session, query: str, top_k: int = 8) -> List[Product]:
    """
    Use the vector store to retrieve top-k similar products for the query.
    """
    result = query_products(query, top_k=top_k)
    ids = result.get("ids", [[]])[0]
    if not ids:
        return []
    int_ids = [int(pid) for pid in ids]
    products = db.query(Product).filter(Product.id.in_(int_ids)).all()

    # Preserve the order from Chroma
    ordered = {p.id: p for p in products}
    return [ordered[pid] for pid in int_ids if pid in ordered]


def run_rag_chat(db: Session, messages: List[ChatMessage]) -> ChatResponse:
    """
    Core RAG pipeline:
    - Take latest user query
    - Retrieve similar products
    - Ask OpenAI to respond with JSON containing reply + recommendations
    """
    user_messages = [m for m in messages if m.role == "user"]
    if not user_messages:
        return ChatResponse(reply="Please ask a question about your hair or scalp concerns.")

    latest_query = user_messages[-1].content

    # If the user is clearly closing the conversation (e.g. \"no\", \"thank you\"),
    # don't run retrieval or call the LLM – just send a friendly goodbye.
    if is_closing_message(latest_query):
        return ChatResponse(
            reply=(
                "You're welcome! I'm glad I could help. "
                "If you have any other hair or scalp concerns later, just come back and ask."
            ),
            recommended_products=[],
        )
    safety_intent = is_side_effect_question(latest_query)

    # Retrieve a larger pool so the model can pick a richer set of options.
    candidates = retrieve_candidate_products(db, latest_query, top_k=8)

    if not candidates:
        # Fallback: if vector search returns nothing (e.g., cold index),
        # use a simple text search over all products as a backup.
        all_products: List[Product] = db.query(Product).all()
        candidates = all_products[:5]

    # Build context string
    context_chunks = []
    for p in candidates:
        ctx = [
            f"Product ID: {p.id}",
            f"Title: {p.title}",
            f"Category: {p.category}",
        ]
        if p.price is not None:
            ctx.append(f"Price: {p.price}")
        if p.features:
            ctx.append(f"Benefits and features: {p.features}")
        if p.short_description:
            ctx.append(f"Summary: {p.short_description}")
        context_chunks.append("\n".join(ctx))

    context_text = "\n\n".join(context_chunks)

    # Optionally fetch extra safety / side‑effect information from DuckDuckGo
    safety_context = None
    if safety_intent:
        # Include both the user's wording and product names in the search query
        titles = ", ".join(p.title for p in candidates)
        search_query = f"{latest_query} {titles} side effects"
        safety_context = search_duckduckgo_side_effects(search_query)

    system_prompt = (
        "You are a careful, friendly hair & scalp care advisor for Traya.health products.\n"
        "You ONLY recommend from the candidate products I give you.\n"
        "\n"
        "Conversation guidelines:\n"
        "- First, briefly acknowledge and summarise the user's concerns in your own words.\n"
        "- Then clearly say something like: 'Based on your concerns, here are some Traya products that can help:'\n"
        "  before you describe any product recommendations, so the cards shown in the UI feel on-topic.\n"
        "- Always recommend 2–4 products by their Product ID with clear, specific reasons that connect to the\n"
        "  concerns mentioned (e.g. oily scalp, hair thinning, dandruff).\n"
        "- You must end by asking ONE short follow-up such as "
        "  'Do you have any other hair or scalp concerns you'd like to discuss?'\n"
        "  and this follow-up should come AFTER you describe the recommended products.\n"
        "- Do NOT repeat information the user has already clearly given (for example, if they already said they\n"
        "  have hair fall, don't ask again whether they have hair fall).\n"
        "- When the user asks about side effects or safety and extra web safety information is provided, use it\n"
        "  carefully: do not invent side effects, and be conservative. If information is uncertain, clearly say\n"
        "  you cannot provide medical advice and suggest consulting a doctor.\n"
        "\n"
        "Return your answer as pure JSON with this shape:\n"
        "{\n"
        '  \"reply\": \"string explanation to the user, including recommendations and an optional single\n'
        '            follow-up question at the end if needed\",\n'
        '  \"recommendations\": [\n'
        "    {\"product_id\": 123, \"reason\": \"short reason\"}\n"
        "  ]\n"
        "}\n"
        "Do not include any extra text outside the JSON."
    )

    prompt_context = (
        "Here are the candidate products you can choose from:\n\n"
        f"{context_text}\n\n"
        "User's latest query:\n"
        f"{latest_query}\n"
    )

    if safety_context:
        prompt_context += (
            "\nAdditional web safety / side-effect information from DuckDuckGo. "
            "Only use side effects or warnings that appear here; do not invent new ones:\n"
            f"{safety_context}\n"
        )

    openai_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_context},
    ]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=openai_messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: return plain reply
        return ChatResponse(
            reply="I'm sorry, I had trouble formatting my answer. "
            "Please try asking your question again.",
            recommended_products=[],
        )

    reply = data.get("reply", "")
    recs_raw = data.get("recommendations", [])

    recommendations: List[RecommendedProduct] = []
    for rec in recs_raw:
        try:
            pid = int(rec.get("product_id"))
            reason = str(rec.get("reason", ""))
        except (TypeError, ValueError):
            continue
        recommendations.append(RecommendedProduct(product_id=pid, reason=reason))

    return ChatResponse(reply=reply, recommended_products=recommendations)


