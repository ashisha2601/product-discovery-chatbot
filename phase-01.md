## Phase 01 – Backend (Traya Product Discovery Assistant)

This document explains **everything implemented so far for the backend**, focused on Traya.health hair-care products. It covers architecture, files, data flow, and how to run and test the backend on your machine.

---

## 1. High-Level Overview

- **Goal**: Build a backend that can:
  - **Scrape** real products from **Traya.health**
  - **Store** them in **PostgreSQL**
  - **Index** them in a **vector store (Chroma)**
  - **Answer chat queries** about hair/scalp concerns using **RAG + OpenAI**
- **Tech stack (backend)**:
  - **FastAPI** – web framework
  - **PostgreSQL** – main database
  - **SQLAlchemy** – ORM for schema and queries
  - **ChromaDB** – local vector database
  - **OpenAI** – embeddings + chat LLM
  - **Pydantic** / **pydantic-settings** – validation and config
  - **httpx + BeautifulSoup** – scraping Traya.health

Current phase: **Backend foundations + scraping + RAG pipeline** are implemented and runnable.

---

## 2. Backend Folder Structure

All backend code lives under `backend/`:

- **`backend/requirements.txt`**
  - Python dependencies for the backend:
    - `fastapi`, `uvicorn[standard]`
    - `SQLAlchemy`, `psycopg2-binary`
    - `pydantic`, `pydantic-settings`
    - `httpx`, `beautifulsoup4`
    - `openai`, `chromadb`, `orjson`

- **`backend/app/main.py`**
  - Creates the FastAPI app via `create_app()`.
  - Adds **CORS** middleware to allow frontend access (e.g. `http://localhost:5173`).
  - This is the entrypoint for `uvicorn` (`app.main:app`).

- **`backend/app/__init__.py`**
  - Defines `create_app()`:
    - Creates `FastAPI()` instance
    - Includes routers:
      - `products` → `/products`
      - `chat` → `/chat`
      - `admin` → `/admin`

- **`backend/app/core/config.py`**
  - Defines `Settings` using `pydantic-settings`:
    - `database_url` (Postgres connection string)
    - `openai_api_key` (OpenAI Secret Key)
    - `chroma_path` (folder path where Chroma stores vectors, default `./chroma_db`)
    - `cors_origins` (optional list of allowed origins)
  - Loads values from `.env` file in `backend/` directory.
  - Provides `get_settings()` (cached config).

- **`backend/app/db/session.py`**
  - Sets up **SQLAlchemy**:
    - `Base` – declarative base for models
    - `engine` – created from `settings.database_url`
    - `SessionLocal` – session factory
    - `get_db()` – FastAPI dependency that yields a DB session and closes it after use

- **Models (`backend/app/models/`)**
  - `product.py`:
    - `Product` SQLAlchemy model with columns:
      - `id` – primary key
      - `title` – product name
      - `price` – optional float
      - `short_description` – optional text
      - `long_description` – optional text
      - `features` – optional text (benefits, key points, list items)
      - `image_url` – optional string (up to 512 chars)
      - `category` – optional string (e.g. shampoo, serum)
      - `source_url` – original Traya product URL
  - `__init__.py` exports `Product`.

- **Schemas (`backend/app/schemas/`)**
  - `product.py`:
    - `ProductBase` – shared fields for product
    - `ProductCreate` – same as base (for future inserts)
    - `ProductRead` – adds `id`, used in API responses
  - `chat.py`:
    - `ChatMessage` – `{ role: "user" | "assistant", content: string }`
    - `ChatRequest` – `{ messages: ChatMessage[] }`
    - `RecommendedProduct` – `{ product_id: int, reason: string }`
    - `ChatResponse` – `{ reply: string, recommended_products: RecommendedProduct[] }`
  - `__init__.py` re-exports schema classes.

- **Routers (`backend/app/routers/`)**
  - `products.py`:
    - Ensures DB tables exist (`Base.metadata.create_all(bind=engine)`).
    - `GET /products` – list all products from DB.
    - `GET /products/{product_id}` – get a single product by ID.
  - `admin.py`:
    - `POST /admin/scrape-traya`:
      - Calls Traya scraper, stores products in DB.
      - Returns all products.
    - `POST /admin/build-index`:
      - Builds or refreshes the vector index in Chroma from all products.
      - Returns number of indexed products.
  - `chat.py`:
    - `POST /chat`:
      - Accepts `ChatRequest`.
      - Calls `run_rag_chat()` (RAG pipeline).
      - Returns `ChatResponse`.

- **Services (`backend/app/services/`)**
  - `scraper_traya.py`:
    - Knows how to scrape Traya.health.
    - Steps:
      - Fetches `https://traya.health/collections/all` to get product links.
      - For each `/products/...` link (up to a limit):
        - Downloads product page.
        - Parses:
          - **Title** (from `<h1>`)
          - **Price** (best-effort using text with `₹`)
          - **Short description** (meta `description`)
          - **Long description** (all paragraphs)
          - **Features/benefits** (all list items)
          - **Image URL** (meta `og:image`)
          - **Category** (simple heuristics: shampoo/serum/supplement)
        - Creates and saves a `Product` row if not already present for that URL.
  - `embeddings.py`:
    - Uses **OpenAI** to generate embeddings:
      - Model: `text-embedding-3-small`
      - `embed_text(text: str) -> List[float]`
  - `vectorstore.py`:
    - Sets up a **persistent Chroma** client:
      - Path from `settings.chroma_path`
      - Collection name: `traya_products`
    - Functions:
      - `index_products(items)`:
        - Input: list of `(product_id, text, metadata)` triples.
        - Adds them to Chroma as documents.
      - `query_products(query, top_k)`:
        - Performs similarity search over the collection.
  - `rag.py`:
    - Central **RAG pipeline** for chat.
    - `build_product_text(product)`:
      - Combines title, category, price, descriptions, features into a single rich text.
    - `index_all_products(db)`:
      - Loads all `Product`s from DB.
      - Builds text and metadata for each.
      - Calls `index_products` to add to Chroma.
    - `retrieve_candidate_products(db, query, top_k)`:
      - Uses `query_products` to get similar product IDs.
      - Fetches corresponding `Product` rows from DB.
    - `run_rag_chat(db, messages)`:
      - Extracts latest user query from `messages`.
      - Retrieves top candidate products from vector store.
      - Constructs a **system prompt**:
        - You are a hair & scalp advisor.
        - Only recommend from given products.
        - Ask 1–2 clarifying questions if needed.
        - Return **pure JSON**:
          - `{ "reply": string, "recommendations": [{ "product_id": number, "reason": string }] }`
      - Calls OpenAI chat model (`gpt-4.1-mini`).
      - Parses JSON and returns a `ChatResponse` with:
        - `reply`: natural language response to show to user.
        - `recommended_products`: structured `product_id` + `reason` list.

---

## 3. Environment Setup

Create a `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/YOUR_DB_NAME
OPENAI_API_KEY=sk-your-openai-api-key
CHROMA_PATH=./chroma_db
```

- **`DATABASE_URL`**:
  - Must point to a running **PostgreSQL** instance.
  - Example for local Postgres:
    - User: `postgres`
    - Password: `password`
    - DB name: `neurasearch`
  - Then:
    ```env
    DATABASE_URL=postgresql://postgres:password@localhost:5432/neurasearch
    ```
- **`OPENAI_API_KEY`**:
  - Your OpenAI secret key for embeddings + chat.
- **`CHROMA_PATH`**:
  - Folder where Chroma will store vector data (will be created if missing).

---

## 4. How to Install and Run the Backend

From the project root:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- This starts the server at `http://127.0.0.1:8000`.
- Open the automatic documentation:
  - `http://127.0.0.1:8000/docs`

---

## 5. Using the Admin Endpoints (Scraping + Indexing)

Use Swagger UI at `http://127.0.0.1:8000/docs` or any REST client (Postman, curl, etc).

### 5.1 Scrape Traya Products

- **Endpoint**: `POST /admin/scrape-traya`
- **What it does**:
  - Requests Traya’s collection page.
  - Extracts links to individual product pages.
  - Scrapes each product and stores it in the `products` table.
  - Skips duplicates based on `source_url`.
  - Returns the list of all products currently in DB.

### 5.2 Build Vector Index

- **Endpoint**: `POST /admin/build-index`
- **What it does**:
  - Loads all products from DB.
  - Builds a text representation (title, benefits, descriptions, etc.).
  - Indexes them into the Chroma collection.
  - Returns how many products were indexed.

You should **always run**:

1. `POST /admin/scrape-traya` (once or occasionally to refresh data)
2. `POST /admin/build-index` (after scraping or updating products)

before using `/chat`.

---

## 6. Product APIs (for Frontend)

These are used by the future React frontend:

- **`GET /products`**
  - Returns list of all products.
  - Response: `ProductRead[]`:
    - `id, title, price, short_description, long_description, features, image_url, category, source_url`

- **`GET /products/{product_id}`**
  - Returns a single product by ID.
  - Used on **Product Detail** page.

---

## 7. Chat API (RAG over Traya Products)

- **`POST /chat`**
  - Request body (`ChatRequest`):

    ```json
    {
      "messages": [
        { "role": "user", "content": "I have a dry itchy scalp and my hair is thinning. What should I use?" }
      ]
    }
    ```

  - Logic:
    - Takes the latest **user** message.
    - Uses Chroma to retrieve similar products for that query.
    - Calls OpenAI chat model with:
      - System prompt: hair & scalp advisor, only recommend Traya products, ask clarifying questions if needed.
      - Candidate product details.
      - User query.
    - Forces **JSON-only** response (`response_format={"type": "json_object"}`).
    - Parses JSON to extract:
      - `reply` – the full answer for the user (includes explanation and possible clarifying questions).
      - `recommendations` – list of `{ "product_id", "reason" }`.

  - Response (`ChatResponse`):

    ```json
    {
      "reply": "Your scalp sounds dry and itchy, which can be a sign of dandruff or irritation. I recommend ...",
      "recommended_products": [
        { "product_id": 12, "reason": "Targets dryness and soothes itchy scalp" },
        { "product_id": 7, "reason": "Helps with hair density over time" }
      ]
    }
    ```

The frontend will:
- Show `reply` as **message bubbles**.
- Use `recommended_products` list to fetch full details (`GET /products/{id}`) and render **product cards**.

---

## 8. What Comes Next (Future Phases)

Next steps (not yet implemented in this phase-01 file, but planned):

- **Frontend (React + Vite)**:
  - Home page (list products from `/products`).
  - Product detail page (`/products/:id`).
  - Chat page (`/chat`) with message bubbles and product cards.
- **Deployment**:
  - Backend + Postgres on Render/Railway.
  - Frontend on Vercel.
  - Proper `.env` and environment variables in both environments.
- **Docs & Demo**:
  - Main `README.md` explaining architecture, scraping, RAG.
  - Loom video walking through Home → Product Detail → Chat.

This `phase-01` document is focused only on the **backend foundation + scraping + RAG pipeline**, which is now ready for you to run locally and connect to a frontend.


