"""
Generates a realistic SYNTHETIC complaint dataset that mimics a utility /
transport authority complaint system (like KPT — Karachi Port Trust, or
similarly structured public service complaint logs).

"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from config import RAW_CSV

fake = Faker()
random.seed(42)
np.random.seed(42)

N_COMPLAINTS = 2500

CATEGORIES = {
    "Billing Issue": [
        "I was overcharged on my last bill and no one is responding.",
        "My bill amount doubled this month without any explanation.",
        "There is a billing error, I already paid but it still shows unpaid.",
        "Why is the late fee applied when I paid on time?",
        "The online payment portal charged me twice for the same bill.",
    ],
    "Service Delay": [
        "It has been three weeks and my complaint is still not resolved.",
        "No technician has visited despite multiple requests.",
        "The response time for service requests is unacceptably slow.",
        "I have been waiting since last month for this issue to be fixed.",
        "Staff keep telling me to wait but nothing happens.",
    ],
    "Staff Behavior": [
        "The staff at the counter was extremely rude to me today.",
        "I was treated very disrespectfully by the customer support agent.",
        "The employee refused to help and was arguing instead of assisting.",
        "Very unprofessional behavior from the officer on duty.",
        "The staff member was polite and handled my issue very well.",
    ],
    "Infrastructure": [
        "The road near the facility is damaged and causing accidents.",
        "There is a major leakage that has not been fixed for weeks.",
        "The equipment at the site is old and frequently malfunctions.",
        "Poor maintenance of the facility is causing repeated problems.",
        "The new infrastructure upgrade has improved things significantly.",
    ],
    "Safety Concern": [
        "There are serious safety hazards at the site that need urgent attention.",
        "No safety measures are in place despite previous warnings.",
        "I witnessed a near-accident due to lack of proper signage.",
        "Security personnel are not checking IDs properly at the gate.",
        "Thank you for quickly fixing the safety issue I reported earlier.",
    ],
    "Corruption/Bribery": [
        "I was asked to pay extra money to get my work done faster.",
        "An official demanded a bribe before processing my documents.",
        "There is clear favoritism and under-the-table dealing happening.",
    ],
    "Appreciation": [
        "I want to thank the team for resolving my issue so quickly.",
        "Excellent service today, very satisfied with the response.",
        "The new online system has made things much easier, well done.",
        "Great job by the support team, issue resolved within a day.",
    ],
}

DEPARTMENTS = ["Billing", "Operations", "Customer Support", "Maintenance",
               "Security", "IT/Online Services", "Administration"]

CATEGORY_TO_DEPT = {
    "Billing Issue": "Billing",
    "Service Delay": "Operations",
    "Staff Behavior": "Customer Support",
    "Infrastructure": "Maintenance",
    "Safety Concern": "Security",
    "Corruption/Bribery": "Administration",
    "Appreciation": "Customer Support",
}

STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

# Seasonal weighting so certain months have more complaints (mimics real
# patterns e.g. billing complaints spike after tariff changes, infrastructure
# complaints spike in monsoon season)
MONTH_WEIGHTS = {
    1: 0.8, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.2, 6: 1.4,
    7: 1.6, 8: 1.5, 9: 1.1, 10: 0.9, 11: 0.8, 12: 1.0,
}

# Certain hours of day see more complaints (business hours skew)
HOUR_WEIGHTS = np.array([
    0.2,0.1,0.1,0.1,0.1,0.2,0.4,0.8,1.5,1.8,1.9,1.7,
    1.3,1.6,1.8,1.7,1.5,1.2,0.8,0.5,0.4,0.3,0.3,0.2
])
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()


def random_datetime_2025():
    """Generate a random datetime in 2025 weighted toward certain months/hours."""
    months = list(MONTH_WEIGHTS.keys())
    weights = list(MONTH_WEIGHTS.values())
    month = random.choices(months, weights=weights)[0]

    day = random.randint(1, 28)
    hour = np.random.choice(range(24), p=HOUR_WEIGHTS)
    minute = random.randint(0, 59)

    return datetime(2025, month, day, int(hour), minute)


def generate_row(i):
    category = random.choices(
        list(CATEGORIES.keys()),
        weights=[0.22, 0.20, 0.15, 0.15, 0.10, 0.08, 0.10]
    )[0]
    text = random.choice(CATEGORIES[category])

    date_received = random_datetime_2025()
    status = random.choices(STATUSES, weights=[0.15, 0.20, 0.30, 0.35])[0]

    date_resolved = None
    if status in ("Resolved", "Closed"):
        # resolution time varies by category (billing resolved faster than infra)
        base_hours = {
            "Billing Issue": 48, "Service Delay": 120, "Staff Behavior": 72,
            "Infrastructure": 200, "Safety Concern": 90, "Corruption/Bribery": 150,
            "Appreciation": 24,
        }[category]
        resolution_hours = max(1, np.random.normal(base_hours, base_hours * 0.4))
        date_resolved = date_received + timedelta(hours=resolution_hours)

    return {
        "complaint_id": i,
        "complaint_text": text,
        "category": category if random.random() > 0.35 else None,  # 35% unlabeled on purpose
        "department": CATEGORY_TO_DEPT[category],
        "status": status,
        "customer_id": f"CUST{random.randint(1000, 9999)}",
        "date_received": date_received.strftime("%Y-%m-%d %H:%M:%S"),
        "date_resolved": date_resolved.strftime("%Y-%m-%d %H:%M:%S") if date_resolved else "",
    }


def main():
    print(f"Generating {N_COMPLAINTS} synthetic complaints...")
    rows = [generate_row(i) for i in range(1, N_COMPLAINTS + 1)]
    df = pd.DataFrame(rows)

    # inject a few messy rows on purpose, to mimic real-world data and give
    # the cleaning script something real to do
    dupe_rows = df.sample(20, random_state=1)
    df = pd.concat([df, dupe_rows], ignore_index=True)
    df.loc[df.sample(15, random_state=2).index, "complaint_text"] = ""
    df.loc[df.sample(10, random_state=3).index, "customer_id"] = None

    df.to_csv(RAW_CSV, index=False)
    print(f"Saved {len(df)} rows to {RAW_CSV}")
    print("\nCategory distribution (labeled rows only):")
    print(df["category"].value_counts())


if __name__ == "__main__":
    main()
