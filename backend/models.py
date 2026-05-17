"""
models.py: Pydantic schemas for request validation and response shaping
=========================================================================
Pydantic v2 style throughout (model_config, @field_validator, @computed_field).

Models:
  Request  : ListingIn, BulkInsertRequest
  Response : BulkInsertResponse, ListingOut, PaginatedListingsResponse,
             CountItem, DashboardResponse
"""

import re
import math
from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing   import Optional
from datetime import datetime


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_str(v: str) -> str:
    """Strip leading/trailing whitespace."""
    return v.strip() if isinstance(v, str) else v


def _normalize_phone(v: Optional[str]) -> Optional[str]:
    """
    Normalize phone numbers to a consistent +91-XXXXXXXXXX format.
    Returns None for empty / clearly invalid values.

    Examples:
      "9876543210"        → "+91-9876543210"
      "91 9876543210"     → "+91-9876543210"
      "+91-9876543210"    → "+91-9876543210"  (unchanged)
      "None" / ""         → None
    """
    if not v or str(v).strip().lower() in ("none", "nan", "null", ""):
        return None

    # Remove all spaces, dashes, parentheses except leading +
    raw = str(v).strip()
    has_plus = raw.startswith("+")
    cleaned  = re.sub(r"[\s\-\(\)]+", "", raw)
    if has_plus:
        cleaned = "+" + cleaned.lstrip("+")

    # Plain 10-digit Indian mobile
    if re.fullmatch(r"\d{10}", cleaned):
        return f"+91-{cleaned}"

    # 91 + 10 digits (no +)
    if re.fullmatch(r"91\d{10}", cleaned):
        return f"+91-{cleaned[2:]}"

    # +91 + 10 digits
    if re.fullmatch(r"\+91\d{10}", cleaned):
        return f"+91-{cleaned[3:]}"

    # Already formatted +91-XXXXXXXXXX or foreign → keep if plausibly valid
    digits_only = re.sub(r"\D", "", cleaned)
    return cleaned if len(digits_only) >= 7 else None


# ─── Request Models ───────────────────────────────────────────────────────────

class ListingIn(BaseModel):
    """
    Schema for a single listing in a bulk-insert request.
    Validates and normalises all fields before they reach the DB.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    business_name: str           = Field(..., min_length=1, max_length=255,
                                         description="Business display name")
    category:      str           = Field(..., min_length=1, max_length=100,
                                         description="Business category e.g. Restaurant")
    city:          str           = Field(..., min_length=1, max_length=100,
                                         description="City the business is located in")
    address:       Optional[str] = Field(default=None, max_length=500)
    phone:         Optional[str] = Field(default=None, max_length=50)
    source:        str           = Field(..., min_length=1, max_length=100,
                                         description="Data source e.g. OpenStreetMap")

    @field_validator("business_name", mode="before")
    @classmethod
    def title_case_name(cls, v: str) -> str:
        """Ensure business names are consistently title-cased."""
        return _clean_str(v).title()

    @field_validator("category", "city", "source", mode="before")
    @classmethod
    def clean_string_fields(cls, v: str) -> str:
        return _clean_str(v)

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_phone(v)


class BulkInsertRequest(BaseModel):
    """Wraps a list of listings for the bulk-insert endpoint."""
    listings: list[ListingIn] = Field(..., min_length=1,
                                      description="One or more listings to insert")


# ─── Response Models ──────────────────────────────────────────────────────────

class BulkInsertResponse(BaseModel):
    message:  str
    inserted: int
    skipped:  int = 0   # reserved: duplicate detection


class ListingOut(BaseModel):
    """Full listing record returned from the DB."""
    model_config = ConfigDict(from_attributes=True)

    id:            int
    business_name: str
    category:      str
    city:          str
    address:       Optional[str]
    phone:         Optional[str]
    source:        str
    created_at:    datetime


class PaginatedListingsResponse(BaseModel):
    """
    Paginated listings response with full metadata.
    Gives the frontend everything it needs to render page controls
    and show "Page 2 of 34" style indicators.
    """
    data:        list[ListingOut]
    total:       int    # total matching records across ALL pages
    page:        int    # current page (1-indexed)
    per_page:    int    # records per page
    total_pages: int    # ceil(total / per_page)
    has_next:    bool
    has_prev:    bool

    @classmethod
    def build(
        cls,
        data:     list,
        total:    int,
        page:     int,
        per_page: int,
    ) -> "PaginatedListingsResponse":
        """Factory: build from raw DB results + counts."""
        total_pages = max(1, math.ceil(total / per_page)) if per_page else 1
        return cls(
            data        = data,
            total       = total,
            page        = page,
            per_page    = per_page,
            total_pages = total_pages,
            has_next    = page < total_pages,
            has_prev    = page > 1,
        )


class CountItem(BaseModel):
    """A single label → count pair used in all dashboard endpoints."""
    label: str
    count: int


class DashboardResponse(BaseModel):
    """
    Standard response for all /dashboard/* endpoints.
    `total` is the grand total across all groups (sum of all counts).
    """
    total: int
    data:  list[CountItem]