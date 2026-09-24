"""
frontend.py
-----------
Reflex application entry point connecting frontend rxconfig to the 
core app module and state architecture.
"""

import sys
import os

# Include parent workspace directory in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import index, AppState, app

# Register page
app.add_page(index, title="Tendy | University Attendance & Safe Skips Guard")
