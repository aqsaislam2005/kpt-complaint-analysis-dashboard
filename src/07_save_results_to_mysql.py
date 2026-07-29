import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import mysql.connector
from config import MYSQL_CONFIG, FINAL_CSV


def clean(value):
    """Convert any NaN/NaT/missing value to None so MySQL accepts it."""
    if pd.isna(value):
        return None
    return value


def main():
    df = pd.read_csv(FINAL_CSV)

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM complaint_analysis")

    insert_query = """
        INSERT INTO complaint_analysis
        (complaint_id, sentiment_label, sentiment_score, sentiment_model_used,
         predicted_category, category_confidence,
         complaint_hour, complaint_day_of_week, complaint_month, complaint_year,
         resolution_time_hours, predicted_resolution_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = []
    for _, r in df.iterrows():
        hour = clean(r.get("complaint_hour"))
        year = clean(r.get("complaint_year"))
        rows.append((
            int(r["complaint_id"]),
            clean(r.get("sentiment_label")),
            clean(r.get("sentiment_score")),
            clean(r.get("sentiment_model_used")),
            clean(r.get("predicted_category")),
            clean(r.get("category_confidence")),
            int(hour) if hour is not None else None,
            clean(r.get("complaint_day_of_week")),
            clean(r.get("complaint_month")),
            int(year) if year is not None else None,
            clean(r.get("resolution_time_hours")),
            clean(r.get("predicted_resolution_hours")),
        ))

    cursor.executemany(insert_query, rows)
    conn.commit()
    print(f"Inserted {cursor.rowcount} rows into `complaint_analysis` table.")
    print("Pipeline complete! Query `complaints_full_view` in MySQL, or launch the dashboard:")
    print("   streamlit run dashboard/app.py")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()