# Project Status & Roadmap

**Last Updated:** December 15, 2025

## 📍 Where We Are

We are currently in **Phase 2** of development, focusing heavily on the **WhatsApp Integration** for the FactChecker MX platform.

### ✅ Recent Accomplishments
*   **Frontend UI**: 
    *   Implemented the WhatsApp Admin Dashboard (`/admin/whatsapp`).
    *   Created the Chat View for individual users (`/admin/whatsapp/[userId]`).
    *   Added Spanish translations and improved styling (Tailwind CSS) for a better UX.
    *   Added manual "Refresh" capabilities for the user list.
*   **Backend**:
    *   Established basic endpoint structure for `users` and `messages`.
    *   Addressed initial CORS and connection issues.
    *   Updated `VerificationStatus` Enum in the database models.

### 🚧 Current Focus
*   **Connecting the Pipes**: We are currently ensuring the local backend (exposed via `ngrok`) correctly receives and processes real-time webhooks from the WhatsApp Business API.
*   **Database Migrations**: Refined the Alembic migration scripts to correctly handle Enum changes for `VerificationStatus`.

---

## 📋 To-Do & Next Steps

### 1. WhatsApp Webhook Verification
- [ ] **Verify Webhook Reception**: Confirm that `POST /api/v1/whatsapp/webhook` correctly receives data from Meta.
- [ ] **Signature Verification**: Ensure `verify_signature` (or similar middleware) is active and securing the webhook endpoint.
- [ ] **End-to-End Test**: Send a message from a real WhatsApp account -> Webhook -> DB -> Frontend Admin View.

### 2. Async Processing & Reliability
- [ ] **Celery Tasks**: Harden the `process_message` task in `backend/app/tasks/whatsapp.py`.
- [ ] **Retries**: Configure automatic retries for transient failures (e.g., network blips).
- [ ] **Idempotency**: Implement checks to ensure the same message ID isn't processed twice.

### 3. Database & Quality Assurance
- [ ] **Migration Verification**: Double-check that `7fecb6e4b649_update_verification_status_enum.py` has been applied successfully to the production/staging DB without data loss.
- [ ] **Unit Tests**: Create tests for the WhatsApp message parsing logic.

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
    *Important*: Update the Callback URL in the [Meta Developers Portal](https://developers.facebook.com/) whenever the ngrok URL changes.

### Key Directories
*   `backend/app/routers/whatsapp.py`: Main API endpoints.
*   `frontend/src/app/admin/whatsapp`: Frontend admin pages.
*   `backend/alembic/versions`: Database migration scripts.
