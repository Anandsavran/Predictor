import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLET_DIR = os.path.join(BASE_DIR, 'Templet')
sys.path.insert(0, TEMPLET_DIR)

from app import app

print("Listing all registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule}")
