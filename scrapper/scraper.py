"""
Business Listings Scraper: OpenStreetMap Overpass API
======================================================
Strategy:
  1. PRIMARY  → Overpass API (real OSM data, free, no API key)
  2. FILL-GAP → Mock data generator (tops up to TARGET if OSM returns fewer)

Overpass API:
  - Endpoint : https://overpass-api.de/api/interpreter
  - Free, public, no auth required
  - Returns nodes/ways with tags: name, phone, address, amenity type

Run:
  pip install -r requirements.txt
  python scraper.py
"""

import time
import logging
import requests
import pandas as pd
from datetime import datetime
from mock_generator import MockDataGenerator, CITIES, CATEGORIES

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Config ───────────────────────────────────────────────────────────────────
TARGET_TOTAL     = 600
OVERPASS_URL     = "https://overpass-api.de/api/interpreter"
RESULTS_PER_CITY = 80    # fetch up to 80 per city (~800 total, dedupe brings it down)
DELAY_BETWEEN    = 3.0   # seconds between API calls (respectful crawling)


# ─── City bounding boxes  [south, west, north, east] ─────────────────────────
CITY_BBOXES: dict = {
    "Mumbai":    (18.85, 72.77, 19.28, 72.98),
    "Delhi":     (28.40, 76.84, 28.88, 77.35),
    "Bangalore": (12.83, 77.46, 13.14, 77.78),
    "Chennai":   (12.90, 80.15, 13.23, 80.30),
    "Hyderabad": (17.27, 78.30, 17.55, 78.58),
    "Pune":      (18.43, 73.74, 18.62, 73.96),
    "Kolkata":   (22.45, 88.26, 22.65, 88.43),
    "Ahmedabad": (22.95, 72.50, 23.13, 72.68),
    "Jaipur":    (26.82, 75.73, 26.96, 75.88),
    "Surat":     (21.11, 72.78, 21.24, 72.91),
}

# OSM tag groups per business category
CATEGORY_TAGS: dict = {
    "Restaurant":  [("amenity", "restaurant"), ("amenity", "fast_food"), ("amenity", "cafe")],
    "Hospital":    [("amenity", "hospital")],
    "Hotel":       [("tourism", "hotel"), ("tourism", "guest_house")],
    "School":      [("amenity", "school")],
    "Salon":       [("shop", "hairdresser"), ("shop", "beauty")],
    "Gym":         [("leisure", "fitness_centre"), ("leisure", "sports_centre")],
    "Pharmacy":    [("amenity", "pharmacy")],
    "Bank":        [("amenity", "bank")],
    "Supermarket": [("shop", "supermarket"), ("shop", "convenience")],
    "Clinic":      [("amenity", "clinic"), ("amenity", "doctors")],
}


# ─── Overpass Scraper ─────────────────────────────────────────────────────────
class OverpassScraper:
    """
    Fetches real business listings from OpenStreetMap via the Overpass API.
    Batches all categories per city into a single API call to minimise requests.
    """

    def _build_query(self, city: str, bbox: tuple, limit: int) -> str:
        """Build an Overpass QL query for all categories in one city."""
        s, w, n, e = bbox
        bbox_str = f"{s},{w},{n},{e}"

        lines = ['[out:json][timeout:60];', '(']
        for tags in CATEGORY_TAGS.values():
            for key, val in tags:
                lines.append(f'  node["{key}"="{val}"]["name"]({bbox_str});')
                lines.append(f'  way["{key}"="{val}"]["name"]({bbox_str});')
        lines.append(');')
        lines.append(f'out center {limit};')

        return "\n".join(lines)

    def _tag_to_category(self, tags: dict) -> str:
        """Map an OSM element's tags back to one of our 10 category labels."""
        for category, tag_list in CATEGORY_TAGS.items():
            for key, val in tag_list:
                if tags.get(key) == val:
                    return category
        return "Other"

    def _extract_address(self, tags: dict, city: str) -> str:
        """Build a readable address from OSM addr:* tags."""
        if tags.get("addr:full"):
            return tags["addr:full"]
        parts = []
        if tags.get("addr:housenumber"):
            parts.append(tags["addr:housenumber"])
        if tags.get("addr:street"):
            parts.append(tags["addr:street"])
        if tags.get("addr:suburb"):
            parts.append(tags["addr:suburb"])
        elif tags.get("addr:neighbourhood"):
            parts.append(tags["addr:neighbourhood"])
        parts.append(city)
        return ", ".join(parts)

    def _extract_phone(self, tags: dict):
        """Extract phone from any common OSM phone key."""
        for key in ("phone", "contact:phone", "contact:mobile", "mobile"):
            if tags.get(key):
                return tags[key].strip()
        return None

    def scrape_city(self, city: str) -> list:
        """Fetch all business listings for one city in a single API call."""
        bbox  = CITY_BBOXES[city]
        query = self._build_query(city, bbox, RESULTS_PER_CITY)

        try:
            logger.info(f"  Querying OSM → {city} ...")
            resp = requests.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=65,
                headers={"User-Agent": "BusinessDashboard/1.0 (internship-assignment)"},
            )

            if resp.status_code != 200:
                logger.warning(f"  HTTP {resp.status_code} for {city}")
                return []

            elements = resp.json().get("elements", [])
            records  = []

            for el in elements:
                tags = el.get("tags", {})
                name = tags.get("name", "").strip()
                if not name:
                    continue

                category = self._tag_to_category(tags)
                if category == "Other":
                    continue

                records.append({
                    "business_name": name,
                    "category":      category,
                    "city":          city,
                    "address":       self._extract_address(tags, city),
                    "phone":         self._extract_phone(tags),
                    "source":        "OpenStreetMap",
                })

            logger.info(f"  {city:<12} → {len(records):>3} real records")
            time.sleep(DELAY_BETWEEN)
            return records

        except requests.exceptions.Timeout:
            logger.warning(f"  Timeout for {city}: skipping")
            return []
        except Exception as e:
            logger.warning(f"  Error for {city}: {e}")
            return []

    def run(self) -> list:
        logger.info("── Overpass API Scraper ──────────────────────────────────")
        all_records = []
        for city in CITY_BBOXES:
            records = self.scrape_city(city)
            all_records.extend(records)
        logger.info(f"── OSM total : {len(all_records)} records ─────────────────")
        return all_records


# ─── Pipeline ─────────────────────────────────────────────────────────────────
def run_pipeline() -> pd.DataFrame:
    logger.info("=" * 50)
    logger.info("  Business Listings Collection Pipeline")
    logger.info("=" * 50)

    all_listings = []

    # ── Step 1: Real data from OpenStreetMap ──────────────────────────────────
    logger.info("\nSTEP 1 › Fetching real data from OpenStreetMap")
    scraper  = OverpassScraper()
    osm_data = scraper.run()
    all_listings.extend(osm_data)
    logger.info(f"         OSM records collected : {len(osm_data)}\n")

    # ── Step 2: Fill gap with mock data ───────────────────────────────────────
    mock_needed = max(0, TARGET_TOTAL - len(all_listings))
    logger.info(f"STEP 2 › Filling gap with {mock_needed} mock records")
    logger.info(f"         (target {TARGET_TOTAL}, have {len(all_listings)} from OSM)")

    if mock_needed > 0:
        gen       = MockDataGenerator()
        mock_data = gen.generate_batch(mock_needed)
        all_listings.extend(mock_data)
    logger.info(f"         Mock records added : {mock_needed}\n")

    # ── Step 3: Clean & export ────────────────────────────────────────────────
    logger.info("STEP 3 › Cleaning and exporting")
    df = pd.DataFrame(all_listings)

    df["business_name"] = df["business_name"].str.strip().str.title()
    df["city"]          = df["city"].str.strip()
    df["category"]      = df["category"].str.strip()
    df["address"]       = df["address"].str.strip()
    df["source"]        = df["source"].str.strip()
    df["created_at"]    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clean phone: treat "None"/"nan" strings as actual null
    df["phone"] = df["phone"].apply(
        lambda x: None if str(x).strip().lower() in ("none", "nan", "") else str(x).strip()
    )

    before = len(df)
    df = df.drop_duplicates(subset=["business_name", "city"])
    df = df.reset_index(drop=True)

    output = "listings.csv"
    df.to_csv(output, index=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    osm_count  = len(df[df["source"] == "OpenStreetMap"])
    mock_count = len(df[df["source"] != "OpenStreetMap"])

    logger.info(f"\n✅  Done!  {len(df)} total records saved → {output}")
    logger.info(f"    Real (OSM)  : {osm_count}")
    logger.info(f"    Mock        : {mock_count}")
    logger.info(f"\n📊  Distribution")
    logger.info(f"    Cities     : {df['city'].nunique()}")
    logger.info(f"    Categories : {df['category'].nunique()}")
    logger.info(f"    Sources    :")
    for src, cnt in df["source"].value_counts().items():
        bar = "█" * (cnt // 10)
        logger.info(f"      {src:<20} {cnt:>4}  {bar}")

    return df


if __name__ == "__main__":
    df = run_pipeline()
    print("\nSample records:")
    print(df.head(8).to_string(index=False))
