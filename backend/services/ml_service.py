"""
ML Service — handles model training, evaluation, and prediction.
"""

import time
import numpy as np
import pandas as pd
from typing import Any, Optional, cast
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)

# In-memory model store
_models: dict = {}
_scaler: Optional[StandardScaler] = None
_feature_columns: list[str] = []
_label_encoder: Optional[LabelEncoder] = None


def preprocess(df: pd.DataFrame, target_col: str) -> tuple:
    """Preprocess dataframe: encode, scale, split."""
    global _scaler, _feature_columns, _label_encoder

    X = df.drop(columns=[target_col]).copy()
    y = df[target_col].copy()

    # Encode target if not numeric
    if y.dtype == object:
        le = LabelEncoder()
        _label_encoder = le
        y = pd.Series(cast(Any, le.fit_transform(y)), index=y.index)

    # Fill missing values
    numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = X.select_dtypes(include="object").columns.tolist()

    for col in numeric_cols:
        X[col] = X[col].fillna(X[col].mean())
    for col in cat_cols:
        mode_val = X[col].mode()
        if len(mode_val) > 0:
            X[col] = X[col].fillna(mode_val.iloc[0])

    # One-hot encode categoricals
    X = pd.get_dummies(X, drop_first=True)
    _feature_columns = X.columns.tolist()

    # Scale numeric columns
    _scaler = StandardScaler()
    scaled_cols = [c for c in X.columns if c in numeric_cols]
    if scaled_cols:
        X[scaled_cols] = _scaler.fit_transform(X[scaled_cols])

    # Safe stratified split
    class_counts = Counter(y)
    min_class = min(class_counts.values())
    stratify_y = y if min_class >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify_y)
    return (X_train, X_test, y_train, y_test)


def _compute_metrics(model_name: str, y_test, y_pred, X: pd.DataFrame) -> dict:
    """Compute all evaluation metrics for a trained model."""
    avg = "weighted"
    cm = confusion_matrix(y_test, y_pred).tolist()
    report = classification_report(y_test, y_pred, output_dict=True)

    zd = cast(Any, 0)
    result: dict[str, Any] = {
        "model_name": model_name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, average=avg, zero_division=zd)), 4),
        "recall": round(float(recall_score(y_test, y_pred, average=avg, zero_division=zd)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, average=avg, zero_division=zd)), 4),
        "confusion_matrix": cm,
        "classification_report": report,
        "feature_importance": None
    }

    # Feature importance for Random Forest
    rf_model = _models.get("random_forest")
    if model_name == "Random Forest" and rf_model is not None and hasattr(rf_model, "feature_importances_"):
        importances = getattr(rf_model, "feature_importances_", [])
        fi = {
            str(col): round(float(imp), 4)
            for col, imp in zip(X.columns.tolist(), importances)
        }
        # Top 15 features sorted by importance
        sorted_items = sorted(fi.items(), key=lambda item: item[1], reverse=True)[:15]
        result["feature_importance"] = {k: v for k, v in sorted_items}

    return result


def train_models(
    df: pd.DataFrame,
    target_col: str,
    model_type: str = "random_forest",
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    lr_max_iter: int = 1000
) -> dict:
    start_time = time.time()
    X_train, X_test, y_train, y_test = preprocess(df, target_col)

    results = []
    models_to_train = []

    if model_type in ("random_forest", "both"):
        models_to_train.append("random_forest")
    if model_type in ("logistic_regression", "both"):
        models_to_train.append("logistic_regression")

    for m in models_to_train:
        if m == "random_forest":
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                n_jobs=-1
            )
            display_name = "Random Forest"
        else:
            model = LogisticRegression(
                max_iter=lr_max_iter,
                random_state=42,
                solver="lbfgs"
            )
            display_name = "Logistic Regression"

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        _models[m] = model

        metrics = _compute_metrics(display_name, y_test, y_pred, X_test)
        results.append(metrics)

    elapsed = round(time.time() - start_time, 2)
    return {
        "success": True,
        "message": f"Trained {len(results)} model(s) in {elapsed}s",
        "results": results,
        "training_time_seconds": elapsed
    }


def predict(features: dict, model_type: str = "random_forest") -> dict:
    """Make a single prediction using a trained model."""
    key = "random_forest" if model_type == "random_forest" else "logistic_regression"
    model = _models.get(key)

    if not model:
        return {"error": f"Model '{model_type}' not trained yet. Call /api/analytics/train first."}

    if not _feature_columns:
        return {"error": "No feature columns available. Please train a model first."}

    # Build feature vector
    input_df = pd.DataFrame([features])
    input_df = pd.get_dummies(input_df, drop_first=True)

    # Align columns with training features
    for col in _feature_columns:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[_feature_columns]

    prediction = model.predict(input_df)[0]
    probabilities = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_df)[0].tolist()

    # Decode label if encoder was used
    if _label_encoder:
        prediction = _label_encoder.inverse_transform([prediction])[0]

    return {
        "prediction": str(prediction),
        "probability": probabilities,
        "model_used": model_type
    }
