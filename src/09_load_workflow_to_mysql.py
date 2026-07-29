"""
Step 9: Load the simulated workflow stages (from 08_generate_workflow.py)
into the MySQL `complaint_workflow` table.

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import mysql.connector
from config import MYSQL_CONFIG, OUTPUT_DIR

WORKFLOW_CSV = os.path.join(OUTPUT_DIR, "complaint_workflow.csv")


def clean(value):
    if pd.isna(value):
        return None
    return value


def main():
    df = pd.read_csv(WORKFLOW_CSV)

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM complaint_workflow")

    insert_query = """
        INSERT INTO complaint_workflow
        (complaint_id, stage_order, department, action, routed_correctly,
         comment, stage_timestamp, resolution_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = []
    for _, r in df.iterrows():
        routed = clean(r.get("routed_correctly"))
        rows.append((
            int(r["complaint_id"]),
            int(r["stage_order"]),
            clean(r.get("department")),
            clean(r.get("action")),
            bool(routed) if routed is not None else None,
            clean(r.get("comment")),
            clean(r.get("stage_timestamp")),
            clean(r.get("resolution_status")),
        ))

    cursor.executemany(insert_query, rows)
    conn.commit()
    print(f"Inserted {cursor.rowcount} workflow stage rows into `complaint_workflow` table.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()