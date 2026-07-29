
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from config import FINAL_CSV, MODEL_DIR


FEATURES = ["final_category", "department", "sentiment_label", "complaint_hour", "complaint_day_of_week"]
TARGET = "resolution_time_hours"


def main():
    df = pd.read_csv(FINAL_CSV)

    data = df[df[TARGET].notna()].copy()
    print(f"Training on {len(data)} resolved complaints with known resolution time.")

    if len(data) < 30:
        print("Not enough resolved complaints yet to train a reliable resolution-time model. "
              "Skipping — this will work once more complaints have status=Resolved/Closed.")
        return

    X = data[FEATURES]
    y = data[TARGET]

    categorical_features = ["final_category", "department", "sentiment_label", "complaint_day_of_week"]
    numeric_features = ["complaint_hour"]

    preprocessor = ColumnTransformer(transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ], remainder="passthrough")

    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)),
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"\nModel performance:")
    print(f"  Mean Absolute Error: {mae:.1f} hours")
    print(f"  R^2 score: {r2:.3f}")

    # Predict for the full dataset (including still-open complaints)
    df["predicted_resolution_hours"] = model.predict(df[FEATURES])

    df.to_csv(FINAL_CSV, index=False)
    joblib.dump(model, os.path.join(MODEL_DIR, "resolution_time_model.pkl"))
    print(f"\nSaved model to {MODEL_DIR}/resolution_time_model.pkl")
    print(f"Updated {FINAL_CSV} with predicted_resolution_hours for every complaint.")


if __name__ == "__main__":
    main()
