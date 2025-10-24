# Encrypted Scratchpad

A zero-knowledge scratch pad for ferrying snippets between machines when the clipboard can’t follow. Ten independent sessions encrypt entirely in the browser; the backend only ever stores ciphertext.

## Features
- Ten named sessions with auto-generated 40-bit encryption keys (two random words + 5 digits)
- AES-GCM (256-bit) with PBKDF2 (100k iterations) derivation via the Web Crypto API
- Auto-save, inactivity locking, and persistent save timestamps
- Basic-auth admin console for resetting individual or all sessions

## Tech Stack
- **Frontend:** Vanilla HTML/CSS/JS (no build step, Web Crypto + Fetch API)
- **Backend:** Flask + Flask-CORS persisting encrypted blobs to a JSON file (file locking included)
- **Reverse Proxy:** nginx (or similar) for serving static assets and gating `/api/cache*/reset` endpoints with dedicated Basic Auth

## Repository Layout
```
backend/
  app.py                  # Flask API (sessions, storage, admin resets)
  reset_cache_session.py  # CLI helper for scripted resets
  requirements.txt        # Python dependencies
web/
  index.html              # Session picker UI
  session.html            # Encryption editor UI
  admin.html              # Basic-auth admin console
README.md
```

## Getting Started
1. Clone and install backend dependencies:
   ```bash
   git clone git@github.com:dillweed/encrypted-scratchpad.git
   cd encrypted-scratchpad/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   FLASK_APP=app.py flask run --host 0.0.0.0 --port 8000
   ```
2. Serve the static frontend (same origin keeps relative `/api` calls working):
   ```bash
   cd ../
   python3 -m http.server 8080 --directory web
   ```
3. Open `http://localhost:8080/index.html`, create a session, copy the displayed encryption key, and start editing. The admin console is available at `/admin.html`—protect that path with Basic Auth in production.

## Deployment Notes
- Point your reverse proxy at `web/` for static files and forward `/api/` to the Flask backend.
- Use a dedicated htpasswd file (e.g., user `cache-admin`) for `/cache-admin/reset-all` and `/cache/<id>/reset` requests.
- Back up the generated `cache_data.json`; without the encryption key the stored data cannot be recovered.
