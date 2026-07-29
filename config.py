import os

# ---------------------------------------------------------------------------
# MySQL connection settings
# ---------------------------------------------------------------------------
MYSQL_CONFIG = {
    "host": os.environ.get("KPT_DB_HOST", "localhost"),
    "user": os.environ.get("KPT_DB_USER", "root"),
    "password": os.environ.get("KPT_DB_PASSWORD", "September30@"),
    "database": os.environ.get("KPT_DB_NAME", "kpt_complaints"),
    "port": int(os.environ.get("KPT_DB_PORT", 3306)),
}

from urllib.parse import quote_plus

def get_sqlalchemy_uri():
    c = MYSQL_CONFIG
    user = quote_plus(c['user'])
    password = quote_plus(c['password'])
    return f"mysql+mysqlconnector://{user}:{password}@{c['host']}:{c['port']}/{c['database']}"

# ---------------------------------------------------------------------------
# File paths (shared across all scripts)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_DIR = os.path.join(OUTPUT_DIR, "models")
CHART_DIR = os.path.join(OUTPUT_DIR, "charts")

RAW_CSV = os.path.join(DATA_DIR, "complaints_raw.csv")
CLEANED_CSV = os.path.join(OUTPUT_DIR, "complaints_cleaned.csv")
SENTIMENT_CSV = os.path.join(OUTPUT_DIR, "complaints_with_sentiment.csv")
CATEGORIZED_CSV = os.path.join(OUTPUT_DIR, "complaints_with_category.csv")
FINAL_CSV = os.path.join(OUTPUT_DIR, "complaints_final.csv")

for d in (DATA_DIR, OUTPUT_DIR, MODEL_DIR, CHART_DIR):
    os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------------------
# Column mapping — if your real KPT export uses different column names,
# change the RIGHT-HAND side (the value) to match your actual CSV headers.
# The LEFT-HAND side (key) is what the rest of the pipeline expects internally.
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "complaint_id": "complaint_id",
    "complaint_text": "complaint_text",
    "category": "category",
    "date_received": "date_received",
    "date_resolved": "date_resolved",
    "status": "status",
    "department": "department",
    "customer_id": "customer_id",
}

# If your complaint text is in Urdu / Roman Urdu, flip this to True.
# See src/02_data_cleaning.py for how this is used.
TEXT_IS_URDU_OR_MIXED = False
