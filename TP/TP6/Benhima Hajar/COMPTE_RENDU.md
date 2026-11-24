# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** 22  ·  **Membres :** Benhima Hajar  ·  **Date :** 24 Nov 2026 5:50PM

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
Client:
 Version:           29.1.3
Server: Docker Desktop 4.55.0 (213807)
```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed, 4 warnings in 34.54s
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est la recette figée. Le conteneur est une copie de l'image qui tourne.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Pour garder le `pip install` en cache. Les bibliothèques changent rarement, le code souvent.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle a été créé avec la 1.8.0. Une autre version pourrait ne pas le lire.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert seulement à prédire. Ces outils sont inutiles et alourdissent l'image.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 2 min 17 s (dont `pip install` : 80 s) | 1,13 Go |
| après une modification de `maintai/predict.py` | 2,3 s | 1,13 Go |

Que signifie `CACHED` dans le journal du second build ?

Docker réutilise la couche déjà construite. Seul le code est recopié.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "$(pwd)/models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `200` · `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | `401` · `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict` avec la clé | `200` · `{"failure_probability":0.9908,"alert":true,"threshold":0.3,...}` |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` : `model_loaded:false`. `/v1/predict` : erreur 503. Le modèle n'est pas dans l'image, il arrive seulement par le volume.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

Les logs disent que l'API tourne, mais `localhost:8002/health` ne répond pas. `127.0.0.1` veut dire « ce conteneur seulement », donc le PC ne peut pas l'atteindre. Il faut `0.0.0.0`.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       Up 4 seconds   0.0.0.0:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        Up 4 seconds   0.0.0.0:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable `MAINTAI_API_URL` définie dans `compose.yaml`.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
{"status":"ok","model_loaded":true}
httpx.ConnectError: [Errno 111] Connection refused
```

Dans le conteneur `ui`, `localhost` veut dire le conteneur `ui` lui-même, et il n'y a pas d'API dedans. Il faut appeler l'API par son nom : `api`.

`docker compose down` supprime les conteneurs et le réseau `tp6_default`. L'image, le modèle et les données restent.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed, 4 warnings in 32.06s
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

L'image contient seulement le code et les bibliothèques. Le modèle et les données arrivent par volume, et la clé par `--env-file`, pour changer de modèle sans rebuild et ne jamais mettre de secret dans l'image.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image (`docker build`) : Linux, Python 3.11, les bibliothèques, `maintai/` et `ui/`. Au lancement : le modèle et les données par volume (`-v`), la clé par `--env-file .env`.
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage. Toute personne qui a l'image pourrait lire la clé.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   L'environnement complet : système, Python et bibliothèques figés. L'API tourne pareil sur tout PC ou serveur qui a Docker.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? oui / non

## 9. Ce qui reste flou

…
