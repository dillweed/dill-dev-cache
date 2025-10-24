# dill.dev/cache

A zero-knowledge scratch pad for moving snippets between machines when the clipboard can’t follow. Ten independent sessions encrypt in the browser; the server only sees ciphertext.

## Features
- Ten named sessions with auto-generated 40-bit encryption keys (two words + 5 digits)
- AES-GCM (256-bit) with PBKDF2 (100k iterations) key derivation, implemented via the Web Crypto API
- Auto-save, inactivity locking, and persistent status timestamps
- Admin console (`/cache/admin.html`) protected by Basic Auth for one-click session resets

## Tech Stack
- **Frontend**: Vanilla HTML, CSS, and JavaScript (Web Crypto API, Fetch)
- **Backend**: Flask + Flask-CORS (approx. 200 LOC) persisting encrypted blobs to a JSON file
- **Ops**: nginx serves static assets and gates admin endpoints with a dedicated Basic Auth user

## Project Layout
```
backend/
  app.py                  # Flask API (JSON storage + reset endpoints)
  order_calculations.py   # Legacy utility (kept for completeness)
  reset_cache_session.py  # SSH-friendly reset helper
  requirements.txt        # Backend dependencies
web/
  index.html              # Session picker
  session.html            # Encryption UI
  admin.html              # Basic-auth admin console
```

## Getting Started
1. Clone the repo and enter the backend directory:
   ```bash
   git clone git@github.com:dillweed/dill-dev-cache.git
   cd dill-dev-cache/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   FLASK_APP=app.py flask run --host 0.0.0.0 --port 8000
   ```
2. Serve the static frontend (same origin keeps the relative `/api` calls working). From a new terminal:
   ```bash
   cd dill-dev-cache
   python3 -m http.server 8080 --directory web
   ```
3. Open `http://localhost:8080/index.html` in your browser. Create a session, copy the displayed encryption key, and start using the pad. The admin panel lives at `/admin.html` (protect behind nginx Basic Auth in production).

## Deployment Notes
- Point nginx (or any reverse proxy) at the `web/` directory for static assets and forward `/api/` to the Flask backend.
- Protect the admin endpoints with their own htpasswd file—this repo assumes the username `cache-admin` with a unique password.
- Back up `cache_data.json` routinely; without the encryption key the data cannot be recovered.
