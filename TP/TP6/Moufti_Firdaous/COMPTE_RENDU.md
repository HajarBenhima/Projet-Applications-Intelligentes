# Compte rendu · TP6 : conteneuriser MaintAI

**Groupe :** 5IADA G2  ·  **Membres :Firdaous Moufti  ·  **Date :** 24/11/2026

## 1. Mise en place
Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```text
Hello from Docker!
Client:
 Version:           29.1.3
Server: Docker Desktop 4.55.0 (213807)
```
Dernière ligne de `python -m pytest` après la mise en place :


```
5 failed, 33 passed, 4 warnings in 34.54s
```


Les commandes utilisées sont :

```powershell
docker run hello-world
docker version
python -m pytest
```

## 2. Image et conteneur

1. Une image est un modèle immuable contenant le système, le code et les dépendances. Un conteneur est une instance en cours d’exécution de cette image, avec son propre processus et ses éventuels volumes.
2. `COPY requirements-docker.txt` est placé avant `COPY maintai` afin que Docker conserve en cache l’installation des dépendances lorsqu’un fichier Python est modifié.
3. `scikit-learn==1.8.0` est fixé car cette version doit être identique à celle utilisée pour produire le modèle. Cela évite les incompatibilités lors du chargement du fichier `joblib`.
4. `mlflow`, `dvc` et `pytest` ne sont pas nécessaires pour servir l’API ou l’interface. Ils servent respectivement au suivi des entraînements, au versionnement des données et aux tests.

## 3. Sprint 1 : Dockerfile

Le [Dockerfile](./Dockerfile) contient :

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


`CACHED` signifie que Docker réutilise une étape déjà construite au lieu de la reconstruire. Grâce à l’ordre du Dockerfile, la modification du code ne relance pas l’installation des bibliothèques.

## 4. Lancer un conteneur

Après génération du modèle, la commande est :

```powershell
python -m maintai.dataset
python -m maintai.train
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

| Essai | Résultat attendu |
|---|---|
| `GET /health` | `200` avec `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | `401 Unauthorized` |
| `POST /v1/predict` avec la clé | `200` avec une probabilité et une alerte |


**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?
Sans le volume `models`, l’API démarre mais le modèle n’est pas chargé : `/health` indique `model_loaded: false` et `/v1/predict` renvoie `503`.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?
Avec `--host 127.0.0.1`, Uvicorn écoute uniquement à l’intérieur du conteneur. Le port publié par Docker devient alors inaccessible depuis le PC ; il faut utiliser `--host 0.0.0.0`.

## 5. Sprint 2 : Docker Compose

Le fichier [compose.yaml](./compose.yaml) lance deux services :

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
    build: .
    image: maintai:0.4.0
    env_file: .env
    environment:
      MAINTAI_API_URL: http://api:8000
    command: ["python", "-m", "streamlit", "run", "ui/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

La commande `docker compose ps` a été validée avec succès. La commande de lancement est :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED       STATUS       PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       3 hours ago   Up 3 hours   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        3 hours ago   Up 3 hours   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```


Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

L’interface est accessible sur http://localhost:8501. Depuis le conteneur UI, l’API est appelée avec `http://api:8000`, car `api` est le nom DNS du service Compose. `localhost` désignerait le conteneur UI lui-même, et non le conteneur API.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
{"status":"ok","model_loaded":true}
httpx.ConnectError: [Errno 111] Connection refused
```

La première doit réussir ; la seconde doit échouer car aucun serveur API n’écoute sur le port `8000` dans le conteneur UI.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed, 4 warnings in 32.06s
```

## 6. Décision : l’ADR 005

La décision complète est documentée dans [docs/adr/005-image-docker.md](./docs/adr/005-image-docker.md). L’image Docker contient uniquement le code applicatif et les dépendances nécessaires à l’exécution ; le modèle, les données et la clé API restent externes et sont injectés au démarrage par volumes et variables d’environnement.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément. Le code et les bibliothèques entrent dans l’image avec `COPY` et `pip install`. Le modèle arrive avec `./models:/app/models:ro`, les données avec `./data:/app/data:ro`, et la clé avec `env_file: .env`.
2. La clé API n’est jamais dans l’image pour éviter qu’elle soit copiée dans les couches Docker ou publiée dans un registre.
3. Docker ajoute une unité de livraison reproductible : le code, les versions des bibliothèques et la commande de démarrage sont réunis dans une image, tandis que le modèle et les données restent remplaçables.

## 8. Rendu Git

- Lien de la pull request : à renseigner après publication.
- Tag `tp6` sur GitHub : à vérifier.
- Le dossier `.env` et `models/` sont exclus par [.gitignore](./.gitignore). Les données CSV sont également ignorées.

## 9. Ce qui reste à vérifier

- Démarrer Docker Desktop et exécuter les commandes de build et de lancement.
- Réparer ou recréer `.venv`, puis exécuter `python -m pytest`.
- Ajouter les durées, tailles d’image et sorties réellement observées dans les sections précédentes.
