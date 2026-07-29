"""
Step 5: When do complaints happen most? Analyzes complaints by hour of day,
day of week, and month — and generates charts for the report/dashboard.


"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

from config import CATEGORIZED_CSV, FINAL_CSV, CHART_DIR

sns.set_theme(style="whitegrid")


def add_time_features(df):
    df["date_received"] = pd.to_datetime(df["date_received"])
    df["complaint_hour"] = df["date_received"].dt.hour
    df["complaint_day_of_week"] = df["date_received"].dt.day_name()
    df["complaint_month"] = df["date_received"].dt.month_name()
    df["complaint_year"] = df["date_received"].dt.year
    return df


def plot_by_hour(df):
    plt.figure(figsize=(10, 5))
    order = list(range(24))
    sns.countplot(x="complaint_hour", data=df, order=order, color="#4C72B0")
    plt.title("Complaints by Hour of Day")
    plt.xlabel("Hour (24h)")
    plt.ylabel("Number of Complaints")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "complaints_by_hour.png"), dpi=150)
    plt.close()


def plot_by_day(df):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    plt.figure(figsize=(9, 5))
    sns.countplot(x="complaint_day_of_week", data=df, order=order, color="#55A868")
    plt.title("Complaints by Day of Week")
    plt.xlabel("Day")
    plt.ylabel("Number of Complaints")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "complaints_by_day.png"), dpi=150)
    plt.close()


def plot_by_month(df):
    order = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
    plt.figure(figsize=(11, 5))
    sns.countplot(x="complaint_month", data=df, order=order, color="#C44E52")
    plt.title("Complaints by Month")
    plt.xlabel("Month")
    plt.ylabel("Number of Complaints")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "complaints_by_month.png"), dpi=150)
    plt.close()


def plot_category_by_month_heatmap(df):
    cat_col = "final_category" if "final_category" in df.columns else "category"
    order = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
    pivot = pd.crosstab(df[cat_col], df["complaint_month"])
    pivot = pivot.reindex(columns=[m for m in order if m in pivot.columns])

    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt="d", linewidths=0.5)
    plt.title("Complaint Category vs Month Heatmap")
    plt.xlabel("Month")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "category_month_heatmap.png"), dpi=150)
    plt.close()


def plot_sentiment_over_time(df):
    monthly_sentiment = df.groupby([df["date_received"].dt.to_period("M"), "sentiment_label"]).size().unstack(fill_value=0)
    monthly_sentiment.index = monthly_sentiment.index.astype(str)

    plt.figure(figsize=(12, 5))
    monthly_sentiment.plot(kind="bar", stacked=True, ax=plt.gca(),
                            color={"Positive": "#55A868", "Negative": "#C44E52", "Neutral": "#8172B2"})
    plt.title("Sentiment Trend Over Time")
    plt.xlabel("Month")
    plt.ylabel("Number of Complaints")
    plt.legend(title="Sentiment")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "sentiment_over_time.png"), dpi=150)
    plt.close()


def generate_wordclouds(df):
    cat_col = "final_category" if "final_category" in df.columns else "category"
    wc_dir = os.path.join(CHART_DIR, "wordclouds")
    os.makedirs(wc_dir, exist_ok=True)

    for cat in df[cat_col].dropna().unique():
        text = " ".join(df[df[cat_col] == cat]["complaint_text_clean"].dropna().astype(str))
        if not text.strip():
            continue
        wc = WordCloud(width=800, height=400, background_color="white").generate(text)
        safe_name = str(cat).replace("/", "_").replace(" ", "_")
        wc.to_file(os.path.join(wc_dir, f"wordcloud_{safe_name}.png"))

    print(f"Word clouds saved to {wc_dir}")


def main():
    df = pd.read_csv(CATEGORIZED_CSV)
    df = add_time_features(df)

    print("Generating time-pattern charts...")
    plot_by_hour(df)
    plot_by_day(df)
    plot_by_month(df)
    plot_category_by_month_heatmap(df)
    plot_sentiment_over_time(df)
    generate_wordclouds(df)

    print(f"\nAll charts saved to {CHART_DIR}")

    print("\nPeak hour:", df["complaint_hour"].value_counts().idxmax())
    print("Peak day:", df["complaint_day_of_week"].value_counts().idxmax())
    print("Peak month:", df["complaint_month"].value_counts().idxmax())

    df.to_csv(FINAL_CSV, index=False)
    print(f"\nSaved final dataset (with time features) to {FINAL_CSV}")


if __name__ == "__main__":
    main()
