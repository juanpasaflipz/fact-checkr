# Project Status & Roadmap

**Last Updated:** December 15, 2025

## 📍 Where We Are

We have successfully **refocused** the project to its original vision: a dual-purpose Intelligence System that monitors Mexican news/social media and informs users via WhatsApp and Web.

### ✅ Recent Accomplishments
*   **Core Logic Refocus**:
    *   **Dual-Mode Bot**: The WhatsApp agent now handles both **Specific Claims** (Fact-Checking) AND **General Topics** (News Summaries).
    *   **Input Restoration**: Validated that `TwitterScraper` and `GoogleNewsScraper` are correctly configured to feed the "Repository of Truth".
*   **Integration Complete**:
    *   **Environment**: All API keys (Twitter, Serper, OpenAI, Anthropic) are verified and active.
    *   **WhatsApp**: End-to-end flow works for Mexican numbers (`+52` normalization fixed).

### 2. WhatsApp Integration (Completed)
- [x] **Webhook Verification**: Confirmed `POST /api/whatsapp/webhook` receives data.
- [x] **Database Setup**: Created `whatsapp_users`, `whatsapp_messages`, `verdicts`, `evidence` tables.
- [x] **End-to-End Test**: Successfully received message, reviewed DB, and sent reply.
- [x] **News Query Support**: Added fallback logic to search Google News when no specific claim is found (e.g., "Noticias de Morena").
- [x] **AI Integration**: AI Keys are set; bot is "Brain-Enabled".
- [ ] **Proactive Educational Mode**: Develop the logic for "pre-bunking" misinformation.
- [ ] **Transparency Citations**: Add a footer to generated content showing sources.

---

## 🛠️ Environment & Setup Notes

### Running the App
1.  **Backend**:
    ```bash
    cd backend
    source venv/bin/activate
    uvicorn app.main:app --reload --port 8000
    ```
2.  **Frontend**:
    ```bash
    cd frontend
    npm run dev
    ```
3.  **Tunneling (for Webhooks)**:
    ```bash
    ngrok http 8000
    ```

### Key Directories
*   `backend/app/routers`: API endpoints (now includes `blog.py`, `share.py`).
*   `frontend/src/app/(marketing)`: Landing page routes.
*   `frontend/src/app/(app)`: Main application routes.
*   `backend/alembic/versions`: Database migration scripts.
