
# ADR 002 — Validation des données d'entrée

## Statut

Accepté

## Contexte

L'API MaintAI reçoit des mesures provenant de capteurs.
Des valeurs absentes ou physiquement incohérentes peuvent empêcher
la prédiction ou produire des résultats non fiables.

## Décision

Nous utilisons Pydantic pour valider les données reçues par l'API.

Le schéma SensorReading impose les champs suivants :

- temperature_c : nombre compris entre -40 et 150 °C ;
- vibration_mm_s : nombre compris entre 0 et 100 mm/s ;
- load_pct : nombre compris entre 0 et 100 % ;
- runtime_hours : nombre compris entre 0 et 200000 heures.

Les champs sont obligatoires. Une donnée manquante ou hors limites
est rejetée par FastAPI avec une réponse HTTP 422.

## Conséquences

- Les données incorrectes sont rejetées avant la prédiction.
- Le client reçoit une réponse d'erreur de validation.
- Les limites doivent être adaptées si les caractéristiques
  des capteurs ou les exigences du projet changent.
