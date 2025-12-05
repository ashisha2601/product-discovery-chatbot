## Traya Product Discovery Assistant (Neurasearch AI Assignment)

An end‑to‑end **AI‑powered product discovery assistant** for **Traya.health** hair products.  
It can:

- Scrape real Traya products.
- Store them in **PostgreSQL**.
- Build a **vector index (Chroma)** over rich product text.
- Use a **RAG chatbot** to interpret abstract queries and recommend products.
- Answer basic **safety / side‑effect** questions using external web context.
- Expose a **React + Vite** ecommerce UI (Home, Product Detail, Chat).

This repo is designed to be easy to read for interviewers and to run locally.

---

## 1. Live Links

- **Frontend (Vercel)** – production UI  
  `https://product-discovery-gamma.vercel.app`  *(Home, Product Detail, Chat)*

- **Backend API (Render, FastAPI)**  
  `https://product-discovery-chatbot.onrender.com`
  - OpenAPI docs: `https://product-discovery-chatbot.onrender.com/docs`

> Note: On Render, the Chroma vector index is in‑memory. The index can be rebuilt
> at any time via `POST /admin/build-index` after scraping.

---

## 2. High‑Level Architecture

- **Backend (Python, FastAPI)**
  - `backend/app/main.py` exposes the FastAPI app with CORS enabled.
  - `backend/app/routers/*` define product, admin, and chat endpoints.
  - `backend/app/services/*` implement scraping, embeddings, vector store, RAG, and safety.

- **Database**
  - **PostgreSQL** via **SQLAlchemy** ORM (`backend/app/db/session.py`, `models/product.py`).
  - Stores normalized `Product` rows scraped from Traya.

- **Vector Store**
  - **Chroma EphemeralClient** in `backend/app/services/vectorstore.py`.
  - Stores embeddings for rich product texts built from title, benefits, descriptions, etc.

- **LLM & Embeddings**
  - Embeddings: OpenAI `text-embedding-3-small` via the `openai` Python SDK.
  - Chat: `llama-3.1-8b-instant` served behind an OpenAI‑compatible endpoint (Groq),
    used via `client.chat.completions.create(...)`.

- **Safety / Side‑Effects**
  - Lightweight **intent detection** identifies safety questions (e.g. “is it safe”, “is it fine
    with PCOS?”, “side effects”).
  - For safety queries, the backend calls **SearchApi.io** with the `duckduckgo` engine and feeds
    a short safety summary into the LLM with strict instructions not to invent side effects and to
    suggest consulting a doctor.

- **Frontend (React + Vite)**
  - Simple ecommerce UI in `frontend/src`:
    - `Home` – product grid pulled from `/products`.
    - `ProductDetail` – detailed view via `/products/{id}`.
    - `Chat` – conversation UI + product cards driven by `/chat`.

---

## 3. Data & RAG Pipeline

**1. Scraping Traya.health**

- Implemented in `backend/app/services/scraper_traya.py`.
- Steps:
  - Fetch `https://traya.health/collections/all`.
  - Collect unique `/products/...` links (up to a configurable limit).
  - For each product:
    - Parse title (`<h1>`), price (₹ text, best‑effort), meta description,
      paragraphs (`<p>`), list items (`<li>`), `og:image`, and a simple category heuristic.
    - Upsert into the `products` table using `Product` SQLAlchemy model.

**2. Database Schema**

`Product` includes:

- `id` (PK)
- `title`
- `price` (nullable float)
- `short_description`, `long_description`
- `features` (benefits / bullet points)
- `image_url`
- `category` (simple string like `shampoo`, `serum`, `supplement`)
- `source_url`
- `active_ingredient` (optional – used for future safety improvements)

**3. Vector Index (Chroma)**

- `index_all_products(db)` in `rag.py`:
  - Loads all products from Postgres.
  - Builds a rich text block per product (title, category, price, benefits, descriptions).
  - Calls `index_products()` to add them to a Chroma collection with metadata:
    - `product_id`, `title`, and (if present) `category`.

- `retrieve_candidate_products(db, query, top_k=8)`:
  - Queries Chroma for similar documents.
  - Fetches matching `Product` rows from Postgres and preserves ranking.
  - Falls back to a simple DB slice if the index is empty (cold start).

**4. Chat / RAG Logic**

Implemented in `backend/app/services/rag.py`:

1. Accepts a `ChatRequest` (`messages: ChatMessage[]`).
2. Extracts the latest **user** message.
3. Early exits:
   - If the message is a clear *closing* (“no thanks”, “that’s all”), returns a friendly goodbye
     with **no new products**.
   - If this is the **first message** and it’s extremely generic (e.g. “hair growth”, “recommend
     something” with no symptoms), returns only a **clarifying question** and no product cards.
4. Detects **safety intent** with a heuristic over phrases like:
   - “side effects”, “is it safe / ok / fine to use”, “interaction”, “PCOS”, “pregnant”, etc.
5. Retrieves candidate products via the vector store.
6. If `safety_intent` is `True`, calls `search_duckduckgo_side_effects()` to fetch an AI
   overview or a snippet from SearchApi.io (DuckDuckGo) using the user question + product titles.
7. Builds a system prompt that enforces:
   - Summarise the user’s concerns.
   - Clearly say **“Based on your concerns, here are some Traya products that can help:”** before
     listing products, so the cards feel on‑topic.
   - Recommend **2–4 products** by product ID with reasons tied to concerns.
   - Ask **exactly one** short follow‑up question **after** recommendations.
   - Don’t re‑ask information already given.
   - For safety: answer the safety question first, use safety context conservatively, and remind
     the user to consult a doctor; never invent side effects.
   - Return **pure JSON**:

   ```json
   {
     "reply": "string",
     "recommendations": [{ "product_id": 123, "reason": "short reason" }]
   }
   ```

8. Calls the chat model with `response_format={"type": "json_object"}` and converts the result into
   a `ChatResponse`:
   - `reply` – assistant message text.
   - `recommended_products` – list of `{ product_id, reason }` to drive the UI.

The frontend then fetches each `product_id` from `/products/{id}` and shows product cards under
the assistant message.

---

## 4. API Surface

All endpoints are under `https://product-discovery-chatbot.onrender.com` in production.

### Product APIs

- `GET /products`
  - Returns `ProductRead[]` for all scraped products.

- `GET /products/{id}`
  - Returns a single `ProductRead`.

### Admin APIs

- `POST /admin/scrape-traya`
  - Scrapes Traya.health and stores/updates products in Postgres.
  - Returns all products in the DB after scraping.

- `POST /admin/build-index`
  - Builds or refreshes the Chroma vector index from the current DB.
  - Returns the number of indexed products.
  - On Render this can return a **502** if the operation runs longer than the edge timeout;
    however the long‑running work will still complete and the index will be usable.

### Chat API

- `POST /chat`

Request body:

```json
{
  "messages": [
    { "role": "user", "content": "I have a dry itchy scalp and my hair is thinning." }
  ]
}
```

Response body:

```json
{
  "reply": "Natural language answer with explanation and one short follow-up.",
  "recommended_products": [
    { "product_id": 12, "reason": "Soothes dry, itchy scalp and supports density" },
    { "product_id": 7, "reason": "Targets hair fall and supports regrowth" }
  ]
}
```

---

## 5. Frontend UX

Key files in `frontend/src`:

- `App.tsx`
  - Header with **Home** and **Chat** links.
  - React Router setup:
    - `/` → `HomePage`
    - `/products/:id` → `ProductDetailPage`
    - `/chat` → `ChatPage`

- `pages/Home.tsx`
  - Fetches `GET /products`.
  - Shows a responsive grid of `ProductCard`s with title, price, image, category.

- `pages/ProductDetail.tsx`
  - Uses URL param `id` and fetches `GET /products/{id}`.
  - Shows full product details plus a link back to Traya.

- `pages/Chat.tsx`
  - Maintains `messages` array in the same shape as the backend.
  - For each user send:
    - Adds a user bubble.
    - Calls `sendChat(messages)` → `/chat`.
    - Displays the assistant `reply` as a green bubble.
    - Renders product cards (with reasons) beneath the assistant bubble.
  - The latest version:
    - Starts with **clarifying questions only** for very generic queries.
    - Handles safety questions (e.g. PCOS) with cautious language.

- `components/ProductCard.tsx`
  - Reusable product card with optional “reason” text.

- `src/api.ts`
  - Centralised REST client with:
    - `API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001"`.
  - Functions: `fetchProducts`, `fetchProduct`, `sendChat`.

- `styles.css`
  - Clean, light green theme (“Traya‑like”).
  - Responsive layout and mobile‑friendly chat UI.

> On Vercel, this is deployed as a static Vite app. `/chat` and other client‑side
> routes are handled via the SPA router.

---

## 6. Running Locally

### 6.1 Prerequisites

- Python **3.11** (matches Render runtime).
- Node.js (any recent LTS).
- PostgreSQL (e.g. Postgres.app on macOS).
- OpenAI‑compatible API key (e.g. Groq) for:
  - Embeddings `text-embedding-3-small`
  - Chat model `llama-3.1-8b-instant`
- Optional: SearchApi.io API key for DuckDuckGo safety lookups.

### 6.2 Backend Setup

Create `backend/.env`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DB_NAME
OPENAI_API_KEY=your-openai-or-groq-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
SEARCHAPI_API_KEY=your-searchapi-key   # optional but recommended
SEARCHAPI_BASE_URL=https://www.searchapi.io/api/v1/search
```

Install and run:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Visit `http://127.0.0.1:8001/docs` and:

1. `POST /admin/scrape-traya`
2. `POST /admin/build-index`

Then test `GET /products` and `POST /chat`.

### 6.3 Frontend Setup

```bash
cd frontend
npm install
# If your backend is not on the default URL, set:
export VITE_API_BASE_URL="http://127.0.0.1:8001"
npm run dev
```

Open `http://localhost:5173` in your browser.

Flow to test locally:

1. Home page shows scraped Traya products.
2. Clicking a card opens the Product Detail page.
3. Chat page:
   - Start with a generic query (“hair growth”) → bot should ask for clarification.
   - Provide a detailed concern (e.g. dry itchy scalp + thinning).
   - Try a safety question (“I also have PCOS, is it fine to use it?”) and observe
     the cautious answer + doctor disclaimer + product cards.

---

## 7. Deployment Setup

### 7.1 Backend – Render (Web Service)

- Root dir: `backend`
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Environment variables (Render → Environment):

```text
PYTHON_VERSION=3.11.9
DATABASE_URL=<Render internal Postgres URL>
OPENAI_API_KEY=<Groq/OpenAI key>
OPENAI_BASE_URL=https://api.groq.com/openai/v1
SEARCHAPI_API_KEY=<SearchApi.io key>
SEARCHAPI_BASE_URL=https://www.searchapi.io/api/v1/search
```

### 7.2 Frontend – Vercel

- Root directory: `frontend`
- Framework preset: **Vite**
- Build command: `npm run build`
- Output directory: `dist`
- Environment variables:

```text
VITE_API_BASE_URL=https://product-discovery-chatbot.onrender.com
```

After deployment, the frontend talks to the Render backend just like in local dev.

---

## 8. Trade‑offs, Edge Cases & Improvements

**Key trade‑offs / decisions**

- **Ephemeral Chroma index** on Render:
  - Keeps deployment simple; `/admin/build-index` (or the first chat) can rebuild the index.
- **Heuristic scraping**:
  - HTML structure is lightly parsed; robust enough for the assignment but not production‑grade.
- **Heuristic intent detection** for safety and closers:
  - Keeps the logic transparent and debuggable without another ML model.

**Edge cases handled**

- CORS configured to allow the Vercel frontend.
- Chroma metadata avoids `None` values to prevent runtime errors.
- Graceful fallback when the vector index is empty or `build-index` times out.
- Simple “goodbye” detection to avoid spamming users with more products.

**If I had more time, I would…**

- Use **pgvector** in Postgres instead of an in‑memory Chroma for persistence.
- Add **user session history** so the model can reference earlier turns more reliably.
- Improve scraping robustness (pagination, better category extraction, price parsing).
- Add **tests** around RAG pieces (retrieval quality, prompt behaviours).
- Add basic **rate limiting & auth** around admin/scraping endpoints.
- Explore streaming responses in the chat UI for a more “live” feel.

For a deeper dive into each phase, see:

- `phase-01.md` – backend architecture, scraping, and RAG.
- `phase-02.md` – frontend structure and local run instructions.


