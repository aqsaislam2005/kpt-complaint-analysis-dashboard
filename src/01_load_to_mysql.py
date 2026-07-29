"""
Step 1: Load the raw complaint CSV into the MySQL `complaints` table.

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import mysql.connector
from config import MYSQL_CONFIG, RAW_CSV, COLUMN_MAP


def load_data():
    df = pd.read_csv(RAW_CSV)
    df = df.rename(columns={v: k for k, v in COLUMN_MAP.items()})
    df = df.where(pd.notnull(df), None)  # NaN -> None for MySQL

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO complaints
        (original_id, complaint_text, category, department, status,
         customer_id, date_received, date_resolved)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = []
    for _, r in df.iterrows():
        rows.append((
            str(r.get("complaint_id")),
            r.get("complaint_text"),
            r.get("category"),
            r.get("department"),
            r.get("status") or "Open",
            r.get("customer_id"),
            r.get("date_received"),
            r.get("date_resolved") if r.get("date_resolved") else None,
        ))

    cursor.executemany(insert_query, rows)
    conn.commit()
    print(f"Inserted {cursor.rowcount} rows into `complaints` table.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    load_data()
