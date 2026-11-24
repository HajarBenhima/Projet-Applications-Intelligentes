# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .
# Chaque ligne crée une "couche". Docker garde en cache les couches qui ne changent pas.

# 1. On part d'un Linux léger avec Python 3.11
FROM python:3.11-slim

# 2. Le dossier où l'on travaille dans l'image
WORKDIR /app

# 3. On installe les bibliothèques AVANT de copier le code.
#    si on modifie seulement le code, Docker la reprend du cache.
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. On copie le code de l'API et de l'interface
COPY maintai ./maintai
COPY ui ./ui

# 5. On indique où chercher le modèle et les données.
#    Ils ne sont pas dans l'image : ils arrivent au lancement par un volume (-v).
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. L'API utilise le port 8000.
#    0.0.0.0 = écouter partout, pour que le PC puisse joindre l'API.
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
