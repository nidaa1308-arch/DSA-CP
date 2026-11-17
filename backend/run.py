import os
import sys
from pathlib import Path
import uvicorn

# Ensure backend directory is in sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def get_port() -> int:
    raw_port = os.environ.get("PORT", "8000")
    if not str(raw_port).isdigit():
        return 8000
    try:
        return int(raw_port)
    except (ValueError, TypeError):
        return 8000

if __name__ == "__main__":
    port = get_port()
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting Uvicorn on {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port)
