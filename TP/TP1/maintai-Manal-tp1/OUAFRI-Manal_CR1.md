# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** 22  ·  **Membres :** OUAFRI Manal  ·  **Date :** 27/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'alert'
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
============================== 3 failed, 10 passed, 1 warning in 11.91s ===============================
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les quatre tests qui passent initialement sont :
1. test_health
2. test_out_of_range_value_is_rejected
3. test_missing_field_is_rejected
4. test_openapi_documents_predict

Les deux tests de validation des données passent pour une mauvaise raison. En effet, le schéma SensorReading ne définit initialement aucun champ et utilise extra="forbid". Pydantic refuse donc les champs reçus, car ils ne sont pas déclarés dans le schéma. Même une requête valide est rejetée avec le code HTTP 422. Le test de valeur hors limites et celui de champ manquant réussissent donc sans vérifier réellement les contraintes attendues.

Les trois tests qui échouent concernent la prédiction, l'alerte de risque élevé et la réponse lorsque le modèle est absent.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` |float|-40|150 |Plage large de températures possibles pour tenir compte des conditions de fonctionnement d'un moteur, tout en rejetant les valeurs physiquement incohérentes pour ce système. |
| `vibration_mm_s` |float|0|100|Une vibration ne peut pas être négative. La limite supérieure permet de rejeter les valeurs excessives ou incohérentes tout en couvrant des vibrations très importantes. |
| `load_pct` |float|0|100|La charge est exprimée en pourcentage : elle ne peut pas être inférieure à 0 % ni supérieure à 100 % dans le cadre de ce modèle.|
| `runtime_hours` |float|0|200000|Le temps de fonctionnement cumulé ne peut pas être négatif. La limite supérieure permet de couvrir une longue durée d'utilisation industrielle.|

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
============================== 3 failed, 10 passed, 1 warning in 11.10s ===============================

Après avoir ajouté les quatre champs au schéma, les requêtes valides peuvent être acceptées et les données incorrectes sont rejetées par la validation Pydantic.
Les trois tests liés à la prédiction échouent encore avec une erreur NotImplementedError, car le corps de la fonction predict() n'est pas encore implémenté.
C'est un bon signe car cela signifie que les relevés valides passent la validation du schéma et atteignent maintenant la fonction de prédiction.
```

…

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle de prédiction indisponible",
        )

    result = predictor.predict(reading.model_dump())

    return PredictionOut(**result)
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le code HTTP 503 signifie que le service est temporairement indisponible. Ce qui fait il est approprié ici, car l'API ne peut pas effectuer de prédiction lorsque le modèle est absent. La réponse indique clairement que le modèle est indisponible. Le code HTTP 500 désigne plutôt une erreur interne inattendue du serveur.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Le modèle est chargé au démarrage de l'application et conservé dans le dictionnaire state. Cela évite de relire le fichier du modèle à chaque requête, réduit le temps de traitement et évite des opérations inutiles. Chaque requête peut ainsi réutiliser le modèle déjà chargé.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
==================================== 13 passed, 1 warning in 6.32s ====================================
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` |200 |{"status":"ok","model_loaded":true}|
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` |200|{
  "failure_probability": 0.9553,
  "alert": true,
  "threshold": 0.3,
  "model_version": "2026-10-27T22:58:48Z"
}|
| `POST /v1/predict` avec une température de 500 |422|{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "body",
        "temperature_c"
      ],
      "msg": "Input should be less than or equal to 150",
      "input": 500,
      "ctx": {
        "le": 150
      }
    }
  ]
}|
| `POST /v1/predicte` (faute de frappe dans l'adresse) |404|{"detail":"Not Found"}|

Dans `/docs`, où voit-on les bornes que vous avez choisies ?
Les bornes apparaissent dans la documentation OpenAPI générée automatiquement par FastAPI à partir des schémas Pydantic.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style d'architecture qui définit des principes pour concevoir des API utilisant des ressources et des méthodes HTTP. FastAPI est un framework Python qui permet de développer des API web, notamment des API respectant les principes REST.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   - Définir la structure des données attendues et les champs obligatoires.
   - Vérifier les types et valider les contraintes des valeurs reçues.
   - Générer une description structurée des données, utilisée notamment par - - - FastAPI pour produire la documentation OpenAPI.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   - localhost désigne la machine locale sur laquelle le serveur est exécuté.
   - 8000 est le port sur lequel le serveur écoute les requêtes.
   - /v1/predict est le chemin de la route de prédiction de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   v1 indique la version 1 de l'API.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   maintai.api.main est le chemin Python du module et app est la variable de ce module qui contient l'instance de l'application FastAPI que Uvicorn doit exécuter.