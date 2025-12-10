from .database import init_db

# Auto-initialize database on package import with failsafe mechanism
try:
    init_db()
except Exception:
    # Silently pass if tables already exist or other non-critical errors
    pass
