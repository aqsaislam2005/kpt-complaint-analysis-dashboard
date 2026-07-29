"""
Step 2: Clean complaint data — handle missing values, duplicates, and
normalize complaint text for downstream NLP tasks (sentiment + categorization).

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import pandas as pd
from sqlalchemy import create_engine
from config import get_sqlalchemy_uri, CLEANED_CSV, TEXT_IS_URDU_OR_MIXED

import nltk
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")
from nltk.corpus import stopwords

ENGLISH_STOPWORDS = set(stopwords.words("english"))

# Minimal Roman-Urdu stopword list — extend this if your KPT data has
# Urdu / Roman Urdu complaint text. Toggle TEXT_IS_URDU_OR_MIXED in config.py.
ROMAN_URDU_STOPWORDS = {
    "hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "aur", "ye", "yeh",
    "wo", "woh", "tha", "thi", "the", "hoon", "ho", "kar", "kya", "nahi",
}


def clean_text(text: str) -> str:
    if not isinstance(text, str) or text.strip() == "":
        return ""

    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)          # URLs
    text = re.sub(r"[^a-zA-Z\s]", " ", text)             # keep letters only
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()
    stop_set = ENGLISH_STOPWORDS | (ROMAN_URDU_STOPWORDS if TEXT_IS_URDU_OR_MIXED else set())
    words = [w for w in words if w not in stop_set and len(w) > 2]

    return " ".join(words)


def main():
    engine = create_engine(get_sqlalchemy_uri())
    df = pd.read_sql("SELECT * FROM complaints", engine)
    print(f"Loaded {len(df)} rows from MySQL.")

    before = len(df)

    # 1. Drop exact duplicate complaints (same customer, text, and timestamp)
    df = df.drop_duplicates(subset=["complaint_text", "customer_id", "date_received"])
    print(f"Removed {before - len(df)} duplicate rows.")

    # 2. Drop rows with empty complaint text — nothing to analyze
    df = df[df["complaint_text"].notna() & (df["complaint_text"].str.strip() != "")]

    # 3. Fill missing categorical fields
    df["department"] = df["department"].fillna("Unassigned")
    df["status"] = df["status"].fillna("Open")
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")

    # 4. Parse dates properly
    df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
    df["date_resolved"] = pd.to_datetime(df["date_resolved"], errors="coerce")
    df = df[df["date_received"].notna()]

    # 5. Clean complaint text for NLP
    df["complaint_text_clean"] = df["complaint_text"].apply(clean_text)
    df = df[df["complaint_text_clean"].str.strip() != ""]

    # 6. Derive resolution time in hours (where available)
    resolved_mask = df["date_resolved"].notna()
    df.loc[resolved_mask, "resolution_time_hours"] = (
        (df.loc[resolved_mask, "date_resolved"] - df.loc[resolved_mask, "date_received"])
        .dt.total_seconds() / 3600
    )

    print(f"Final cleaned dataset: {len(df)} rows.")
    df.to_csv(CLEANED_CSV, index=False)
    print(f"Saved cleaned data to {CLEANED_CSV}")


if __name__ == "__main__":
    main()
