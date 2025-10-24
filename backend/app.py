from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import json
from datetime import datetime
import secrets
import fcntl
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
CACHE_FILE = BASE_DIR / 'cache_data.json'
LOG_DIR = BASE_DIR / 'logs'

app = Flask(__name__)
CORS(app)

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_path = LOG_DIR / 'encrypted-scratchpad.log'
handler = RotatingFileHandler(log_path, maxBytes=10240, backupCount=10)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

SESSION_IDS = [
    'blue-river',
    'green-forest',
    'red-canyon',
    'golden-plains',
    'silver-lake',
    'purple-mountain',
    'orange-sunset',
    'pink-cloud',
    'brown-earth',
    'gray-storm',
]

def default_session_record():
    return {
        'encrypted_content': None,
        'salt': None,
        'iv': None,
        'updated': None,
        'has_data': False,
    }

def generate_salt():
    return secrets.token_hex(16)

@contextmanager
def locked_file(path, mode, lock_type):
    with open(path, mode) as handle:
        fcntl.flock(handle, lock_type)
        try:
            yield handle
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

def write_json_atomic(path, data):
    serialized = json.dumps(data, indent=2)
    with open(path, 'w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            handle.write(serialized)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

def ensure_cache_file():
    if not CACHE_FILE.exists():
        initial = {sid: default_session_record() for sid in SESSION_IDS}
        write_json_atomic(CACHE_FILE, initial)
        app.logger.info('Initialized cache file at %s', CACHE_FILE)

def normalize_schema(cache):
    updated = False
    normalized = {}
    for session_id in SESSION_IDS:
        record = cache.get(session_id)
        if not isinstance(record, dict):
            record = default_session_record()
            updated = True
        else:
            for key in ('encrypted_content', 'salt', 'iv', 'updated', 'has_data'):
                if key not in record:
                    record[key] = None if key != 'has_data' else False
                    updated = True
        normalized[session_id] = record
    if set(cache.keys()) - set(SESSION_IDS):
        updated = True
    return normalized, updated

def load_cache():
    ensure_cache_file()
    with locked_file(CACHE_FILE, 'r', fcntl.LOCK_SH) as handle:
        cache = json.load(handle)
    normalized, needs_update = normalize_schema(cache)
    if needs_update:
        write_json_atomic(CACHE_FILE, normalized)
    return normalized

def save_cache(cache):
    write_json_atomic(CACHE_FILE, cache)

@app.route('/api/cache/sessions', methods=['GET'])
def list_sessions():
    try:
        cache = load_cache()
        sessions = []
        for session_id in SESSION_IDS:
            record = cache.get(session_id, default_session_record())
            sessions.append({
                'id': session_id,
                'name': session_id.replace('-', ' ').title(),
                'has_data': record.get('has_data', False),
                'updated': record.get('updated'),
            })
        return jsonify({'sessions': sessions})
    except Exception as exc:
        app.logger.exception('Failed to list sessions')
        return jsonify({'error': str(exc)}), 500

@app.route('/api/cache/<session_id>', methods=['GET'])
def get_session(session_id):
    if session_id not in SESSION_IDS:
        return jsonify({'error': 'Invalid session ID'}), 404
    try:
        cache = load_cache()
        record = cache.get(session_id, default_session_record())
        if record.get('salt') is None:
            record['salt'] = generate_salt()
            cache[session_id] = record
            save_cache(cache)
        return jsonify({
            'encrypted_content': record.get('encrypted_content'),
            'salt': record.get('salt'),
            'iv': record.get('iv'),
            'updated': record.get('updated'),
            'has_data': record.get('has_data', False),
        })
    except Exception as exc:
        app.logger.exception('Failed to load session %s', session_id)
        return jsonify({'error': str(exc)}), 500

@app.route('/api/cache/<session_id>', methods=['POST'])
def save_session(session_id):
    if session_id not in SESSION_IDS:
        return jsonify({'error': 'Invalid session ID'}), 404
    try:
        payload = request.json or {}
        encrypted_content = payload.get('encrypted_content')
        iv = payload.get('iv')
        salt = payload.get('salt')

        cache = load_cache()
        record = cache.get(session_id, default_session_record())

        if record.get('salt') is None:
            record['salt'] = salt or generate_salt()
        elif salt:
            record['salt'] = salt

        has_data = bool(encrypted_content)
        record.update({
            'encrypted_content': encrypted_content,
            'iv': iv,
            'updated': datetime.utcnow().isoformat() if has_data else None,
            'has_data': has_data,
        })
        cache[session_id] = record
        save_cache(cache)
        return jsonify({'success': True, 'updated': record['updated'], 'has_data': has_data})
    except Exception as exc:
        app.logger.exception('Failed to save session %s', session_id)
        return jsonify({'error': str(exc)}), 500

@app.route('/api/cache/<session_id>/reset', methods=['POST'])
def reset_session(session_id):
    if session_id not in SESSION_IDS:
        return jsonify({'error': 'Invalid session ID'}), 404
    try:
        cache = load_cache()
        cache[session_id] = default_session_record()
        save_cache(cache)
        app.logger.info('Reset session %s', session_id)
        return jsonify({'success': True})
    except Exception as exc:
        app.logger.exception('Failed to reset session %s', session_id)
        return jsonify({'error': str(exc)}), 500

@app.route('/api/cache-admin/reset-all', methods=['POST'])
def reset_all():
    try:
        cache = {sid: default_session_record() for sid in SESSION_IDS}
        save_cache(cache)
        app.logger.info('Reset all sessions')
        return jsonify({'success': True})
    except Exception as exc:
        app.logger.exception('Failed to reset all sessions')
        return jsonify({'error': str(exc)}), 500

@app.route('/api/')
def api_root():
    return jsonify({'message': 'encrypted-scratchpad API'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
