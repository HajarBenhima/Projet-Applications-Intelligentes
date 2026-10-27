# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Projet :** MaintAI — maintenance prédictive  

**Groupe :** 5IADA-G2

**Membres :** Firdaous Moufti  

**Date :** 27 octobre 2026


---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```text
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'alert'
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
3 failed, 10 passed, 1 warning in 3.76s
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les quatre tests sont `test_health`, `test_openapi_documents_predict`, `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected`.

Les deux derniers passent pour une mauvaise raison : le schéma vide et `extra="forbid"` rejettent tous les champs, même valides. Le code 422 n'est donc pas provoqué par les contraintes réellement attendues.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 200 | Une température très basse ou très élevée peut être incompatible avec le fonctionnement d'une machine. |
| `vibration_mm_s` | `float` | 0 | 100 | Une vibration ne peut pas être négative ; une vibration excessive signale un fonctionnement anormal. |
| `load_pct` | `float` | 0 | 100 | La charge est un pourcentage compris entre 0 % et 100 %. |
| `runtime_hours` | `float` | 0 | 100 000 | Une durée ne peut pas être négative ; 100 000 heures correspondent à environ 11 ans. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```text
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed, 1 warning in 4.00s
```

C'est un bon signe : les données passent la validation Pydantic. Les tests échouent désormais parce que `predict()` n'est pas encore implémentée.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le code 500 indique une erreur interne. Le code 503 indique que le service est temporairement indisponible parce que le modèle n'est pas chargé.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger le modèle prend du temps. Le conserver en mémoire accélère les prédictions et évite les chargements inutiles.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```text
13 passed, 1 warning in 1.75s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 pour les requêtes de prédiction observées | Corps JSON exact non visible dans le terminal ; champs attendus : `failure_probability`, `alert`, `threshold`, `model_version`. |
| `POST /v1/predict` avec une température de 500 | 422 attendu (non vérifié par une requête manuelle visible) | Erreur de validation Pydantic : `temperature_c` dépasse le maximum 200. |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 attendu (non vérifié par une requête manuelle visible) | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la section **Schemas**, en ouvrant `SensorReading`.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est une manière d'organiser une API ; FastAPI est un framework Python pour la développer.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Valider les données, les convertir en objets Python et générer la documentation.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est mon ordinateur, `8000` est le port et `/v1/predict` est la route de prédiction.
4. Pourquoi `/v1` dans l'adresse ?
   Il indique la première version de l'API.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` désigne le module `maintai/api/main.py` ; `app` est l'objet FastAPI défini dans ce module.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ? …

## 8. Ce qui reste flou

Le choix du seuil d'alerte et la manière dont le modèle calcule la probabilité de panne restent à approfondir.
