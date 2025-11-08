## Copilot instructions — Unified Cloud Storage

Quick reference to help an AI coding agent become productive in this repo.

- Architecture: backend (FastAPI) lives in `backend/` (entry: `main.py`, `app.py`). Frontend is a React app in `frontend/` (entry: `src/index.js`, config in `src/config.js`). DB models and provider adapters are under `backend/models.py` and `backend/storage_providers/`.

- Key flows to know:

  - OAuth/connect flow: `backend/main.py` -> `initiate_auth` and `auth_callback`. Provider-specific configs are in `backend/config.py` (see `PROVIDER_CONFIGS` keys like `google_drive_full_access` and `google_drive_metadata_only`).
  - Sync pipeline: `sync_account_files` in `backend/main.py` fetches provider files (provider class implements `list_files`) and writes `FileMetadata` records. Prefer marking files inactive rather than deleting.
  - Duplicate detection: uses `FileMetadata.content_hash` and `size_hash` (see `backend/models.py`). Grouping happens in `/api/duplicates`.

- Developer workflows / commands (Windows PowerShell):

  - Backend dev (create venv, install, run):
    ```powershell
    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python main.py     # or: uvicorn main:app --reload --port 8000
    ```
  - Frontend dev:
    ```powershell
    cd frontend
    npm install
    npm start
    ```
  - Initialize DB if needed:
    ```powershell
    cd backend
    python -c "from backend.database import engine, Base; Base.metadata.create_all(bind=engine)"
    ```

- Project-specific conventions and patterns:

  - Two account modes: `metadata` vs `full_access` (user `mode` on `User` and `mode` on `StorageAccount`). Many endpoints enforce behavior by checking `storage_account.mode`.
  - Provider configs are mode-aware (keys use pattern `{provider}_{metadata_only|full_access}` in `PROVIDER_CONFIGS`). When adding a provider, add entries there and new env vars in `.env`.
  - Tokens are encrypted before storage via a security util (see `backend/utils.py` usage in `main.py`). Avoid logging raw tokens; note that some debug prints exist and should not be expanded.
  - Background tasks: long-running operations (sync) are scheduled with FastAPI `BackgroundTasks` and should be idempotent and safe to retry.

- Integration points to inspect before edits:

  - `backend/storage_providers/` — implement the provider class methods: `get_authorization_url`, `exchange_code_for_token`, `get_user_info`, `list_files`, `delete_file`, `get_preview_link`.
  - `backend/config.py` — central place for settings and PROVIDER_CONFIGS. Update env var names here when adding providers.
  - `frontend/src/config.js` — API base URL and provider list used by UI components; keep it in sync with backend ports.

- Quick examples of common edits:

  - To add a new provider: add `backend/storage_providers/newprovider.py`, register class in `storage_providers.__init__`, add `PROVIDER_CONFIGS` entry in `backend/config.py`, and add env vars in `.env`.
  - To change OAuth redirect URLs: update `backend/config.py` PROVIDER_CONFIGS redirect_uri and corresponding env var, and update the OAuth app settings at provider console.

- Where tests & builds live:

  - Frontend: `npm test` (React scripts). `npm run build` for production bundle.
  - Backend: minimal test scaffolding exists; run `pytest` from repo root if tests are added.

- Safety notes for agents:
  - Do not commit secrets or API keys. Look for values in `backend/config.py` that reference `.env` — update `.env` instead of hardcoding.
  - Search for `print` or `logger.debug` lines that leak tokens (e.g., in `main.py`), and avoid copying those values into patches.

Reference files: `README.md`, `backend/main.py`, `backend/app.py`, `backend/config.py`, `backend/models.py`, `backend/storage_providers/`, `frontend/src/config.js`, `frontend/package.json`.

If anything is unclear or you want more details (examples of a provider class, DB schema notes, or common PR checklist), tell me which area to expand and I will update this file.
