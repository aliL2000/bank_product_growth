"""Phase 2 baseline model: logistic regression on modeling_table.parquet.

Fits on train only, does a quick sanity check on val (ROC-AUC + top-1% lift
by predicted score) - not the full precision@K evaluation, which is a
separate, later step once LightGBM is also in the picture for comparison.

Feature choices:
- `renta_log` is used instead of `renta_imputed` - both encode the same
  income value, and feeding a linear model two collinear versions of the
  same signal doesn't add information, just noise to the coefficients.
- Continuous features are standardized (mean 0, std 1) using train-only
  statistics, same train-only rule as every imputation step so far
  (docs/decisions/002-train-val-split.md) - logistic regression's
  gradient-based solver converges poorly when features sit on very
  different scales (renta_log ~11-17 vs activity_index's 0/1).
- The 0/1 flag and one-hot columns are left unscaled; standardizing a
  binary indicator doesn't help the solver and would make its coefficient
  harder to read directly as "this category vs. not."
"""

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MODELING_TABLE_PATH = PROCESSED_DIR / "modeling_table.parquet"

CONTINUOUS_COLS = [
    "tenure_months",
    "activity_index",
    "product_count_prev",
    "age_years",
    "age_years_sq",
    "renta_log",
]
BINARY_COLS = [
    "tenure_missing",
    "activity_missing",
    "product_count_missing",
    "age_missing",
    "sexo_h",
    "sexo_v",
    "sexo_missing",
    "segmento_top",
    "segmento_particulares",
    "segmento_universitario",
    "segmento_missing",
    "renta_missing",
]
FEATURE_COLS = CONTINUOUS_COLS + BINARY_COLS


def load_train_val() -> pd.DataFrame:
    """Only train/val are needed today - test stays untouched until the
    final reported number (docs/decisions/004-three-way-split.md)."""
    df = pd.read_parquet(MODELING_TABLE_PATH, columns=FEATURE_COLS + ["adoption", "split"])
    return df[df["split"].isin(["train", "val"])]


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Select the feature matrix and cast the target to int (sklearn wants
    numeric, not pandas' nullable boolean dtype)."""
    X = df[FEATURE_COLS].copy()
    y = df["adoption"].astype("int8")
    return X, y


def scale_continuous(X_train: pd.DataFrame, X_val: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """Fit the scaler on train's continuous columns only, apply to both."""
    scaler = StandardScaler()
    X_train = X_train.copy()
    X_val = X_val.copy()
    X_train[CONTINUOUS_COLS] = scaler.fit_transform(X_train[CONTINUOUS_COLS])
    X_val[CONTINUOUS_COLS] = scaler.transform(X_val[CONTINUOUS_COLS])
    return X_train, X_val, scaler


def fit_baseline(X_train: pd.DataFrame, y_train: pd.Series) -> LogisticRegression:
    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    return model


def top_k_lift(y_true: pd.Series, scores, k_frac: float = 0.01) -> float:
    """Adoption rate among the top k_frac of rows by predicted score,
    relative to the overall rate - an intuitive stand-in for precision@K
    today; the real precision@K evaluation (with a fixed contact budget K,
    compared against random targeting) is next session's work."""
    k = max(1, int(len(y_true) * k_frac))
    order = pd.Series(scores).sort_values(ascending=False).index[:k]
    top_rate = y_true.iloc[order].mean()
    overall_rate = y_true.mean()
    return top_rate / overall_rate


def evaluate(model: LogisticRegression, X: pd.DataFrame, y: pd.Series, label: str) -> None:
    scores = model.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, scores)
    lift = top_k_lift(y, scores)
    print(f"{label}: ROC-AUC={auc:.4f}, top-1% lift={lift:.2f}x, n={len(y):,}, adoption_rate={y.mean():.3%}")


def print_coefficients(model: LogisticRegression) -> None:
    coefs = pd.Series(model.coef_[0], index=FEATURE_COLS).sort_values(key=abs, ascending=False)
    print("\ncoefficients (log-odds scale, sorted by |value|):")
    print(coefs.to_string())


if __name__ == "__main__":
    df = load_train_val()

    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)

    X_train, X_val, _ = scale_continuous(X_train, X_val)

    model = fit_baseline(X_train, y_train)

    evaluate(model, X_train, y_train, "train")
    evaluate(model, X_val, y_val, "val")
    print_coefficients(model)
