## Phase 02 – Frontend + Running the Full System Locally

This document explains how the **frontend** is structured and exactly how to **run backend + frontend together** on your machine for the Traya product discovery assistant.

---

## 1. Frontend Overview (React + Vite)

All frontend code lives under `frontend/`:

- **`package.json`**
  - Scripts:
    - `"dev"` – runs the Vite dev server
    - `"build"` – production build
    - `"preview"` – preview built app
  - Dependencies:
    - `react`, `react-dom`
    - `react-router-dom`
  - Dev dependencies:
    - `vite`, `@vitejs/plugin-react-swc`, `typescript`, `@types/react`, `@types/react-dom`

- **`tsconfig.json`**
  - Standard TypeScript config for React + Vite.

- **`vite.config.ts`**
  - Uses the React SWC plugin.
  - Dev server runs on port **5173** by default.

- **`index.html`**
  - Root HTML shell with `<div id="root"></div>` and script loading `src/main.tsx`.

- **`src/main.tsx`**
  - Entry point:
    - Renders `<App />` inside `#root`.
    - Wraps app in `BrowserRouter` for URL-based routing.
    - Imports `styles.css` for styling.

- **`src/App.tsx`**
  - Top-level layout with:
    - Header + navigation:
      - `Home` → `/`
      - `Chat` → `/chat`
    - `Routes`:
      - `/` → `HomePage`
      - `/products/:id` → `ProductDetailPage`
      - `/chat` → `ChatPage`

---

## 2. Frontend API Client

All HTTP calls to the backend go through `src/api.ts`:

- **Base URL**

```ts
const DEFAULT_BASE_URL = "http://127.0.0.1:8001";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL;
```

- **Types**
  - `Product` – matches the backend `ProductRead` schema.
  - `ChatMessage` – `{ role: "user" | "assistant"; content: string }`.
  - `RecommendedProduct` – `{ product_id: number; reason: string }`.
  - `ChatResponse` – `{ reply: string; recommended_products: RecommendedProduct[] }`.

- **Functions**
  - `fetchProducts()` → `GET /products`
  - `fetchProduct(id)` → `GET /products/{id}`
  - `sendChat(messages)` → `POST /chat`

This keeps all backend URLs + types in one place and makes the React components simpler.

---

## 3. Pages and Components

### 3.1 `HomePage` – `/`

File: `src/pages/Home.tsx`

- On mount:
  - Calls `fetchProducts()` to get all products.
  - Shows loading and error states if needed.
- Layout:
  - Title: “Traya Products”
  - Subtitle describing the page.
  - Grid of `ProductCard` components.

### 3.2 `ProductDetailPage` – `/products/:id`

File: `src/pages/ProductDetail.tsx`

- Uses `useParams` to read `id` from URL.
- Calls `fetchProduct(Number(id))`.
- Shows:
  - Image, title, price, category.
  - Short description.
  - Features/benefits (formatted with line breaks).
  - Long description.
  - Link to the original Traya product URL.

### 3.3 `ChatPage` – `/chat`

File: `src/pages/Chat.tsx`

- Local state:
  - `input` – user text.
  - `messages: ChatMessage[]` – conversation history sent to backend.
  - `bubbles: { role; content; products? }[]` – used just for UI.
  - `loading`, `error`.
- Flow:
  1. User types a concern and submits.
  2. New user message is added to `messages` and `bubbles`.
  3. Calls `sendChat(messages)` to hit backend `/chat`.
  4. Backend returns `{ reply, recommended_products }`.
  5. For each recommendation:
     - Calls `fetchProduct(product_id)` to fetch full product info.
  6. Adds an assistant bubble with:
     - `content` = reply text.
     - `products` = list of `{ product, reason }`.
- UI:
  - Message bubbles for user (right) and assistant (left).
  - Recommended products shown as `ProductCard`s under the assistant bubble.

### 3.4 `ProductCard` component

File: `src/components/ProductCard.tsx`

- Props: `product: Product`, optional `reason: string`.
- Displays:
  - Image, title, price, category.
  - Optional “reason” text (e.g., “Targets dry, itchy scalp”).
  - “View details” link to `/products/{id}`.

---

## 4. Styling (Simple, Clean UI)

File: `src/styles.css`

- Global reset and dark background.
- Sticky header with nav links for `Home` and `Chat`.
- **Home**:
  - Responsive grid for product cards.
- **Product Detail**:
  - Two-column layout on desktop (image + text).
  - Stacks on mobile.
- **Chat**:
  - Chat window with:
    - Scrollable messages area.
    - Input row (text field + send button).
    - Distinct styles for user vs assistant bubbles.
    - Product cards grid under assistant responses.

The focus is on clarity and usability, not heavy design or animations.

---

## 5. Running Everything Locally (Step-by-Step)

### 5.1 Prerequisites

- **Python** (3.10 or similar) with `pip`.
- **Node.js + npm** (any recent LTS is fine).
- **Postgres.app** (for real PostgreSQL) – used during development.

Make sure:
- `backend/.env` exists with valid values (see `phase-01.md`).
- PostgreSQL server in Postgres.app is **Running**.

### 5.2 Start Backend

Open **Terminal 1**:

```bash
cd /Users/ashishasharma/Desktop/Neurasearch-AI/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Leave this terminal running. You should see:

- `Uvicorn running on http://127.0.0.1:8001`
- No error about Postgres connection (if Postgres.app is running and `DATABASE_URL` is correct).

Then open your browser at:

- `http://127.0.0.1:8001/docs`

Use Swagger UI to:

1. `POST /admin/scrape-traya` – scrape and store products.
2. `POST /admin/build-index` – build the vector index.
3. Optionally test `GET /products` and `POST /chat`.

### 5.3 Start Frontend

Open **Terminal 2**:

```bash
cd /Users/ashishasharma/Desktop/Neurasearch-AI/frontend
npm install
npm run dev
```

Vite will print a URL like:

```text
Local:   http://localhost:5173/
```

Open that URL in your browser.

If your backend is not on `http://127.0.0.1:8001`, set an env variable for Vite:

```bash
# in Terminal 2 before npm run dev
export VITE_API_BASE_URL="http://127.0.0.1:8001"
npm run dev
```

---

## 6. What You Can Demo

Once everything is running:

1. **Home Page (`/`)**
   - Shows a grid of Traya products scraped from the live site.
2. **Product Detail (`/products/:id`)**
   - Click any card → see title, price, category, benefits, long description, and link to Traya.
3. **Chat (`/chat`)**
   - Type queries like:
     - “I have a dry itchy scalp and thinning hair. What should I use?”
     - “My scalp is oily but I have mild hair fall.”
   - The assistant:
     - Responds as a hair & scalp advisor.
     - (Optionally) asks clarifying questions.
     - Shows recommended Traya products as cards with reasons.

This full flow demonstrates:
- End-to-end system from scraping → DB → vector index → RAG chat → React UI.
- Use of external APIs (OpenAI/Groq) and a vector DB (Chroma).
- Clean, simple UI and structure that you can explain easily in your interview.


