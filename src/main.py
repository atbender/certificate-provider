import os
from src.api.api import start_api_server


def main():
    os.makedirs('data', exist_ok=True)
    print("Starting API server...")
    start_api_server()


if __name__ == "__main__":
    main()
