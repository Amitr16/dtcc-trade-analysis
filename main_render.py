# main_render.py - Gunicorn entry point
from src.main import app

# Gunicorn will import this module and use the 'app' object
if __name__ == "__main__":
    # Fallback for direct execution (not recommended in production)
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
