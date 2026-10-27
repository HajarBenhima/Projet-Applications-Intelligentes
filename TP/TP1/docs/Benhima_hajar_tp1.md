# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'alert'
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
=================== 3 failed, 10 passed, 1 warning in 100.79s (0:01:40) ====================
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests qui passent déjà sont :

- `test_health` 
- `test_openapi_documents_predict` 
- `test_out_of_range_value_is_rejected` (attend 422) ;
- `test_missing_field_is_rejected` (attend 422).

Le schéma est vide et `extra="forbid"` refuse tout champ inconnu. Donc toutes les requêtes donnent 422, même les bonnes. Le 422 ne vient pas de la vraie erreur (500 °C, champ manquant).

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | Une machine ne fonctionne pas sous -40 °C ni au-dessus de 150 °C (elle casse). |
| `vibration_mm_s` | `float` | 0 | 50 | Une vibration n'est jamais négative. Au-dessus de 50 mm/s, la machine serait détruite. |
| `load_pct` | `float` | 0 | 100 | C'est un pourcentage : de 0 % (arrêt) à 100 % (pleine charge). |
| `runtime_hours` | `float` | 0 | 100 000 | Une durée n'est pas négative. 100 000 h ≈ 11 ans sans arrêt, la vie d'une machine. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
=================== 3 failed, 10 passed, 1 warning in 3.24s ====================
```

L'erreur n'est plus 422 mais `NotImplementedError`. Bon signe : la requête passe la validation, le schéma est bon.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé : lancez l'entraînement d'abord.")
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

500 = bug dans le code. 503 = service pas encore prêt (modèle pas entraîné). Ce n'est pas un bug, on peut réessayer plus tard.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger le modèle est lent. Le recharger à chaque requête rendrait l'API lente pour rien. On le charge une fois et on le garde en mémoire.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
======================== 13 passed, 1 warning in 2.99s =========================
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-27T22:06:28Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans **Schemas** en bas de la page, en ouvrant `SensorReading`.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST = une façon d'organiser une API (URL + GET/POST + codes HTTP). FastAPI = un outil Python pour coder une API.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Valider les données, les convertir en objet Python, et générer la doc.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` = ma machine, `8000` = le port, `/v1/predict` = la route.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la version de l'API.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` = le fichier `maintai/api/main.py`. `app` = la variable FastAPI dans ce fichier.

## 7. Le rendu Git

- Lien de la pull request : 
- Le tag `tp1` existe sur GitHub : oui
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  

## 8. Ce qui reste flou

…
