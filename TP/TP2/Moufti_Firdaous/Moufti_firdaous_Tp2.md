# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** 5IADAG2 · **Membres :** Moufti Firdaous · **Date :** 03/11/2026

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

L'objectif est de vérifier que l'API refuse les données incorrectes et retourne les codes HTTP appropriés.

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | Champ `load_pct` manquant | 422 | 422 (pytest) |
| 2 | `load_pct = 250` | 422 | 422 (pytest) |
| 3 | `temperature_c = "abc"` | 422 | 422 (pytest) |
| 4 | Champ supplémentaire `couleur = "rouge"` | 422 | 422 (pytest) |
| 5 | Route inexistante `/v1/inconnue` | 404 | 404 (pytest) |

**Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?**

Les cinq prévisions correspondent aux résultats des tests automatiques. Aucune différence n'a été observée dans les tests Pytest.

Les résultats dans `/docs` du TP1 restent à confirmer séparément.

**Dernière ligne de `python -m pytest` avec `tests/test_casser.py` dans TP1 :**

```text
18 passed 
```

**À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?**

`@pytest.mark.parametrize` permet d'exécuter la même fonction de test avec plusieurs données différentes.

Dans notre projet, nous avons cinq cas dans `CAS_REFUSES`. Pytest exécute donc cinq tests distincts à partir d'une seule fonction `test_requete_refusee()`.

Cela évite de répéter le même code plusieurs fois.

---

## 2. Ruff

**Sortie de `ruff check .` :**

```text
Found 4 errors (4 fixed, 0 remaining).
All checks passed!
```

Ce résultat a été obtenu dans le TP2.
**Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?**

`ruff check .` vérifie la qualité du code Python sans l'exécuter. Il détecte notamment les imports inutilisés et certaines erreurs de programmation.

`python -m pytest` exécute les tests automatiques pour vérifier que les fonctions et l'API donnent les résultats attendus.

Ruff vérifie donc la qualité du code, tandis que Pytest vérifie son fonctionnement.

---

## 3. Mise en place du TP2 (dans `TP/TP2`)

Nous avons préparé le projet dans un environnement virtuel Python, installé les dépendances et configuré l'API.

**Dernière ligne de `python -m pytest` juste après la mise en place :**

```text
2 failed, 16 passed
```

**Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?**

Les deux tests concernés sont :

- Le test qui vérifie le refus d'une requête sans clé API.
- Le test qui vérifie le refus d'une requête avec une fausse clé API.

Avant l'implémentation de la sécurité, ces requêtes reçoivent le code **200 OK** au lieu de **401 Unauthorized**.

Cela signifie que l'API accepte les requêtes sans vérifier correctement la clé API.

---

## 4. La clé API (sprint 1)

**Votre fonction `require_api_key()` dans `maintai/api/security.py` :**

```python
def require_api_key(
    x_api_key: str | None = Header(default=None)
) -> None:

    expected = get_settings().api_key

    if not expected:
        raise HTTPException(
            status_code=500,
            detail="Clé API non configurée"
        )

    if x_api_key is None or not secrets.compare_digest(
        x_api_key, expected
    ):
        raise HTTPException(
            status_code=401,
            detail="Clé API absente ou invalide"
        )
```

Cette fonction récupère la clé envoyée par le client et la compare avec celle configurée sur le serveur.

Si la clé est absente ou incorrecte, l'API retourne 401. Si aucune clé n'est configurée côté serveur, elle retourne 500.

**Votre ligne `router = ...` dans `maintai/api/main.py` :**

```python
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)]
)
```

Cette configuration oblige FastAPI à vérifier la clé API avant d'exécuter les routes `/v1`.

**Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?**

Deux tests échouent encore, car la fonction `require_api_key()` existe, mais elle n'est pas encore appelée par FastAPI.

L'ajout de `Depends(require_api_key)` au routeur permet d'activer cette vérification automatiquement.

**Dernière ligne de `python -m pytest` à la fin du sprint 1 :**

```text
18 passed
```

*Résultat attendu à cette étape du starter. La validation finale de notre projet a ensuite donné 23 tests réussis.*

### Résultats des six requêtes

| Requête | Code obtenu / attendu | Réponse JSON |
|---|---|---|
| `GET /health`, sans clé | 200 observé | `{"status":"ok","model_loaded":false}` avant entraînement |
| `POST /v1/predict`, relevé normal, sans clé | 401 attendu | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 attendu | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 observé via la page web | Probabilité de panne : 94,75 %, alerte activée |
| `POST /v1/predict`, 500 °C, sans clé | 401 attendu | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 attendu | Détail JSON de l'erreur de validation |

Les réponses attendues sont à confirmer individuellement dans Swagger ou avec `curl.exe`.

**500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?**

La sécurité est vérifiée avant les données de la requête.

Sans clé, FastAPI refuse immédiatement la requête avec 401.

Avec une clé valide, la requête passe le contrôle de sécurité, puis FastAPI vérifie les données. La température de 500 °C est hors des limites autorisées, donc l'API retourne 422.

**Relancez Uvicorn sans `--env-file .env`. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?**

Résultat attendu, si aucune clé n'est déjà définie dans l'environnement :

```text
500 Internal Server Error
```

La clé attendue n'est pas configurée sur le serveur. Il s'agit donc d'un problème de configuration interne, et non d'une erreur d'authentification du client.


---

## 5. La page web (sprint 2)

Nous avons complété le fichier `web/index.html` pour permettre à l'utilisateur d'envoyer les valeurs des capteurs à l'API.

**Votre code `fetch` (contenu du `addEventListener`) :**

```javascript
document.getElementById("go").addEventListener("click", async () => {

  const reading = Object.fromEntries(
    FEATURES.map(f => [
      f,
      Number(document.getElementById(f).value)
    ])
  );

  const url = document.getElementById("url").value.trim();
  const cle = document.getElementById("key").value;
  const adresse = `${url.replace(/\/$/, "")}/v1/predict`;

  try {
    const resp = await fetch(adresse, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": cle
      },
      body: JSON.stringify(reading)
    });

    const data = await resp.json();

    if (!resp.ok) {
      show("err", `Erreur ${resp.status} : ${JSON.stringify(data)}`);
      return;
    }

    const probabilite = (
      data.failure_probability * 100
    ).toFixed(2);

    if (data.alert) {
      show("alert", `Alerte ! Risque de panne : ${probabilite}%`);
    } else {
      show("ok", `État normal. Risque de panne : ${probabilite}%`);
    }

  } catch (e) {
    show("err", "API injoignable ou erreur CORS : " + e.message);
  }
});
```

### Résultats de la page web

Le port 5500 était déjà occupé par Oracle TNS Listener. Nous avons donc utilisé le port **5502**, autorisé dans notre configuration CORS.

| Essai | Ce qu'affiche la page |
|---|---|
| Relevé de test (72 °C, 6 mm/s, 85 %, 15 000 h), bonne clé | `Alerte ! Risque de panne : 94.75%` |
| 500 °C, bonne clé | Erreur 422 attendue — à vérifier |
| Relevé normal, fausse clé | Erreur 401 attendue — à vérifier |

### Résultat du modèle Machine Learning

Nous avons généré 5 000 relevés de capteurs, avec un taux de panne de 13,6 %.

L'entraînement a donné :

```json
{
  "model": {
    "accuracy": 0.904,
    "recall": 0.75,
    "precision": 0.622,
    "threshold": 0.3
  },
  "baseline": {
    "accuracy": 0.864,
    "recall": 0.0
  },
  "n_train": 4000,
  "n_test": 1000
}
```

Le modèle a été sauvegardé dans `models/model.joblib`.

La page web a ensuite réussi à afficher une probabilité de panne de **94,75 %**, avec une alerte.

Cela confirme la communication entre la page HTML, FastAPI et le modèle Machine Learning.

### Expérience CORS

**Pourquoi avons-nous utilisé les ports 5502 et 5503 ?**

Le port 5500 était occupé par Oracle Database, qui utilise ce port pour son service HTTPS.

Nous avons donc adapté l'expérience :

- Port 5502 : origine autorisée.
- Port 5503 : origine non autorisée.

**Que dit la page, et que dit la console (F12) ?**

Résultat attendu sur le port 5503 :

```text
API injoignable ou erreur CORS : Failed to fetch
```

Dans la console, le navigateur doit afficher une erreur indiquant que l'origine n'est pas autorisée par la politique CORS.

*L'expérience sur le port 5503 reste à exécuter et à documenter avec le message exact de la console.*

**Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5503 est bloquée ?**

CORS est une restriction appliquée par les navigateurs web.

`curl.exe` n'applique pas cette restriction. Il peut donc envoyer une requête et recevoir la réponse du serveur, à condition de fournir une clé API valide pour les routes protégées.

---

## 6. Les tests de l'activité 1 dans le TP2

**Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?**

Quatre tests doivent échouer avec le code 401 au lieu du code 422 attendu.

Cela se produit parce que l'API vérifie la clé avant de valider les données.

Le test de la mauvaise route `/v1/inconnue` passe quand même avec 404, car cette route n'existe pas.

Nous avons corrigé les tests en ajoutant :

```python
HEADERS = {"X-API-Key": "test-key"}
```

Puis :

```python
response = client.post(
    url,
    json=corps,
    headers=HEADERS
)
```

**Dernière ligne de `python -m pytest` avec `headers=HEADERS` :**

```text
23 passed
```

Ce résultat a été confirmé après l'ajout des cinq tests de sécurité supplémentaires.

Nous avons également exécuté Ruff :

```text
Found 4 errors (4 fixed, 0 remaining).
All checks passed!
```

Après les corrections de Ruff, les 23 tests ont de nouveau réussi.

---

## 7. Questions de compréhension

**1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?**

- **401 Unauthorized :** la clé API est absente ou incorrecte.
- **422 Unprocessable Entity :** les données envoyées sont invalides.
- **403 Forbidden :** le client est authentifié, mais n'a pas le droit d'effectuer l'action demandée.

**2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?**

La clé doit rester secrète pour empêcher les accès non autorisés à l'API.

Le fichier `.env` contient les vraies valeurs de configuration, notamment la clé API. Il ne doit pas être envoyé sur Git.

Le fichier `.env.example` contient des exemples de variables avec des valeurs fictives. C'est ce fichier qui est commité.

**3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?**

Parce que les URL peuvent être enregistrées dans l'historique du navigateur et les journaux des serveurs.

L'en-tête `X-API-Key` permet de transmettre la clé sans l'exposer dans l'URL.

**4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?**

`secrets.compare_digest` compare les clés en limitant les différences de temps qui pourraient révéler des informations sur leur contenu.

Il est donc plus adapté à la comparaison de secrets.

**5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?**

Une origine est composée du protocole, du domaine et du port.

Ces deux adresses ne sont pas de la même origine, car leurs ports sont différents.

CORS permet au serveur d'indiquer quelles origines web sont autorisées à lire ses réponses depuis un navigateur.

---

## 8. Le rendu Git



---

## 9. Ce qui reste flou



---
