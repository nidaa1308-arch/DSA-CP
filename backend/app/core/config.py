"""
System Configuration & Environment Settings for BHUMI-FUSE.
"""

from __future__ import annotations
import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "BHUMI-FUSE"
    VERSION: str = "2.0.0"
    API_PREFIX: str = ""

    # Database: Supports PostgreSQL+PostGIS, defaults to SQLite for zero-dependency local testing
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'bhumi_fuse.db'}"
    )

    # Security & Authentication
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "bhumifuse-gov-in-sih26013-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Upload Limits (50 MB standard limit for GIS packages)
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024

    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://web-production-d5b3c14b.up.railway.app",
    ]

    # Algorithm Defaults (Configurable by Officer in UI)
    DEFAULT_METRIC_CRS: str = "EPSG:32643"  # UTM Zone 43N (Maharashtra / Pune standard)
    MAX_RESIDUAL_TOLERANCE_M: float = 1.5
    CRITICAL_RESIDUAL_THRESHOLD_M: float = 3.0
    RANSAC_INLIER_THRESHOLD_M: float = 2.0
    TPS_REGULARIZATION_LAMBDA: float = 0.01

settings = Settings()
