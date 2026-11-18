"""
Pydantic v2 Request & Response Schemas for BHUMI-FUSE API.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Investigation Schemas ────────────────────────────────────────────────────

class InvestigationCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    area_id: Optional[str] = None
    crs_target: Optional[str] = "EPSG:32643"
    metadata: Optional[dict[str, Any]] = None


class InvestigationResponse(BaseModel):
    id: str
    title: str
    area_id: Optional[str]
    state: str
    crs_target: str
    created_at: Any
    sources_count: int = 0
    sources: list[dict[str, Any]] = []


# ── Harmonization Schemas ────────────────────────────────────────────────────

class AuthorityWeights(BaseModel):
    cadastral: float = Field(0.40, ge=0.0, le=1.0)
    drone: float = Field(0.35, ge=0.0, le=1.0)
    gnss: float = Field(0.25, ge=0.0, le=1.0)


class HarmonizeRequest(BaseModel):
    investigation_id: Optional[str] = None
    area_id: Optional[str] = None
    model: str = Field("tps", pattern="^(affine|tps)$")
    authority_weights: Optional[AuthorityWeights] = None
    custom_layers: Optional[dict[str, Any]] = None


# ── Review Decision Schemas ──────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    investigation_id: Optional[str] = None
    case_id: str
    parcel_id: str
    decision: str = Field(..., pattern="^(accept|reject|adjust|escalate)$")
    note: str = Field(..., min_length=2, max_length=2000, description="Mandatory officer review note")
    ai_recommendation: Optional[str] = None


class ReviewResponse(BaseModel):
    stored: bool
    version: int
    case_id: str
    parcel_id: str
    decision: str
    reviewer: str
    timestamp: str
    row_hash: str


# ── Topology Schemas ─────────────────────────────────────────────────────────

class TopologyRequest(BaseModel):
    investigation_id: Optional[str] = None
    harmonized: dict[str, Any]
