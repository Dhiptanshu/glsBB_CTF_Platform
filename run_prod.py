from waitress import serve
from app import app, db
import logging

import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    # Determine threads based on cores (2 threads per core is a good rule of thumb for I/O bound web apps)
    threads = (os.cpu_count() or 4) * 2
    
    print("----------------------------------------------------------------")
    print("Starting PRODUCTION server for 100+ users...")
    print(f"Detected {os.cpu_count()} cores. Spawning {threads} threads.")
    print("Listening on: http://0.0.0.0:5002")
    print("Use this port for ngrok: ngrok http 5002")
    print("----------------------------------------------------------------")
    
    serve(app, host='0.0.0.0', port=5002, threads=threads)
