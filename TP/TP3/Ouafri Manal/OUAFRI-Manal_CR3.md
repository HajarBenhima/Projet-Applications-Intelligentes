# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** 22  ·  **Membres :** OUAFRI Manal  ·  **Date :** 10/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
===================== 5 failed, 18 passed, 1 warning in 21.86s =====================
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?
Les fichiers concernés sont tests/test_client.py et tests/test_ui.py.

test_client.py : trois tests échouent parce que la méthode predict() n'est pas encore implémentée. Elle déclenche une exception NotImplementedError.

test_ui.py : deux tests échouent parce que les fonctionnalités des onglets « Données » et « Prédiction » ne sont pas encore développées. Le premier ne trouve pas les indicateurs attendus et le deuxième ne trouve pas le résultat de prédiction.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'

```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Cette commande fonctionne parce que l'option -m lance Streamlit comme un module Python et permet d'inclure le répertoire courant dans le chemin de recherche. Python peut donc retrouver le dossier maintai et importer ses modules correctement.

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

variable = st.selectbox("Variable", FEATURES)

tranches = pd.cut(df[variable], bins=10)

taux = df.groupby(
    tranches, observed=True
)["failure"].mean()

taux.index = [round(i.mid, 1) for i in taux.index]

st.bar_chart(taux)

df_graph = df.copy()

df_graph["Panne"] = df_graph["failure"].map({
    0: "Non",
    1: "Oui"
})

st.scatter_chart(
    df_graph,
    x="temperature_c",
    y="vibration_mm_s",
    color="Panne"
)
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 % |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

On remarque que le taux de panne augmente globalement lorsque la vibration augmente. Les machines présentant de fortes vibrations ont donc une probabilité de panne plus importante.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

orsqu'on déplace un curseur hors d'un formulaire, le message relance s'affiche de nouveau dans le terminal.

Cela montre que Streamlit réexécute le script Python du début à la fin à chaque interaction avec un widget. Les éléments de l'interface sont ensuite actualisés automatiquement.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Le @st.cache_data permet de conserver en mémoire le résultat de la fonction charger.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé à l'API et retourne la prédiction."""

    headers = {}

    if self.api_key:
        headers["X-API-Key"] = self.api_key

    r = self.http.post(
        "/v1/predict",
        json=reading,
        headers=headers
    )

    if r.status_code != 200:
        raise APIError(
            r.status_code,
            r.json().get("detail")
        )

    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
============================ 23 passed, 1 warning in 12.86s ============================
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne d'environ 95 % et message d'alerte signalant un risque de panne |
| valeurs par défaut, fausse clé | Message d'avertissement « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Message d'erreur « API injoignable : vérifiez que le serveur est lancé » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est un mécanisme de sécurité appliqué par les navigateurs aux requêtes entre origines différentes. Mais dans ce TP, c'est le serveur Python de Streamlit qui envoie la requête HTTP vers l'API. Cette communication entre serveurs n'est pas soumise aux restrictions CORS du navigateur.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, c'est le navigateur de l'utilisateur qui envoie directement la requête HTTP à l'API grâce à JavaScript et à la fonction fetch(). Dans ce TP, c'est le serveur Python de Streamlit qui envoie la requête à l'API à l'aide du client HTTP httpx.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Les tests utilisent le TestClient de FastAPI, qui permet d'envoyer des requêtes directement à l'application sans démarrer un serveur HTTP.Ainsi que le client de test est transmis à MaintaiClient grâce au paramètre http. Cela permet donc de vérifier le fonctionnement des requêtes, des réponses et de la gestion des erreurs sans lancer Uvicorn.

3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une démonstration rapide à un client, nous choisirions Streamlit, car il permet de créer facilement une interface claire avec des indicateurs, des graphiques et des formulaires, sans développer beaucoup de code frontend. Pour une application destinée à être utilisée quotidiennement par un technicien de maintenance, nous choisirions une interface HTML et JavaScript personnalisée. Elle permettrait de mieux adapter l'ergonomie aux besoins du technicien et d'intégrer davantage de fonctionnalités spécifiques.


