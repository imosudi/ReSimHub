"""
Public-facing entry point for the ReSimHub Flask web application.
"""

import os
import sys

try:
    from backend.flask_app import app
except ImportError:
    from flask_app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
