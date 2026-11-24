# ADR 005 : le modèle arrive par un volume, pas dans l'image

Date : 24/11/2026 · Auteurs : Benhima Hajar

## Contexte
MaintAI doit tourner sur un serveur sans `.venv`, donc dans une image Docker. Il faut choisir ce qui entre dans l'image et ce qui arrive au lancement.

## Options étudiées
1. **Modèle dans l'image** : une seule image suffit pour tout lancer. Mais il faut reconstruire l'image à chaque nouveau modèle, et l'image devient plus lourde.
2. **Modèle par un volume** (`-v ./models:/app/models:ro`) : on change de modèle sans reconstruire l'image. Mais il faut penser au volume, sinon l'API répond 503.

Ce que `.dockerignore` laisse dehors :
- `data/`, `models/` : ils changent sans nouveau code, ils arrivent par volume.
- `.env` : c'est un secret, il arrive par `--env-file`. Dans l'image, il serait lisible par toute personne qui a l'image.
- `mlflow.db`, `mlruns/`, `.dvc/`, `tests/`, `.venv/` : inutiles pour prédire, ils alourdiraient l'image.

Les mettre dans l'image ferait gagner une image autonome. Mais l'image serait plus lourde, plus lente à construire, et elle risquerait de contenir un secret.

## Décision
Option 2 : le modèle arrive par un volume. Le code et le modèle changent à des rythmes différents (MLOps), comme pour le wheel du TP4.

## Conséquences
- Facile : on met à jour le modèle sans rebuild, et l'image reste partageable sans secret.
- Plus difficile : il faut entraîner le modèle et monter le volume avant de lancer l'API.
- À surveiller : la version de scikit-learn de l'image (1.8.0) doit rester celle qui a créé le modèle.
