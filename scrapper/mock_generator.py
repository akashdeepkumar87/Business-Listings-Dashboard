"""
Mock Data Generator
===================
Generates realistic Indian business listings with:
  - Proper Indian city names
  - Real business name patterns per category
  - Valid Indian phone number format (+91-XXXXXXXXXX)
  - Realistic addresses with area names
  - Balanced distribution across cities, categories, sources
"""

import random
from datetime import datetime

# ─── Shared Constants (imported by scraper.py too) ───────────────────────────
CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
    "Pune",   "Kolkata", "Ahmedabad", "Jaipur", "Surat",
]

CATEGORIES = [
    "Restaurant", "Hospital", "Hotel", "School", "Salon",
    "Gym",        "Pharmacy", "Bank",  "Supermarket", "Clinic",
]

SOURCES = ["Google", "Justdial", "Sulekha"]


# ─── Seed Data ────────────────────────────────────────────────────────────────
BUSINESS_NAMES: dict[str, list[str]] = {
    "Restaurant": [
        "Spice Garden", "Royal Dhaba", "Punjab Kitchen", "South Spice",
        "Biryani House", "Tandoor Express", "Zaika Restaurant", "Masala Junction",
        "Curry Leaf Cafe", "Saffron Dining", "Barbeque Nation", "Desi Tadka",
        "Maa Ki Rasoi", "Shree Thali", "Highway King Dhaba", "Bombay Bites",
    ],
    "Hospital": [
        "Apollo", "Fortis", "Medanta", "Max Healthcare", "City Care",
        "Lifeline", "Global Care", "Metro Hospital", "Star Hospital", "Sunrise",
        "Rainbow", "Manipal", "Narayana", "Aster", "Columbia Asia",
    ],
    "Hotel": [
        "Comfort Inn", "Royal Residency", "Grand Palace", "Sai Hotel",
        "Park View", "Elite Suites", "Heritage Inn", "Lotus Hotel",
        "Crown Residency", "Capital Stay", "Treebo", "FabHotel", "OYO Premium",
    ],
    "School": [
        "DPS", "Modern School", "St. Mary's Convent", "Sunrise Academy",
        "Cambridge International", "Ryan International", "Delhi Public School",
        "Spring Dale", "Little Flower", "Oxford Public School",
        "Kendriya Vidyalaya", "Jawahar Navodaya", "DAV Public School",
    ],
    "Salon": [
        "Jawed Habib", "Looks Studio", "Naturals", "Green Trends",
        "Lakme Salon", "Mirror Beauty", "Style Studio", "Glamour Zone",
        "Scissors & Comb", "Hair Story", "Enrich Salon", "Jean-Claude Biguine",
    ],
    "Gym": [
        "Gold's Gym", "Fitness First", "Anytime Fitness", "Cult.fit",
        "Snap Fitness", "Iron Paradise", "Power Zone Gym", "Body Flex",
        "Planet Fitness", "F45 Training", "CrossFit Studio", "Prime Fitness",
    ],
    "Pharmacy": [
        "MedPlus", "Apollo Pharmacy", "Wellness Forever", "Jan Aushadhi",
        "Dawa Bazar", "Life Care Pharmacy", "Sanjeevani Medical", "Amrut Pharma",
        "Healthkart", "Sasta Sundar", "NetMeds Store", "1mg Pharmacy",
    ],
    "Bank": [
        "SBI Branch", "HDFC Bank", "ICICI Bank", "Axis Bank",
        "PNB Branch", "Canara Bank", "Union Bank", "Bank of Baroda",
        "Kotak Mahindra Bank", "Yes Bank", "IndusInd Bank", "Bank of India",
    ],
    "Supermarket": [
        "Big Bazaar", "Reliance Fresh", "D-Mart", "More Supermarket",
        "Spencer's Retail", "Nature's Basket", "Spar Hypermarket",
        "Star Bazaar", "Vishal Mega Mart", "Easyday", "Heritage Fresh",
    ],
    "Clinic": [
        "Family Health Clinic", "Wellness Point", "Arogya Clinic",
        "Pulse Clinic", "Prime Health", "Nirog Clinic", "Svastha Centre",
        "MediCare Clinic", "Life Health", "Quick Heal Clinic",
        "Dr. Sharma Clinic", "Swasthya Clinic",
    ],
}

STREET_TYPES = [
    "Road", "Street", "Marg", "Nagar", "Colony",
    "Sector", "Phase", "Enclave", "Vihar", "Layout",
    "Chowk", "Bazaar", "Lane", "Cross", "Avenue",
]

# Area names that sound plausible across many Indian cities
AREA_NAMES = [
    "Andheri", "Koramangala", "Connaught Place", "Anna Nagar",
    "Banjara Hills", "Kothrud", "Salt Lake", "Satellite", "Malviya Nagar",
    "Adajan", "Vaishali Nagar", "Paldi", "Laxmi Nagar", "Shivaji Nagar",
    "MG Road", "FC Road", "Brigade Road", "Commercial Street",
    "Indiranagar", "Jayanagar", "Rajouri Garden", "Rohini",
    "Dwarka", "Powai", "Thane West", "Viman Nagar", "Kharadi",
]

# Valid Indian mobile prefixes (as of 2024)
MOBILE_PREFIXES = [
    "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
    "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "90", "91", "92", "93", "94", "95", "96", "97", "98", "99",
]


# ─── Generator Class ──────────────────────────────────────────────────────────
class MockDataGenerator:

    def _phone(self) -> str:
        prefix = random.choice(MOBILE_PREFIXES)
        number = random.randint(10_000_000, 99_999_999)
        return f"+91-{prefix}{number}"

    def _address(self, city: str) -> str:
        num    = random.randint(1, 999)
        area   = random.choice(AREA_NAMES)
        stype  = random.choice(STREET_TYPES)
        return f"{num}, {area} {stype}, {city}"

    def _name(self, category: str) -> str:
        base_names = BUSINESS_NAMES.get(category, ["Business Centre"])
        name       = random.choice(base_names)
        suffixes   = ["", "", "", " & Co.", " Pvt. Ltd.", " Services", " Centre"]
        return f"{name}{random.choice(suffixes)}"

    def generate_one(
        self,
        category: str | None = None,
        city:     str | None = None,
        source:   str | None = None,
    ) -> dict:
        category = category or random.choice(CATEGORIES)
        city     = city     or random.choice(CITIES)
        source   = source   or random.choice(SOURCES)

        # ~15% of records have no phone (realistic)
        phone = self._phone() if random.random() > 0.15 else None

        return {
            "business_name": self._name(category),
            "category":      category,
            "city":          city,
            "address":       self._address(city),
            "phone":         phone,
            "source":        source,
        }

    def generate_batch(self, count: int) -> list[dict]:
        """
        Generate `count` records with balanced distribution across
        cities, categories, and sources.
        """
        records = []

        # Even spread across all combinations
        combinations = [
            (city, cat, src)
            for city in CITIES
            for cat  in CATEGORIES
            for src  in SOURCES
        ]
        random.shuffle(combinations)

        per_combo = max(1, count // len(combinations))

        for city, cat, src in combinations:
            for _ in range(per_combo):
                records.append(self.generate_one(cat, city, src))
            if len(records) >= count:
                break

        # Top up if needed (can happen due to integer division)
        while len(records) < count:
            records.append(self.generate_one())

        random.shuffle(records)
        return records[:count]


# ─── Standalone run (for testing) ────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd

    gen = MockDataGenerator()
    data = gen.generate_batch(600)
    df = pd.DataFrame(data)
    df["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Generated {len(df)} records")
    print(df.head(10).to_string(index=False))
    print("\nCity distribution:")
    print(df["city"].value_counts())
    print("\nCategory distribution:")
    print(df["category"].value_counts())
    print("\nSource distribution:")
    print(df["source"].value_counts())

    df.to_csv("mock_listings.csv", index=False)
    print("\nSaved to mock_listings.csv")
