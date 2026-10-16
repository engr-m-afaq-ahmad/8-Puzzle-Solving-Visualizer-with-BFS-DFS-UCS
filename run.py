"""Production entry point: serves the Flask API and the built React app
from a single origin/port. Start with:  python run.py
"""

import os
import sys

from backend import create_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "backend", "static")

app = create_app()

if __name__ == "__main__":
    if not os.path.isfile(os.path.join(STATIC_DIR, "index.html")):
        print(
            "Frontend build not found at backend/static/index.html.\n"
            "Build it first:\n"
            "  cd frontend\n"
            "  npm install\n"
            "  npm run build\n"
            "Then re-run: python run.py",
            file=sys.stderr,
        )
        sys.exit(1)
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"8-Puzzle Visualizer running on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug)
