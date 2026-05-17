# BizDash: Business Listings Dashboard

A full-stack data-driven dashboard that collects, stores, and visualizes business listings across Indian cities.

Built as part of the **Data Science Intern Assignment**.

---

## 🖥️ Live Preview

| Layer    | Tech                          | Status       |
| -------- | ----------------------------- | ------------ |
| Frontend | React + TypeScript + Recharts | ✅ Running   |
| Backend  | FastAPI (Python)              | ✅ Running   |
| Database | MySQL (Railway Cloud)         | ✅ Connected |

---

## 📁 Project Structure

```
business-dashboard/
├── scraper/                    # Part 1: Data Collection
│   ├── scraper.py              # Main pipeline (OSM API + mock fallback)
│   ├── mock_generator.py       # Realistic Indian business data generator
│   ├── load_to_db.py           # Bulk insert CSV → MySQL
│   ├── schema.sql              # DB schema reference
│   ├── listings.csv            # Generated dataset (661 records)
│   ├── requirements.txt
│   └── .env.example
│
├── backend/                    # Part 3: FastAPI
│   ├── main.py                 # API routes
│   ├── models.py               # Pydantic request/response schemas
│   ├── database.py             # MySQL connection pool
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # Part 4: React Dashboard
│   ├── src/
│   │   ├── App.tsx             # Main component + all views
│   │   ├── main.tsx            # React entry point
│   │   ├── index.css           # Global styles + DM Sans font
│   │   └── services/
│   │       └── api.ts          # Axios API client
│   ├── package.json
│   └── vite.config.ts
│
├── dump/
│   └── listing_master.sql      # Database dump
│
└── README.md
```

---

## ⚙️ Tech Stack

| Layer           | Technology                 | Purpose                  |
| --------------- | -------------------------- | ------------------------ |
| Frontend        | React 18 + TypeScript      | UI framework             |
| Styling         | Tailwind CSS               | Utility-first CSS        |
| Charts          | Recharts                   | Bar + Donut charts       |
| Icons           | Lucide React               | UI icons                 |
| Backend         | FastAPI (Python 3.11+)     | REST API                 |
| Validation      | Pydantic v2                | Request/response schemas |
| Database        | MySQL 8 (Railway Cloud)    | Persistent storage       |
| Data Collection | OpenStreetMap Overpass API | Real business listings   |
| HTTP Client     | Axios                      | Frontend API calls       |
| Server          | Uvicorn                    | ASGI server for FastAPI  |

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Railway](https://railway.app) account (free tier is enough)

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/business-dashboard.git
cd business-dashboard
```

---

### 2. Database Setup (Railway MySQL)

1. Go to [railway.app](https://railway.app) → **New Project → Deploy MySQL**
2. Once deployed, click the MySQL service → **Variables** tab
3. Note down: `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`
4. Use the **public proxy** values (not the internal `mysql.railway.internal` host)

---

### 3. Scraper: Collect Data

```bash
cd scraper
pip install -r requirements.txt

# Copy and fill in your Railway credentials
copy .env.example .env

# Run the scraper (fetches real data from OpenStreetMap + fills gaps with mock data)
python scraper.py

# Load the generated listings.csv into MySQL
python load_to_db.py
```

Expected output:

```
✅  Done!  661 total records saved → listings.csv
    Real (OSM)  : ~420
    Mock        : ~241
```

---

### 4. Backend: FastAPI

```bash
cd backend
pip install -r requirements.txt

# Copy and fill in your Railway credentials (same as scraper)
copy .env.example .env

# Start the API server
uvicorn main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

#### Available Endpoints

| Method | Endpoint                   | Description                     |
| ------ | -------------------------- | ------------------------------- |
| `GET`  | `/health`                  | DB ping + total listing count   |
| `POST` | `/listings/bulk-insert`    | Bulk insert listings (JSON)     |
| `GET`  | `/listings`                | Paginated listings with filters |
| `GET`  | `/dashboard/city-wise`     | Business count by city          |
| `GET`  | `/dashboard/category-wise` | Business count by category      |
| `GET`  | `/dashboard/source-wise`   | Business count by source        |

---

### 5. Frontend: React Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:5173**

> Make sure the FastAPI backend is running on port 8000 before starting the frontend.

---

## 📊 Data Collection Approach

### Primary Source: OpenStreetMap Overpass API

- Queried real business data across **10 Indian cities**: Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Pune, Kolkata, Ahmedabad, Jaipur, Surat
- Used **10 business categories**: Restaurant, Hospital, Hotel, School, Salon, Gym, Pharmacy, Bank, Supermarket, Clinic
- Each city queried with a geographic bounding box: returns real OSM nodes/ways with name, phone, address tags
- **No API key required**: Overpass API is fully public and free
- Respectful crawling: 3-second delay between city queries

### Fallback: Mock Data Generator

- When OSM returns fewer than 600 records, the gap is filled with realistic generated data
- Uses real Indian business name patterns, valid `+91-XXXXXXXXXX` phone formats, and real area names
- Final dataset: **661 records** across 10 cities, 10 categories, multiple sources

---

## 🗄️ Database Schema

```sql
CREATE TABLE listing_master (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    business_name VARCHAR(255)  NOT NULL,
    category      VARCHAR(100)  NOT NULL,
    city          VARCHAR(100)  NOT NULL,
    address       TEXT,
    phone         VARCHAR(50)   DEFAULT NULL,
    source        VARCHAR(100)  NOT NULL,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_city     (city),
    INDEX idx_category (category),
    INDEX idx_source   (source)
);
```

---

## ⚠️ Challenges Faced

### 1. Web Scraping Restrictions (403 Blocked)

**Problem:** Justdial, Sulekha, and Google Maps all returned HTTP 403 when accessed via Python `requests`. These platforms actively block automated scraping.

**Solution:** Switched to the **OpenStreetMap Overpass API**: a free, public, and legally accessible source of real business data. Supplemented with a mock data generator to meet the 500+ record requirement.

### 2. Railway Internal vs Public Hostname

**Problem:** Railway provides two sets of MySQL connection details: an internal hostname (`mysql.railway.internal`) that only works within Railway's network, and a public proxy that works from local machines.

**Solution:** Used the public proxy domain (`RAILWAY_TCP_PROXY_DOMAIN`) and the corresponding 5-digit port for local development.

### 3. Pagination Without Total Count

**Problem:** The original `/listings` endpoint returned a plain list with no metadata, so the frontend couldn't show "Page 2 of 34" or disable the Next button correctly.

**Solution:** Updated the endpoint to run a `COUNT(*)` query alongside the data query and return a `PaginatedListingsResponse` with `total`, `total_pages`, `has_next`, and `has_prev`.

### 4. Phone Number Inconsistency

**Problem:** OSM data had phone numbers in many different formats: some with country codes, some without, some with spaces/dashes.

**Solution:** Added a `_normalize_phone()` validator in Pydantic models that standardises all numbers to `+91-XXXXXXXXXX` format.

---

## 📽️ Demo Video

[Link to demo video: add after recording]

Covers:

- Scraping approach and data pipeline
- FastAPI endpoints via Swagger UI (`/docs`)
- Dashboard functionality walkthrough

---

## 👤 Author

Built for the Data Science Intern assignment.
