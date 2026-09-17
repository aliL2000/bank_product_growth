"""Phase 2 baseline model: LightGBM (gradient boosted decision trees) on
modeling_table.parquet - directly comparable to baseline_logistic_regression.py
(same train/val split, same 16 features, same top-1%-lift sanity check).

Unlike logistic regression, LightGBM needs:
- no feature scaling - tree splits are invariant to monotonic transforms of a
  feature, so raw values work as well as standardized ones.
- no engineered `age_years_sq` - tree splits capture the non-monotonic age
  pattern natively; `age_years` alone is enough.
- an early-stopping validation set instead of a fixed number of boosting
  rounds, since boosting can keep reducing train error indefinitely and
  start overfitting if left unchecked.

Deliberately does NOT reweight for class imbalance the way the logistic
regression baseline does (`class_weight="balanced"`). Tried the LightGBM
equivalent (`is_unbalance=True`) first: it made early stopping trigger after
a single round (`best_iteration_ == 1`) because the inflated gradient on the
rare class made val AUC swing wildly round to round, so round 1 looked like
a local peak before boosting could do anything. Unlike logistic regression's
one-shot convex optimization, boosting corrects errors incrementally across
rounds, and rare-class reweighting amplifies each round's correction enough
to destabilize that process. Dropping it let boosting actually run (36
rounds) and scored *better* (val ROC-AUC 0.9198 vs 0.9158, top-1% lift
17.1x vs 13.3x) - trees split on information gain regardless of class
balance, so they don't need the same nudge a linear decision boundary does.
"""

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import roc_auc_score

from models.baseline_logistic_regression import (
    FEATURE_COLS,
    load_train_val,
    prepare_features,
    top_k_lift,
)


def fit_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> lgb.LGBMClassifier:
    model = lgb.LGBMClassifier(
        objective="binary",
        n_estimators=500,
        random_state=42,
        verbosity=-1,
    )
    model.fit(
        X_train,
        y_train,
        eval_X=X_val,
        eval_y=y_val,
        eval_metric="auc",
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)],
    )
    return model


def evaluate(model: lgb.LGBMClassifier, X: pd.DataFrame, y: pd.Series, label: str) -> None:
    scores = model.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, scores)
    lift = top_k_lift(y, scores)
    print(f"{label}: ROC-AUC={auc:.4f}, top-1% lift={lift:.2f}x, n={len(y):,}, adoption_rate={y.mean():.3%}")


def print_feature_importance(model: lgb.LGBMClassifier) -> None:
    importance = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    print("\nfeature importance (split count, sorted):")
    print(importance.to_string())


if __name__ == "__main__":
    df = load_train_val()

    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)

    model = fit_baseline(X_train, y_train, X_val, y_val)

    evaluate(model, X_train, y_train, "train")
    evaluate(model, X_val, y_val, "val")
    print_feature_importance(model)
