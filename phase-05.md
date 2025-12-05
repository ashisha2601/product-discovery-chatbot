## Phase 05 – Product Thinking & Chat UX

This phase focuses on **how the assistant feels** to a user, rather than
just the raw tech.

---

### 1. Target User Experience

The assistant should feel like:

- A **Traya hair coach** that:
  - Understands hair/scalp concerns.
  - Explains *why* a product is relevant.
  - Doesn’t ask the same question twice.
- A simple ecommerce flow:
  - Browse all products.
  - Deep dive on a product.
  - Ask a human‑style question and get tailored product ideas.

The assignment brief emphasises **abstract queries** like:

- “I have a dry scalp. What products can improve my hair density?”
- “Looking for something I can wear in the gym and also in meetings.”  
  (analogy used in the spec as a general example of nuanced intent).

The RAG + prompt design aim to map these open‑ended concerns onto concrete
Traya SKUs and a clean visual explanation.

---

### 2. Chat Flow Decisions

Key UX decisions in the chat behaviour:

- **Clarification before cards**:
  - If the first message is extremely generic (“hair growth”), the bot *only*
    asks a clarifying question.
  - No product cards appear yet, so the UI doesn’t feel random.

- **Explicit connection between text and cards**:
  - The system prompt forces a line such as:
    - “Based on your concerns, here are some Traya products that can help:”
  - This appears immediately before the products used for cards, so users
    always understand why cards showed up.

- **Exactly one follow‑up**:
  - To keep the flow crisp, the bot always ends with **one** short follow‑up
    question, after recommendations.
  - This mirrors a human consultant: recommend first, then check if there are
    any extra concerns.

- **Goodbye handling**:
  - When users say “no thanks / that’s all / ok thanks”, the bot replies with a
    short thank‑you and **no additional products**, avoiding awkward restarts.

---

### 3. Safety Queries & Trust

For questions like:

- “I also have PCOS, is it fine to use it?”

The assistant:

1. Detects safety intent via keywords + medical condition mentions.
2. Pulls in a short web safety snippet (SearchApi.io + DuckDuckGo).
3. Answers the **safety concern first**, before talking about products.
4. Clearly states:
   - It can’t provide medical advice.
   - The user should consult their doctor for conditions such as PCOS.

This balances product discovery with user trust and aligns with expectations
in a real product environment.

---

### 4. Frontend UX Choices

- **Colour scheme**:
  - Very light green backgrounds and dark “Traya‑like” green headers/buttons,
    making the interface feel calm and aligned with a wellness brand.

- **Layout**:
  - Desktop: wide content area with clean spacing.
  - Mobile: stacked cards and full‑width chat bubbles.

- **Chat**:
  - Messages have clear left (assistant) vs right (user) alignment.
  - Product cards are visually grouped under the assistant’s reply to show
    that they belong to that explanation.

The goal is **clarity and readability** over flashy design, as requested in
the assignment brief.


