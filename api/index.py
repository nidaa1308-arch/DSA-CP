import sys
from pathlib import Path

# Add backend directory to sys.path so imports resolve cleanly on Vercel serverless
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app
