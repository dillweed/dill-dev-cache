from flask import Flask, request, jsonify
import traceback
from order_calculations import calculate_orders
from flask_cors import CORS 
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime
import secrets
import fcntl
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)  # Enable CORS on the app

# Setup logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/myflaskapp.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('My Flask app startup')

# Multi-session cache configuration
CACHE_FILE = '/home/ubuntu/myflaskapp/cache_data.json'
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
    'gray-storm'
]

def default_session_record():
    return {
        'encrypted_content': None,
        'salt': None,
        'iv': None,
        'updated': None,
        'has_data': False
    }


def generate_salt():
    return secrets.token_hex(16)


@contextmanager
def locked_file(path, mode, lock_type):
    with open(path, mode) as f:
        fcntl.flock(f, lock_type)
        try:
            yield f
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def write_json_atomic(path, data):
    serialized = json.dumps(data, indent=2)
    with open(path, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(serialized)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def ensure_cache_schema(cache):
    updated = False
    normalized = {}
    for session_id in SESSION_IDS:
        record = cache.get(session_id)
        if not isinstance(record, dict):
            record = default_session_record()
            updated = True
        else:
            if 'encrypted_content' not in record:
                record['encrypted_content'] = None
                updated = True
            if 'salt' not in record:
                record['salt'] = None
                updated = True
            if 'iv' not in record:
                record['iv'] = None
                updated = True
            if 'updated' not in record:
                record['updated'] = None
                updated = True
            if 'has_data' not in record:
                record['has_data'] = False
                updated = True
        normalized[session_id] = record
    if set(cache.keys()) - set(SESSION_IDS):
        updated = True
    return normalized, updated

def init_cache_file():
    """Initialize cache file with empty sessions if it doesn't exist"""
    if not os.path.exists(CACHE_FILE):
        empty_cache = {}
        for session_id in SESSION_IDS:
            empty_cache[session_id] = default_session_record()
        write_json_atomic(CACHE_FILE, empty_cache)
        app.logger.info('Initialized multi-session cache file')

def load_cache():
    """Load cache data from file"""
    init_cache_file()
    with locked_file(CACHE_FILE, 'r', fcntl.LOCK_SH) as f:
        cache = json.load(f)
    normalized_cache, needs_update = ensure_cache_schema(cache)
    if needs_update:
        save_cache(normalized_cache)
    return normalized_cache

def save_cache(data):
    """Save cache data to file"""
    write_json_atomic(CACHE_FILE, data)

@app.route('/api/cache/sessions', methods=['GET'])
def get_sessions():
    """Get list of all sessions with metadata (no content)"""
    try:
        cache = load_cache()
        sessions = []
        for session_id in SESSION_IDS:
            session = cache.get(session_id, {})
            sessions.append({
                'id': session_id,
                'name': session_id.replace('-', ' ').title(),
                'has_data': session.get('has_data', False),
                'updated': session.get('updated')
            })
        return jsonify({'sessions': sessions})
    except Exception as e:
        app.logger.error('Sessions list error: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get encrypted data for a specific session"""
    try:
        if session_id not in SESSION_IDS:
            return jsonify({'error': 'Invalid session ID'}), 404
        
        cache = load_cache()
        session = cache.get(session_id)

        updated = False
        if session is None:
            session = default_session_record()
            cache[session_id] = session
            updated = True
        if session.get('salt') is None:
            session['salt'] = generate_salt()
            updated = True
        if updated:
            save_cache(cache)
        
        return jsonify({
            'encrypted_content': session.get('encrypted_content'),
            'salt': session.get('salt'),
            'iv': session.get('iv'),
            'updated': session.get('updated'),
            'has_data': session.get('has_data', False)
        })
    except Exception as e:
        app.logger.error('Session GET error (%s): %s', session_id, str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/<session_id>', methods=['POST'])
def save_session(session_id):
    """Save encrypted data for a specific session"""
    try:
        if session_id not in SESSION_IDS:
            return jsonify({'error': 'Invalid session ID'}), 404
        
        data = request.json
        encrypted_content = data.get('encrypted_content')
        iv = data.get('iv')
        
        cache = load_cache()
        session = cache.get(session_id, default_session_record())

        if session.get('salt') is None:
            incoming_salt = data.get('salt')
            if incoming_salt:
                session['salt'] = incoming_salt
            else:
                session['salt'] = generate_salt()
        elif session.get('salt') != data.get('salt') and data.get('salt'):
            # Honor existing encrypted data generated with legacy clients
            session['salt'] = data.get('salt')
        
        # Determine if session has data
        has_data = encrypted_content is not None and len(encrypted_content) > 0
        
        session.update({
            'encrypted_content': encrypted_content,
            'iv': iv,
            'updated': datetime.utcnow().isoformat() if has_data else None,
            'has_data': has_data
        })
        cache[session_id] = session
        
        save_cache(cache)
        
        app.logger.info('Session saved: %s (has_data: %s)', session_id, has_data)
        
        return jsonify({
            'success': True,
            'updated': cache[session_id]['updated'],
            'has_data': has_data
        })
    except Exception as e:
        app.logger.error('Session POST error (%s): %s', session_id, str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/<session_id>/reset', methods=['POST'])
def reset_session(session_id):
    """Reset a session (admin endpoint, requires basic auth from nginx)"""
    try:
        if session_id not in SESSION_IDS:
            return jsonify({'error': 'Invalid session ID'}), 404
        
        cache = load_cache()
        cache[session_id] = default_session_record()
        save_cache(cache)
        
        app.logger.info('Session reset: %s', session_id)
        
        return jsonify({'success': True, 'message': f'Session {session_id} has been reset'})
    except Exception as e:
        app.logger.error('Session reset error (%s): %s', session_id, str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache-admin/reset-all', methods=['POST'])
def reset_all_sessions():
    """Reset all sessions (admin endpoint)"""
    try:
        cache = load_cache()
        for session_id in SESSION_IDS:
            cache[session_id] = default_session_record()
        save_cache(cache)

        app.logger.info('All sessions reset by admin')

        return jsonify({'success': True, 'message': 'All sessions have been reset'})
    except Exception as e:
        app.logger.error('Reset all error: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate_orders', methods=['POST'])
def order_calc_api():
    try:
        data = request.json
        current_price = float(data['current_price'])
        target_price = float(data['target_price'])
        total_amount = float(data['total_amount'])
        num_orders = int(data['num_orders'])
        scale = float(data['scale'])

        results = calculate_orders(current_price, target_price, total_amount, num_orders, scale)
        return jsonify(results)
    except Exception as e:
        app.logger.error('Unhandled Exception: %s', traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/')
def index():
    return 'API Home'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
