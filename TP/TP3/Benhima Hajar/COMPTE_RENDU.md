# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** 22  ·  **Membres :** BENHIMA Hajar  ·  **Date :** 10.Nov.2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
======================== 5 failed, 18 passed, 1 warning in 3.23s ========================
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

- `tests/test_client.py` (3 tests) : la méthode `predict` n'est pas encore écrite, donc pas de prédiction ni d'`APIError`.
- `tests/test_ui.py` (2 tests) : la page est vide, donc pas de `metric` à lire → erreur `IndexError`.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'httpx'
Traceback:
File "/usr/local/Caskroom/miniconda/base/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 75, in exec_func_with_error_handling
    result = func()
File "/usr/local/Caskroom/miniconda/base/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 574, in code_to_exec
    exec(code, module.__dict__)
    ~~~~^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/hajarbenhima/Documents/EMSI/S9/AI App Intelligent/maintai-starter-tp3/ui/app.py", line 5, in <module>
    import httpx
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

`streamlit` tout seul utilise le Python où il est installé , qui n'a pas nos bibliothèques (`httpx`) et ne voit pas le dossier `maintai`. `python -m streamlit` utilise notre Python et ajoute le dossier courant dans les chemins de recherche : il trouve donc `httpx` et `maintai`.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
c1, c2, c3 = st.columns(3)

    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df['failure'].mean():.1%}")
    c3.metric(
        "Température moyenne",
        f"{df['temperature_c'].mean():.1f} °C"
    )

    # 2. Choix de la variable
    st.subheader("Analyse des pannes")
    variable = st.selectbox("Variable", FEATURES)

    # 3. Taux de panne par tranche
    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True)["failure"].mean()
    taux.index = [round(i.mid, 1) for i in taux.index]
    st.bar_chart(taux)

    # 4. Nuage de points
    st.subheader("Température et vibration")
    df_graph = df.copy()
    df_graph["Panne"] = df_graph["failure"].map({0: "Non", 1: "Oui"})
    st.scatter_chart(df_graph, x="temperature_c", y="vibration_mm_s", color="Panne")
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Il monte très vite, La vibration compte plus que la température.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

« relance » s'affiche à chaque fois que je touche un widget. Cela montre que Streamlit relance tout le script, de la première à la dernière ligne, à chaque interaction.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Il garde le résultat en mémoire.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
        """Envoie un relevé à l'API MaintAI."""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        response = self.http.post("/v1/predict", json=reading, headers=headers)

        if response.status_code != 200:
            raise APIError(response.status_code, response.json().get("detail"))

        return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
======================== 23 passed, 1 warning in 47.91s ========================
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | « Probabilité de panne : 95 % » + message rouge « ALERTE : risque de panne élevé (seuil 30%) » |
| valeurs par défaut, fausse clé | message jaune « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | message rouge « API injoignable : vérifiez que uvicorn tourne sur http://localhost:8000 » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une règle du navigateur. Avec Streamlit, ce n'est pas le navigateur qui appelle l'API, c'est le serveur Python (httpx). Python n'applique pas CORS, donc pas de blocage.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   TP2 : le navigateur (JavaScript avec `fetch`). Streamlit : le serveur Python, avec `httpx` (`MaintaiClient`).
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Ils donnent un `TestClient` au client avec `http=client`. La requête va directement à l'application FastAPI en mémoire, sans réseau ni serveur.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   - Démo client : Streamlit. C'est rapide à faire, tout en Python, avec des graphiques prêts.
   - Technicien : page HTML + JavaScript. On peut faire une interface plus propre et adaptée (mobile, design), plus légère, et le serveur ne relance pas tout le script à chaque clic.

## 6. Le rendu Git

- Lien de la pull request : (à compléter après le push)
- Le tag `tp3` existe sur GitHub : (à compléter : oui / non)
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? non (ils sont dans le `.gitignore`)

## 7. Ce qui reste flou

