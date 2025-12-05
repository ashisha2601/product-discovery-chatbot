## Phase 04 – Deployment & Environment Configuration

This phase documents how the project is deployed and which environment
variables are required in each environment.

---

### 1. Backend – Render Web Service

- **Platform**: Render (Web Service, Python 3).
- **Source**: GitHub repo root, `rootDir` set to `backend`.
- **Build command**:

  ```bash
  pip install -r requirements.txt
  ```

- **Start command**:

  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

- **Runtime**:
  - Python version pinned via:
    - `PYTHON_VERSION=3.11.9` (environment variable).
    - `backend/runtime.txt` as an extra hint.
  - Switched from `psycopg2-binary` to **psycopg3** (`psycopg[binary]`) so the
    app runs cleanly on newer Python versions, avoiding the
    `_PyInterpreterState_Get` import error.

#### 1.1 Backend Environment Variables (Render)

- `DATABASE_URL` – Render Postgres internal URL.
- `OPENAI_API_KEY` – key for Groq/OpenAI compatible API.
- `OPENAI_BASE_URL` – e.g. `https://api.groq.com/openai/v1`.
- `SEARCHAPI_API_KEY` – SearchApi.io key (for DuckDuckGo).
- `SEARCHAPI_BASE_URL` – `https://www.searchapi.io/api/v1/search`.
- `PYTHON_VERSION` – `3.11.9`.

The backend URL is:

```text
https://product-discovery-chatbot.onrender.com
```

---

### 2. Frontend – Vercel (Vite React App)

- **Platform**: Vercel, project imported from GitHub.
- **Root Directory**: `frontend`.
- **Framework preset**: **Vite** (so that `/chat` and other routes are handled
  by the SPA router, not as 404s).
- **Build command**: `npm run build`.
- **Output directory**: `dist`.

#### 2.1 Frontend Environment Variables (Vercel)

- `VITE_API_BASE_URL` – points to the Render backend:

  ```text
  VITE_API_BASE_URL=https://product-discovery-chatbot.onrender.com
  ```

This value is read in `src/api.ts` and used for all HTTP calls.

---

### 3. Dealing With Deployment Issues (What Was Fixed)

During deployment a few common issues showed up and were resolved:

1. **Python / psycopg2 compatibility on Render**
   - Render’s default Python 3.13 caused `psycopg2` to fail to import.
   - Fix:
     - Pin `PYTHON_VERSION=3.11.9`.
     - Migrate to `psycopg[binary]` (psycopg3) and update SQLAlchemy
       `create_engine` to use the `postgresql+psycopg` driver when the URL
       uses plain `postgresql://`.

2. **Chroma metadata `None` values**
   - Chroma rejects `None` values in metadata.
   - Fix:
     - Only add `category` to metadata when it is not `None`.

3. **Long‑running `/admin/build-index` on Render**
   - Building the ONNX embedding model and index can exceed frontend timeout
     limits, sometimes returning a 502 even though the work completes.
   - Fix/Decision:
     - Accept that `/admin/build-index` may occasionally show a 502 in Swagger,
       but the side‑effect (index built in memory) is still valid.
     - On first chat, the app falls back to DB products if the index is cold.

4. **CORS and “Failed to fetch” between Vercel and Render**
   - Fix:
     - Configure CORS in `backend/app/main.py` to allow all origins for
       simplicity in this assignment.
     - Ensure `VITE_API_BASE_URL` on Vercel points to the Render backend URL.

5. **Vercel 404s on `/chat` refresh**
   - SPA routing caused a 404 if the user refreshed on `/chat`.
   - Fix:
     - Set framework preset to **Vite** so Vercel routes all paths back to the
       built `index.html`, letting React Router handle the path.

---

### 4. What Production‑Like Aspects Are Covered

- Separate **backend** and **frontend** services.
- Environment variables for all secrets and environment‑specific configuration.
- Clean HTTP API boundary (`/products`, `/chat`, `/admin/*`).
- CORS configuration for cross‑origin traffic.
- Runtime pinned and dependencies selected for stability.

For a short summary suitable for the assignment form, you can say:

> Backend deployed on Render (FastAPI + PostgreSQL + Chroma + Groq/OpenAI),
> frontend deployed on Vercel (Vite React), with environment variables
> controlling API keys and cross‑service URLs.


