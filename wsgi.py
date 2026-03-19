import sys
import os

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLET_DIR = os.path.join(BASE_DIR, 'Templet')

# Add Templet directory to Python path
if TEMPLET_DIR not in sys.path:
    sys.path.insert(0, TEMPLET_DIR)

# Import the app
from app import app

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

