"""
Step 8: Simulate the complaint WORKFLOW — the journey a complaint takes from
being filed to being resolved.

Real KPT data likely doesn't track this yet, so this generates a realistic
synthetic workflow for each complaint already in your dataset:

    Complaint Filed
          -> Public Relations Department (first point of contact)
          -> Forwarded to a Department (based on category)
             - 80% of the time: forwarded to the CORRECT department first try
             - 20% of the time: forwarded to a WRONG department first,
               which then bounces it to the correct one (extra delay)
          -> Department reviews and adds a comment
          -> Marked Resolved / Unresolved

This lets you analyze: how often complaints get misrouted, which departments
misroute most, how much time misrouting adds, and what comments departments
leave at each stage.

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import pandas as pd
import numpy as np
from datetime import timedelta

from config import FINAL_CSV, OUTPUT_DIR, MYSQL_CONFIG

random.seed(7)
np.random.seed(7)

WORKFLOW_CSV = os.path.join(OUTPUT_DIR, "complaint_workflow.csv")

# Correct department for each category (same mapping used in data generation)
CATEGORY_TO_DEPT = {
    "Billing Issue": "Billing",
    "Service Delay": "Operations",
    "Staff Behavior": "Customer Support",
    "Infrastructure": "Maintenance",
    "Safety Concern": "Security",
    "Corruption/Bribery": "Administration",
    "Appreciation": "Customer Support",
}
ALL_DEPARTMENTS = list(set(CATEGORY_TO_DEPT.values()))

# How often each category gets misrouted on the first try.
MISROUTE_RATE_BY_CATEGORY = {
    "Billing Issue": 0.10,        # very distinct wording (bills, fees, payments) -> rarely misrouted
    "Safety Concern": 0.10,       # urgent/distinct wording -> rarely misrouted
    "Staff Behavior": 0.15,
    "Service Delay": 0.20,
    "Infrastructure": 0.20,
    "Corruption/Bribery": 0.30,   # sensitive, sometimes filed under Admin or Staff Behavior by mistake
    "Appreciation": 0.30,         # positive feedback isn't always obviously "a complaint" -> often misfiled
}
DEFAULT_MISROUTE_RATE = 0.20

# Sample comments a department might leave — varied by whether resolved or not
RESOLVED_COMMENTS = [
    "Issue verified and resolved after review.",
    "Corrected the error and notified the customer.",
    "Resolved following standard procedure.",
    "Confirmed with the customer that the issue is fixed.",
    "Completed the requested action successfully.",
]
UNRESOLVED_COMMENTS = [
    "Still under investigation, pending further review.",
    "Waiting on additional information from the customer.",
    "Escalated to senior staff for further action.",
    "Requires field visit before it can be closed.",
    "On hold due to resource availability.",
]
MISROUTE_COMMENTS = [
    "This complaint does not belong to our department, forwarding to the correct team.",
    "Incorrectly routed here, reassigning to the appropriate department.",
    "Not within our scope, sending to the relevant department.",
]


def simulate_workflow_for_complaint(row):
    """Returns a list of workflow stage dicts for one complaint."""
    complaint_id = row["complaint_id"]
    category = row.get("final_category", row.get("category"))
    correct_dept = CATEGORY_TO_DEPT.get(category, "Customer Support")
    date_received = pd.to_datetime(row["date_received"])
    final_status = row.get("status", "Open")

    stages = []

    # Stage 1: Public Relations receives it (always first)
    pr_time = date_received + timedelta(hours=np.random.uniform(0.1, 2))
    stages.append({
        "complaint_id": complaint_id,
        "stage_order": 1,
        "department": "Public Relations",
        "action": "Received",
        "routed_correctly": None,
        "comment": "Complaint logged and reviewed for routing.",
        "stage_timestamp": pr_time,
        "resolution_status": None,
    })

   # Decide: was it forwarded correctly the first time?
    # Rate depends on the category (see MISROUTE_RATE_BY_CATEGORY above)
    misroute_rate = MISROUTE_RATE_BY_CATEGORY.get(category, DEFAULT_MISROUTE_RATE)
    forwarded_correctly_first_try = random.random() > misroute_rate

    if forwarded_correctly_first_try:
        forward_time = pr_time + timedelta(hours=np.random.uniform(1, 8))
        stages.append({
            "complaint_id": complaint_id,
            "stage_order": 2,
            "department": correct_dept,
            "action": "Forwarded (Correct)",
            "routed_correctly": True,
            "comment": f"Received from Public Relations, correctly routed for {category}.",
            "stage_timestamp": forward_time,
            "resolution_status": None,
        })
        last_time = forward_time
        last_dept_order = 2
    else:
        wrong_dept = random.choice([d for d in ALL_DEPARTMENTS if d != correct_dept])
        wrong_time = pr_time + timedelta(hours=np.random.uniform(1, 8))
        stages.append({
            "complaint_id": complaint_id,
            "stage_order": 2,
            "department": wrong_dept,
            "action": "Forwarded (Incorrect)",
            "routed_correctly": False,
            "comment": random.choice(MISROUTE_COMMENTS),
            "stage_timestamp": wrong_time,
            "resolution_status": None,
        })
        bounce_time = wrong_time + timedelta(hours=np.random.uniform(4, 24))
        stages.append({
            "complaint_id": complaint_id,
            "stage_order": 3,
            "department": correct_dept,
            "action": "Forwarded (Re-routed)",
            "routed_correctly": True,
            "comment": f"Re-routed from {wrong_dept}; now correctly assigned for {category}.",
            "stage_timestamp": bounce_time,
            "resolution_status": None,
        })
        last_time = bounce_time
        last_dept_order = 3

    is_resolved = final_status in ("Resolved", "Closed")
    resolve_time = last_time + timedelta(hours=np.random.uniform(4, 96))
    stages.append({
        "complaint_id": complaint_id,
        "stage_order": last_dept_order + 1,
        "department": correct_dept,
        "action": "Reviewed",
        "routed_correctly": True,
        "comment": random.choice(RESOLVED_COMMENTS if is_resolved else UNRESOLVED_COMMENTS),
        "stage_timestamp": resolve_time,
        "resolution_status": "Resolved" if is_resolved else "Unresolved",
    })

    return stages


def main():
    df = pd.read_csv(FINAL_CSV)
    print(f"Simulating workflow for {len(df)} complaints...")

    all_stages = []
    for _, row in df.iterrows():
        all_stages.extend(simulate_workflow_for_complaint(row))

    workflow_df = pd.DataFrame(all_stages)
    workflow_df.to_csv(WORKFLOW_CSV, index=False)
    print(f"Saved {len(workflow_df)} workflow stage records to {WORKFLOW_CSV}")

    first_routing = workflow_df[workflow_df["stage_order"] == 2]
    misroute_rate = (first_routing["routed_correctly"] == False).mean()
    print(f"\nFirst-attempt misrouting rate: {misroute_rate:.1%}")

    final_stages = workflow_df.sort_values("stage_order").groupby("complaint_id").tail(1)
    resolved_rate = (final_stages["resolution_status"] == "Resolved").mean()
    print(f"Overall resolved rate: {resolved_rate:.1%}")


if __name__ == "__main__":
    main()