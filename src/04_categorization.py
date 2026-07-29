"""
Step 4: What kind of complaint is it? Trains a TF-IDF + Logistic Regression
classifier on the labeled portion of the data, then predicts categories for
any complaints that don't already have one (common in real complaint logs).

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from config import SENTIMENT_CSV, CATEGORIZED_CSV, MODEL_DIR


def main():
    df = pd.read_csv(SENTIMENT_CSV)
    df["complaint_text_clean"] = df["complaint_text_clean"].fillna("")

    labeled = df[df["category"].notna() & (df["category"].str.strip() != "")]
    unlabeled = df[df["category"].isna() | (df["category"].str.strip() == "")]

    print(f"Labeled complaints: {len(labeled)} | Unlabeled: {len(unlabeled)}")

    if len(labeled) < 20:
        print("Not enough labeled data to train a classifier. "
              "Consider manually labeling a sample, or use topic modeling instead "
              "(see README extension ideas: BERTopic/LDA).")
        df["predicted_category"] = df["category"]
        df["category_confidence"] = 1.0
        df.to_csv(CATEGORIZED_CSV, index=False)
        return

    X = labeled["complaint_text_clean"]
    y = labeled["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # --- Model 1: Logistic Regression ---
    logreg = LogisticRegression(max_iter=1000)
    logreg.fit(X_train_tfidf, y_train)
    lr_preds = logreg.predict(X_test_tfidf)
    lr_acc = accuracy_score(y_test, lr_preds)

    # --- Model 2: Naive Bayes (comparison) ---
    nb = MultinomialNB()
    nb.fit(X_train_tfidf, y_train)
    nb_preds = nb.predict(X_test_tfidf)
    nb_acc = accuracy_score(y_test, nb_preds)

    print(f"\nLogistic Regression accuracy: {lr_acc:.2%}")
    print(f"Naive Bayes accuracy:         {nb_acc:.2%}")

    best_model, best_name = (logreg, "logistic_regression") if lr_acc >= nb_acc else (nb, "naive_bayes")
    print(f"\nBest model: {best_name}")
    print("\nClassification report (best model):")
    best_preds = lr_preds if best_name == "logistic_regression" else nb_preds
    print(classification_report(y_test, best_preds))

    # Save model + vectorizer for reuse (e.g. by the dashboard or new data)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "category_classifier.pkl"))
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
    print(f"Saved best model to {MODEL_DIR}/category_classifier.pkl")

    # Predict categories for unlabeled rows
    df["predicted_category"] = df["category"]
    df["category_confidence"] = 1.0

    if len(unlabeled) > 0:
        X_unlabeled_tfidf = vectorizer.transform(unlabeled["complaint_text_clean"])
        preds = best_model.predict(X_unlabeled_tfidf)

        if hasattr(best_model, "predict_proba"):
            probs = best_model.predict_proba(X_unlabeled_tfidf).max(axis=1)
        else:
            probs = [None] * len(preds)

        df.loc[unlabeled.index, "predicted_category"] = preds
        df.loc[unlabeled.index, "category_confidence"] = probs

    df["final_category"] = df["category"].fillna(df["predicted_category"])

    df.to_csv(CATEGORIZED_CSV, index=False)
    print(f"\nSaved categorized data to {CATEGORIZED_CSV}")
    print("\nFinal category distribution:")
    print(df["final_category"].value_counts())


if __name__ == "__main__":
    main()
