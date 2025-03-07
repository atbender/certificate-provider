import argparse
import threading
import time
import os
import subprocess

from src.web.app import *
from src.api.api import start_api_server


def run_api_server():
    start_api_server()


def run_web_interface():
    subprocess.Popen(["streamlit", "run", "src/web/certificate.py", "--server.port=8501", "--server.address=0.0.0.0"])


def main():
    parser = argparse.ArgumentParser(
        description='Kubernetes Certificate Generator and Validator'
    )
    parser.add_argument(
        '--api-only', 
        action='store_true',
        help='Run only the API server'
    )
    parser.add_argument(
        '--web-only', 
        action='store_true',
        help='Run only the web interface'
    )
    
    args = parser.parse_args()
    
    os.makedirs('data', exist_ok=True)
    
    if args.api_only:
        print("Starting API server only...")
        start_api_server()
    elif args.web_only:
        print("Starting web interface only...")
        run_web_interface()
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print("Shutting down...")
                break
    else:
        print("Starting both API server and web interface...")
        api_thread = threading.Thread(target=run_api_server)
        api_thread.daemon = True
        api_thread.start()
        
        run_web_interface()
        
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print("Shutting down...")
                break


if __name__ == "__main__":
    main()