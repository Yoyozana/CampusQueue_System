"""Simple in-memory limit on requests per IP address.

Stops one computer from hammering the login with guesses across many
accounts. (Per-account lockout lives in services/auth_service.py.)
Memory is per server process, which is fine for a single Render instance.
"""
import time
from collections import defaultdict, deque
from functools import wraps
from threading import Lock

from flask import request, jsonify

_hits = defaultdict(deque)
_lock = Lock()


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() or request.remote_addr or "unknown"


def limit_by_ip(name, max_requests, per_seconds):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (name, _client_ip())
            now = time.time()
            with _lock:
                q = _hits[key]
                while q and now - q[0] > per_seconds:
                    q.popleft()
                if len(q) >= max_requests:
                    return jsonify({"error": "Too many attempts. Please wait and try again."}), 429
                q.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
