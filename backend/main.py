"""
main.py: Business Listings Dashboard API
==========================================
Endpoints:
  POST /listings/bulk-insert         Insert listings in bulk
  GET  /dashboard/city-wise          City-wise business count
  GET  /dashboard/category-wise      Category-wise business count
  GET  /dashboard/source-wise        Source-wise business count
  GET  /listings                     Paginated listing records
  GET  /health                       Health check

Run:
  uvicorn main:app --reload --port 8000
Docs:
  http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection
from models import (
    BulkInsertRequest,
    BulkInsertResponse,
    DashboardResponse,
    CountItem,
    ListingOut,
    PaginatedListingsResponse,
)

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Business Listings Dashboard API",
    version="1.0.0",
    description="API for the Business Listings Dashboard: internship assignment",
)

# Allow React dev server (port 3000 / 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    """Verify the API and DB connection are alive."""
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM listing_master")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "ok", "total_listings": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Listings ─────────────────────────────────────────────────────────────────
@app.post("/listings/bulk-insert", response_model=BulkInsertResponse, tags=["Listings"])
def bulk_insert(payload: BulkInsertRequest):
    """
    Bulk insert business listings into listing_master.
    Accepts a JSON body: { "listings": [ {...}, {...} ] }
    """
    if not payload.listings:
        raise HTTPException(status_code=400, detail="listings array is empty")

    sql = """
        INSERT INTO listing_master
            (business_name, category, city, address, phone, source)
        VALUES
            (%s, %s, %s, %s, %s, %s)
    """
    rows = [
        (
            item.business_name,
            item.category,
            item.city,
            item.address,
            item.phone,
            item.source,
        )
        for item in payload.listings
    ]

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, rows)
        conn.commit()
        inserted = cursor.rowcount
        cursor.close()
        conn.close()
        return BulkInsertResponse(
            message=f"Successfully inserted {inserted} listings",
            inserted=inserted,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/listings", response_model=PaginatedListingsResponse, tags=["Listings"])
def get_listings(
    page:     int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=200),
    city:     str = Query(default=None),
    category: str = Query(default=None),
):
    """
    Return paginated listings with full pagination metadata.
    Supports optional city and category filters (applied server-side).
    """
    conditions  = []
    filter_vals = []

    if city:
        conditions.append("city = %s")
        filter_vals.append(city)
    if category:
        conditions.append("category = %s")
        filter_vals.append(category)

    where  = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * per_page

    count_sql = f"SELECT COUNT(*) AS total FROM listing_master {where}"
    data_sql  = f"""
        SELECT id, business_name, category, city, address, phone, source, created_at
        FROM listing_master
        {where}
        ORDER BY id
        LIMIT %s OFFSET %s
    """

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Total count for pagination metadata
        cursor.execute(count_sql, filter_vals)
        total = cursor.fetchone()["total"]

        # Page of data
        cursor.execute(data_sql, filter_vals + [per_page, offset])
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return PaginatedListingsResponse.build(
            data     = rows,
            total    = total,
            page     = page,
            per_page = per_page,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Dashboard ────────────────────────────────────────────────────────────────
def _run_group_query(group_col: str) -> DashboardResponse:
    """Generic helper: SELECT group_col, COUNT(*) FROM listing_master GROUP BY group_col."""
    sql = f"""
        SELECT {group_col} AS label, COUNT(*) AS count
        FROM listing_master
        GROUP BY {group_col}
        ORDER BY count DESC
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        rows  = cursor.fetchall()
        total_sql = "SELECT COUNT(*) FROM listing_master"
        cursor.execute(total_sql)
        total = cursor.fetchone()["COUNT(*)"]
        cursor.close()
        conn.close()
        return DashboardResponse(
            total=total,
            data=[CountItem(label=r["label"], count=r["count"]) for r in rows],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/city-wise", response_model=DashboardResponse, tags=["Dashboard"])
def city_wise():
    """Return business count grouped by city."""
    return _run_group_query("city")


@app.get("/dashboard/category-wise", response_model=DashboardResponse, tags=["Dashboard"])
def category_wise():
    """Return business count grouped by category."""
    return _run_group_query("category")


@app.get("/dashboard/source-wise", response_model=DashboardResponse, tags=["Dashboard"])
def source_wise():
    """Return business count grouped by source."""
    return _run_group_query("source")