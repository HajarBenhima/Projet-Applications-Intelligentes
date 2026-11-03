# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G22  ·  **Membres :** Benhima Hajar  ·  **Date :** 03.Nov.2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 · `POST /v1/predict` avec `{"temperature_c": 60.0, "vibration_mm_s": 2.0, "runtime_hours": 5000}` | champ manquant  | 422 | 422 |
| 2 · `POST /v1/predict` avec `{..., "load_pct": 250}` | valeur absurde  | 422 | 422 |
| 3 · `POST /v1/predict` avec `{..., "temperature_c": "abc"}` | texte au lieu d'un nombre | 422 | 422 |
| 4 · `POST /v1/predict` avec `{..., "couleur": "rouge"}` | champ en trop | 422 | 422 |
| 5 · `POST /v1/inconnue` avec un relevé valide | mauvaise route | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, les cinq étaient justes. Le champ en trop donne 422 grâce à `extra="forbid"`, sinon il serait accepté. La mauvaise route donne 404 car la route n'existe pas.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
=================== 19 passed, 1 warning in 1.66s ====================
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

Il permet de lancer le même test avec plusieurs données. Pytest compte 5 tests, un par cas de la liste.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
All checks passed!
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff` lit le code sans l'exécuter et vérifie s'il est bien écrit . `pytest` exécute le code et vérifie qu'il marche correctement.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
=================== 2 failed, 16 passed, 1 warning in 1.88s ====================
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

`test_missing_key_is_rejected` et `test_wrong_key_is_rejected`. Ils reçoivent 200 au lieu de 401, car l'API ne vérifie pas encore la clé.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Toujours 2 tests échouent. La fonction existe, mais personne ne l'appelle.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
======================== 18 passed, 1 warning in 1.60s =========================
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,"model_version":"2026-11-03T17:45:05Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Sans clé, la requête est refusée (401). Avec la clé, on passe ce contrôle, puis Pydantic refuse les 500 °C (422).

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

500, avec `{"detail":"La clé API du serveur n'est pas configurée"}`. Le serveur qui n'a pas de clé, car `.env` n'a pas été chargé.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));
  const adresse = document.getElementById("url").value + "/v1/predict";
  const cle = document.getElementById("key").value;
  try {
    const resp = await fetch(adresse, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cle },
      body: JSON.stringify(reading),
    });
    const data = await resp.json();
    if (!resp.ok) {
      show("err", `Erreur ${resp.status} : ${JSON.stringify(data.detail)}`);
      return;
    }
    const pct = (data.failure_probability * 100).toFixed(1);
    if (data.alert) {
      show("alert", `ALERTE : probabilité de panne ${pct} % (seuil ${data.threshold})`);
    } else {
      show("ok", `Pas d'alerte : probabilité de panne ${pct} % (seuil ${data.threshold})`);
    }
  } catch (e) {
    show("err", "API injoignable (serveur arrêté ou CORS)");
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | Pas d'alerte : probabilité de panne 0.1 % (seuil 0.3) |
| 500 °C, bonne clé | ALERTE : probabilité de panne 94.8 % (seuil 0.3) |
| relevé normal, fausse clé | Erreur 401 : "Clé API absente ou invalide" |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche « API injoignable (serveur arrêté ou CORS) ». La console dit : *Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.* L'origine 5501 n'est pas dans la liste de `.env`, donc l'API refuse la requête OPTIONS (400 « Disallowed CORS origin »).

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle du navigateur, pas du serveur. `curl.exe` n'est pas un navigateur : il ne demande pas la permission et ne bloque rien. Seule la clé API protège vraiment l'API.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

4 tests échouent : ils reçoivent 401 au lieu de 422, car la clé est vérifiée avant les données. La « mauvaise route » passe quand même (404) : la route n'existe pas, donc la clé n'est jamais vérifiée.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
======================== 23 passed, 1 warning in 1.87s =========================
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   401 : on ne sait pas qui tu es (clé absente ou fausse). 422 : la clé est bonne, mais les données sont invalides. 403 : on sait qui tu es, mais tu n'as pas le droit.
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Sinon elle finit sur GitHub et reste dans l'historique pour toujours. `.env` contient la vraie clé (non commité, ignoré par Git). `.env.example` contient une fausse valeur pour montrer quoi configurer (commité).
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout (journaux du serveur, historique du navigateur). La clé serait donc visible.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   Il compare toujours en un temps constant. `==` s'arrête au premier caractère faux : le temps de réponse pourrait révéler combien de caractères sont justes.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine = schéma + domaine + port. Non, ce sont deux origines différentes, car le port change.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` apparaissait-il ? oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

…
