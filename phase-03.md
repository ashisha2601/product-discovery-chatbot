## Phase 03 – Retrieval, Safety & Chat Behaviour

This phase explains the **RAG behaviour and safety logic** that sits between the raw
vector search and the final chat response.

---

### 1. Retrieval Strategy

- **Vector store**: Chroma `EphemeralClient` in `backend/app/services/vectorstore.py`.
- **Indexing**:
  - `index_all_products(db)` builds a rich text representation per product
    (title, category, price, short + long descriptions, features).
  - Each product is stored with metadata `product_id`, `title`, and `category` (when present).
- **Querying**:
  - `retrieve_candidate_products(db, query, top_k=8)`:
    - Calls Chroma `query()` to get nearest neighbours.
    - Loads the corresponding `Product` rows from Postgres.
    - Preserves Chroma’s ranking order.
  - If the index is empty (e.g. first boot, or `build-index` hasn’t run),
    it falls back to a simple slice of products from the DB so the chat
    endpoint never fully breaks.

---

### 2. Safety & Intent Detection

Inside `backend/app/services/rag.py`:

- **Closing detection** – `is_closing_message(text)`:
  - Matches simple “no / no thanks / that’s all / ok thanks / thank you”.
  - If triggered, the chatbot returns a friendly goodbye and **no new products**.

- **Safety detection** – `is_side_effect_question(text)`:
  - Looks for:
    - “side effect(s)”, “is it safe / ok / fine to use”, “harmful”, “allergy”,
      “contraindication”, “interaction”.
  - Also treats condition + usage questions as safety intent:
    - Mentions of **PCOS, pregnancy, blood pressure, diabetes, thyroid**, etc.
    - Combined with verbs like “use, take, have, apply” and a question mark.

- **Generic‑query clarification** – `needs_clarification_first(text)`:
  - If the **first** user message is very short and generic
    (e.g. “hair growth”, “recommend something for hair”) and doesn’t mention
    a clear symptom, the bot:
    - Sends only a **clarifying question**.
    - Does **not** show any product cards yet.

These heuristics give predictable, interview‑friendly behaviour without
adding another ML model.

---

### 3. External Safety Context (DuckDuckGo via SearchApi.io)

For safety questions:

1. The backend constructs a search query combining:
   - The **user’s wording**, and
   - The **titles of candidate products**.
2. It calls `search_duckduckgo_side_effects(query)` in
   `backend/app/services/safety.py`:
   - Uses SearchApi.io’s `duckduckgo` engine.
   - Prefers the AI overview text when available, else the first organic snippet.
3. The returned snippet (if any) is injected into the LLM prompt as
   `safety_context` with strict instructions:
   - Only use concrete side‑effect information that appears in this snippet.
   - Never invent or guess side effects.
   - Always remind the user to consult a doctor for medical conditions.

This keeps the RAG pipeline focused on **product discovery**, but still lets the
assistant answer “is it safe with PCOS?” type questions responsibly.

---

### 4. Prompt Design & JSON Contract

- **Base prompt**:
  - The model is a **Traya hair & scalp advisor**.
  - It may only recommend from the **candidate products** provided.
  - It must:
    - Acknowledge and summarise the user’s concerns.
    - Clearly say **“Based on your concerns, here are some Traya products that can help:”**
      before listing products (so the UI cards feel on‑topic).
    - Recommend **2–4 products** with reasons tied to the concerns.
    - Ask **one** short follow‑up question at the end (after recommendations).
    - Avoid re‑asking information already given.

- **Safety prompt extension** (when `safety_intent=True`):
  - Answer the **safety question first** in cautious language.
  - Use `safety_context` conservatively; no invented side effects.
  - Always add a doctor disclaimer for conditions such as PCOS or pregnancy.

- **JSON‑only response**:
  - The LLM is forced to return:

    ```json
    {
      "reply": "string",
      "recommendations": [{ "product_id": 123, "reason": "short reason" }]
    }
    ```

  - This keeps the backend → frontend contract simple:
    - `reply` renders as a message bubble.
    - `recommended_products` drive additional `/products/{id}` fetches and cards.

Together, these choices make the chatbot’s behaviour **predictable**, easy to
demo, and clearly aligned with the assignment requirements in the Neusearch
specification.


