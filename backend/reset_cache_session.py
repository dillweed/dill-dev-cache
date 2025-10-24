#!/usr/bin/env python3
"""
Reset cache sessions - Admin utility
Usage:
  python3 reset_cache_session.py <session-id>    # Reset specific session
  python3 reset_cache_session.py --all           # Reset all sessions
"""
import sys
import json
import os

CACHE_FILE = '/home/ubuntu/myflaskapp/cache_data.json'
SESSION_IDS = [
    'blue-river', 'green-forest', 'red-canyon', 'golden-plains', 'silver-lake',
    'purple-mountain', 'orange-sunset', 'pink-cloud', 'brown-earth', 'gray-storm'
]

def reset_session(session_id):
    """Reset a single session"""
    if not os.path.exists(CACHE_FILE):
        print(f'Error: Cache file not found at {CACHE_FILE}')
        return False
    
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
    
    if session_id not in cache:
        print(f'Error: Session "{session_id}" not found')
        print(f"Valid sessions: {', '.join(SESSION_IDS)}")
        return False
    
    cache[session_id] = {
        'encrypted_content': None,
        'salt': None,
        'iv': None,
        'updated': None,
        'has_data': False
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f'✓ Session "{session_id}" has been reset')
    return True

def reset_all():
    """Reset all sessions"""
    if not os.path.exists(CACHE_FILE):
        print(f'Error: Cache file not found at {CACHE_FILE}')
        return False
    
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
    
    count = 0
    for session_id in SESSION_IDS:
        cache[session_id] = {
            'encrypted_content': None,
            'salt': None,
            'iv': None,
            'updated': None,
            'has_data': False
        }
        count += 1
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f'✓ All {count} sessions have been reset')
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print(f'  {sys.argv[0]} <session-id>    # Reset specific session')
        print(f'  {sys.argv[0]} --all           # Reset all sessions')
        print(f"\nValid session IDs: {', '.join(SESSION_IDS)}")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == '--all':
        success = reset_all()
    else:
        success = reset_session(arg)
    
    sys.exit(0 if success else 1)
