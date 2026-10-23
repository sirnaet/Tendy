"""
Tendy/Tendy.py
--------------
Reflex entry point. Delegates entirely to the root app.py which contains
the full production-ready Python frontend + Firebase backend logic.
"""

# Re-export the Reflex app so `reflex run` picks it up correctly
from app import app, AppState, index  # noqa: F401
