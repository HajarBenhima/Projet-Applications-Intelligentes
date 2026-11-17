"""Entraîne le modèle, le compare à la baseline, sauvegarde les artefacts et enregistre le run dans MLflow.

Usage : python -m maintai.train
        python -m maintai.train --model forest
        python -m maintai.train --C 0.1 --threshold 0.2
        python -m maintai.train --grid --threshold 0.2   (GridSearch : cherche les meilleurs réglages)
"""
import argparse
import json
import sys
from datetime import datetime, timezone

import joblib
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from maintai.config import FEATURES, SEED, TARGET, Settings, get_settings
from maintai.data import load_data, split
from maintai.tracking import log_run


def build_model(kind: str = "logreg", C: float = 1.0) -> Pipeline:
    """Le prétraitement fait partie du modèle : scaler et classifieur sont sauvegardés ensemble."""
    if kind == "forest":
        clf = RandomForestClassifier(n_estimators=200, random_state=SEED)
    else:
        clf = LogisticRegression(C=C, max_iter=1000)
    return Pipeline([("scale", StandardScaler()), ("clf", clf)])


# Les réglages essayés par la GridSearch, pour chaque type de modèle
GRIDS = {
    "logreg": {"clf__C": [0.01, 0.1, 1.0, 10.0]},
    "forest": {"clf__n_estimators": [100, 200], "clf__max_depth": [None, 5, 10]},
}


def grid_search(kind: str, X_train, y_train, threshold: float) -> GridSearchCV:
    """Essaie chaque réglage de GRIDS[kind] en validation croisée (5 plis) et garde le meilleur recall au seuil choisi."""

    def recall_at_threshold(estimator, X, y):
        pred = (estimator.predict_proba(X)[:, 1] >= threshold).astype(int)
        return recall_score(y, pred)

    search = GridSearchCV(build_model(kind), GRIDS[kind], scoring=recall_at_threshold, cv=5, n_jobs=-1)
    return search.fit(X_train, y_train)


def evaluate(model, X_test, y_test, threshold: float) -> dict:
    """Mesure le modèle au seuil de décision choisi, et non au seuil 0,5 par défaut."""
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= threshold).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 3),
        "recall": round(float(recall_score(y_test, pred)), 3),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 3),
        "threshold": threshold,
    }


def evaluate_baseline(X_train, y_train, X_test, y_test) -> dict:
    """La méthode la plus simple : toujours prédire la classe majoritaire (« pas de panne »)."""
    baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    pred = baseline.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 3),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 3),
    }


def save(model, metrics: dict, settings: Settings, threshold: float) -> None:
    """Écrit le modèle, son contrat d'entrée (model_info.json) et ses métriques."""
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.model_path)
    info = {
        "features": FEATURES,
        "target": TARGET,
        "threshold": threshold,
        "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sklearn_version": sklearn.__version__,
    }
    settings.info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    settings.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m maintai.train")
    p.add_argument("--model", choices=["logreg", "forest"], default="logreg")
    p.add_argument("--C", type=float, default=1.0, help="régularisation de la régression logistique")
    p.add_argument("--threshold", type=float, default=None, help="seuil d'alerte (défaut : MAINTAI_THRESHOLD)")
    p.add_argument("--grid", action="store_true", help="GridSearch : cherche les meilleurs réglages du modèle")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> dict:
    args = parse_args(argv or [])
    settings = get_settings()
    threshold = args.threshold if args.threshold is not None else settings.threshold
    df = load_data(settings.data_path)
    X_train, X_test, y_train, y_test = split(df)
    best_params, cv_metrics = {}, {}
    if args.grid:
        search = grid_search(args.model, X_train, y_train, threshold)
        model = search.best_estimator_
        best_params = {k.removeprefix("clf__"): v for k, v in search.best_params_.items()}
        cv_metrics = {"cv_recall": round(float(search.best_score_), 3)}
        print(f"GridSearch : meilleurs réglages {best_params} (recall en validation croisée : {cv_metrics['cv_recall']})")
    else:
        model = build_model(args.model, args.C).fit(X_train, y_train)
    metrics = {
        "model": evaluate(model, X_test, y_test, threshold),
        "baseline": evaluate_baseline(X_train, y_train, X_test, y_test),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    save(model, metrics, settings, threshold)

    params = {"model": args.model, "threshold": threshold, "n_train": len(X_train)}
    if args.grid:
        params |= {"grid": True} | best_params
    elif args.model == "logreg":
        params["C"] = args.C
    run_id = log_run(
        params=params,
        metrics={k: v for k, v in metrics["model"].items() if k != "threshold"}
        | {"baseline_recall": metrics["baseline"]["recall"]}
        | cv_metrics,
        model=model,
        X_example=X_train.head(3),
        data_path=settings.data_path,
    )
    print(json.dumps(metrics, indent=2))
    print(f"Modèle sauvegardé dans {settings.model_path}")
    print(f"Run MLflow : {run_id}")
    return metrics


if __name__ == "__main__":
    main(sys.argv[1:])
