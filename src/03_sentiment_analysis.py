"""
Step 3: Sentiment analysis on each complaint — is the tone positive or
negative? Runs TWO models so you can compare them in your report:

  1. VADER  - fast, rule-based, no training needed (baseline)
  2. DistilBERT (HuggingFace transformer) - more accurate, context-aware

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import CLEANED_CSV, SENTIMENT_CSV

# Which model's output the dashboard/final columns should use: "vader" or "transformer"
SENTIMENT_MODEL = "transformer"


def run_vader(df):
    analyzer = SentimentIntensityAnalyzer()

    def score_row(text):
        s = analyzer.polarity_scores(text)
        compound = s["compound"]
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        return pd.Series([label, compound])

    df[["vader_label", "vader_score"]] = df["complaint_text"].fillna("").apply(score_row)
    return df


def run_transformer(df):
    from transformers import pipeline
    print("Loading transformer model (distilbert-base-uncased-finetuned-sst-2-english)...")
    clf = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        truncation=True,
    )

    texts = df["complaint_text"].fillna("").tolist()
    results = []
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        results.extend(clf(batch))
        print(f"  scored {min(i + batch_size, len(texts))}/{len(texts)}")

    labels = [r["label"].capitalize() for r in results]  # POSITIVE/NEGATIVE -> Positive/Negative
    scores = [r["score"] if r["label"] == "POSITIVE" else -r["score"] for r in results]

    df["transformer_label"] = labels
    df["transformer_score"] = scores
    return df


def main():
    df = pd.read_csv(CLEANED_CSV)
    print(f"Running sentiment analysis on {len(df)} complaints...")

    df = run_vader(df)
    print("VADER done.")

    try:
        df = run_transformer(df)
        print("Transformer model done.")
    except Exception as e:
        print(f"Transformer model unavailable ({e}); falling back to VADER only.")
        global SENTIMENT_MODEL
        SENTIMENT_MODEL = "vader"

    # Unified columns used by the rest of the pipeline
    if SENTIMENT_MODEL == "transformer" and "transformer_label" in df.columns:
        df["sentiment_label"] = df["transformer_label"]
        df["sentiment_score"] = df["transformer_score"]
        df["sentiment_model_used"] = "transformer"
    else:
        df["sentiment_label"] = df["vader_label"]
        df["sentiment_score"] = df["vader_score"]
        df["sentiment_model_used"] = "vader"

    df.to_csv(SENTIMENT_CSV, index=False)
    print(f"Saved sentiment results to {SENTIMENT_CSV}")

    print("\nSentiment distribution:")
    print(df["sentiment_label"].value_counts())

    # Model agreement check — useful stat for your report
    if "vader_label" in df.columns and "transformer_label" in df.columns:
        agreement = (df["vader_label"] == df["transformer_label"]).mean()
        print(f"\nVADER vs Transformer agreement rate: {agreement:.1%}")


if __name__ == "__main__":
    main()
