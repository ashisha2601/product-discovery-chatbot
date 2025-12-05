## Phase 06 – What to Demo & How to Talk About It

This phase is a short guide for your **interview demo** and how to
frame the project clearly.

---

### 1. Demo Script (2–3 minutes)

Suggested Loom / live demo flow:

1. **Home page (Vercel)**
   - Show `Traya Assistant` header and the grid of products.
   - Mention that these are **scraped from Traya.health** and stored in
     **PostgreSQL** on Render.

2. **Product detail**
   - Click any product.
   - Point out: title, price, category, benefits, long description,
     and “view on Traya” link.

3. **Chat**
   - Go to `/chat`.
   - First, show a generic query:
     - e.g. “hair growth” → assistant asks for clarification only.
   - Then a concrete query:
     - e.g. “I have dry, itchy scalp and my hair is thinning.”
     - Highlight:
       - Assistant summary of concerns.
       - The sentence “Based on your concerns, here are some Traya products
         that can help:”
       - Product cards with reasons under the bubble.
   - Finally, a safety question:
     - e.g. “I also have PCOS, is it fine to use it?”
     - Point out:
       - Clear, cautious answer and doctor disclaimer.
       - Products still recommended, but with emphasis on safety.

4. **Very quick architecture slide (optional)**
   - If you have 10–20 seconds, mention:
     - Scraper → Postgres → Chroma → LLM → React UI.

---

### 2. How to Map to the Assignment Requirements

Use wording close to the official spec
([Neusearch AI – AI Engineering Intern Technical Assignment](file:///Users/ashishasharma/Desktop/Neurasearch-AI/Neusearch%20AI%20%E2%80%93%20AI%20Engineering%20Intern%20Technical%20Assignment.pdf)):

- **Data collection pipeline**
  - Scrapes at least 25 Traya products with title, price, descriptions,
    features, image URL, category & extras.
  - Implemented as FastAPI admin endpoints.

- **Backend**
  - FastAPI + PostgreSQL + SQLAlchemy.
  - Clear schema, routers, and services structure.

- **Vectorisation + RAG**
  - Embeddings with OpenAI / Groq.
  - Vectors stored in Chroma.
  - Retrieval + LLM reasoning to interpret abstract queries and recommend
    products with explanations.

- **Frontend**
  - Simple ecommerce UI (Home, Product Detail, Chat) in React + Vite.

- **Deployment**
  - Backend on Render, frontend on Vercel, with proper environment variables.

---

### 3. How to Answer “What Would You Improve?”

You can reuse the points already summarised in `README.md`:

- Move from in‑memory Chroma to **pgvector** for persistent, SQL‑native search.
- Add more robust scraping (pagination, better category inference).
- Add **automated tests** around the RAG logic and scraping.
- Introduce simple **user accounts** or session tracking for more personalised
  recommendations.
- Add basic **observability** (logging of queries, retrieval metrics) to
  analyse which products are most often recommended.

This phase is mainly for you: it makes it easier to tell a clear story that
matches the assignment rubric when you submit the repo, live link, and Loom.


