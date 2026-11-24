# ADR 005 : Image Docker et données externes

Date : 24/11/2026 · Auteurs : Moufti Firdaous

## Contexte

MaintAI doit être exécutée de manière reproductible avec les mêmes versions de Python et des bibliothèques que celles utilisées pour entraîner le modèle. Le modèle, les données et la clé API sont toutefois des éléments variables ou sensibles qui ne doivent pas être intégrés à l’image Docker.

## Options étudiées

1. **Construire une image contenant le code, le modèle, les données et la clé API** : déploiement simple, mais image lourde, données difficiles à mettre à jour et risque d’exposition du secret.
2. **Construire une image contenant uniquement le code et les dépendances, puis injecter le reste au lancement** : image réutilisable et sûre, mais le déploiement doit fournir les volumes et le fichier `.env`.

## Décision

Nous retenons la deuxième option. L’image contient le code MaintAI et les dépendances figées dans `requirements-docker.txt`; le modèle est monté dans `/app/models`, les données dans `/app/data`, et la clé API est fournie par `.env` via Docker Compose.

## Conséquences

Cette décision permet de reconstruire une image stable sans exposer de secret et de remplacer le modèle ou les données sans reconstruire l’image. En contrepartie, le dossier `models/`, le dossier `data/` et `.env` doivent être présents et correctement configurés sur la machine qui lance Compose.
