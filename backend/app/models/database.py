"""
SQLAlchemy 2 Declarative Database Models for BHUMI-FUSE.
Compatible with PostgreSQL+PostGIS in production and SQLite for local test runs.
Includes automatic schema migration for SQLite.
"""

from __future__ import annotations
import datetime
import sqlite3
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from ..core.config import settings

Base = declarative_base()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    area_id = Column(String(64), nullable=True)
    state = Column(String(32), default="CREATED")  # CREATED, UPLOADED, HARMONIZED, REVIEWED
    crs_target = Column(String(32), default=settings.DEFAULT_METRIC_CRS)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    metadata_json = Column(Text, nullable=True)

    sources = relationship("InvestigationSource", back_populates="investigation", cascade="all, delete-orphan")


class InvestigationSource(Base):
    __tablename__ = "investigation_sources"

    id = Column(String(128), primary_key=True, index=True)
    investigation_id = Column(String(64), ForeignKey("investigations.id"), nullable=False, index=True)
    source_key = Column(String(64), nullable=False)  # cadastral, buildings, gnss, dsm, revenue, municipal
    filename = Column(String(255), nullable=False)
    file_format = Column(String(32), nullable=False)
    original_crs = Column(String(32), default="EPSG:4326")
    detected_crs = Column(String(32), default="EPSG:4326")
    target_crs = Column(String(32), default=settings.DEFAULT_METRIC_CRS)
    features_count = Column(Integer, default=0)
    status = Column(String(32), default="VALID")  # PENDING, VALID, INVALID
    data_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    investigation = relationship("Investigation", back_populates="sources")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    investigation_id = Column(String(64), nullable=True, index=True)
    action = Column(String(128), nullable=False)
    user = Column(String(128), default="Reviewing Officer")  # Backward compatibility
    user_id = Column(String(64), nullable=False, default="officer-01")
    user_name = Column(String(128), nullable=False, default="Reviewing Officer")
    details = Column(Text, nullable=True)
    type = Column(String(64), default="system")
    timestamp = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=False, default="0" * 64)
    row_hash = Column(String(64), nullable=False)


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String(64), nullable=True, index=True)
    case_id = Column(String(64), nullable=False, index=True)
    parcel_id = Column(String(64), nullable=False, index=True)
    decision = Column(String(32), nullable=False)  # accept, reject, adjust, escalate
    reviewer = Column(String(128), default="Reviewing Officer")  # Backward compatibility
    reviewer_id = Column(String(64), nullable=False, default="officer-01")
    reviewer_name = Column(String(128), nullable=False, default="Reviewing Officer")
    note = Column(Text, nullable=True)
    ai_recommendation = Column(String(64), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(String(64), default=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    timestamp = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=False, default="0" * 64)
    row_hash = Column(String(64), nullable=False)


def migrate_sqlite_tables_if_needed():
    """Ensure SQLite database columns match the target schema."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Column migrations dictionary: table -> list of (col_name, col_type)
    migrations = {
        "audit_logs": [
            ("investigation_id", "TEXT"),
            ("user_id", "TEXT DEFAULT 'officer-01'"),
            ("user_name", "TEXT DEFAULT 'Reviewing Officer'"),
            ("prev_hash", f"TEXT DEFAULT '{(64 * '0')}'"),
        ],
        "review_decisions": [
            ("investigation_id", "TEXT"),
            ("reviewer_id", "TEXT DEFAULT 'officer-01'"),
            ("reviewer_name", "TEXT DEFAULT 'Reviewing Officer'"),
            ("ai_recommendation", "TEXT"),
            ("prev_hash", f"TEXT DEFAULT '{(64 * '0')}'"),
            ("timestamp", "TEXT"),
        ],
        "investigations": [
            ("title", "TEXT DEFAULT 'Investigation'"),
            ("state", "TEXT DEFAULT 'CREATED'"),
            ("crs_target", "TEXT DEFAULT 'EPSG:32643'"),
            ("updated_at", "DATETIME"),
            ("metadata_json", "TEXT"),
        ],
        "investigation_sources": [
            ("detected_crs", "TEXT DEFAULT 'EPSG:4326'"),
            ("created_at", "DATETIME"),
        ]
    }

    for table, cols in migrations.items():
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cur.fetchone():
            cur.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cur.fetchall()}
            for col_name, col_type in cols:
                if col_name not in existing:
                    try:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass

    conn.commit()
    conn.close()


def init_database_tables():
    """Create database tables and run migrations if needed."""
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_tables_if_needed()
