# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** 22  ·  **Membres :** OUAFRI Manal  ·  **Date :** 10/11/2026 | 18:20

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
================= 2 failed, 25 passed, 1 warning in 18.60s =================
```

Quels sont les deux tests qui échouent, et pourquoi ?
Les deux tests qui échouent se trouvent dans le fichier tests/test_package.py :

- test_installed_version_matches_the_code() : ce test vérifie que la version du package installé correspond à celle définie dans maintai/__init__.py. Il échoue parce que MaintAI n'est pas encore installé comme package Python.

- test_command_is_declared() : ce test vérifie que la commande maintai-predict existe parmi les points d'entrée du système. Il échoue parce que cette commande n'a pas encore été déclarée et installée.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
    "numpy>=2.4",
    "pandas>=3.0",
    "scikit-learn>=1.8",
    "joblib>=1.5",
    "httpx>=0.28"
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?
Ces deux bibliothèques sont donc placées dans les dépendances optionnelles : pytest dans le groupe dev et fastapi dans le groupe api. Cela permet de limiter les dépendances obligatoires et d'éviter d'installer des bibliothèques inutiles.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: TODO : une phrase qui dit ce que fait le package
Home-page:

```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
================== 27 passed, 1 warning in 14.74s ==================
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

…

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui, le changement est visible immédiatement après la modification du fichier maintai/cli.py, sans effectuer une nouvelle installation.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
Les deux fichiers attendus dans le dossier dist sont :
maintai-0.2.0-py3-none-any.whl
maintai-0.2.0.tar.gz

```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD

Le modèle entraîné, les tests et le dossier ui/ ne sont pas inclus dans le wheel.
Cela s'explique par la configuration de pyproject.toml, qui sélectionne uniquement le package maintai et ses sous-packages. Les fichiers du modèle sont générés séparément lors de l'entraînement. Les tests servent à vérifier le code pendant le développement et l'interface Streamlit appartient à un dossier indépendant. Le wheel contient donc principalement le code Python installable, les métadonnées du package et le point d'entrée de la commande.

```

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | Message « Modèle introuvable », car le wheel ne contient pas le modèle entraîné. |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | Le modèle est trouvé et la prédiction peut s'exécuter, mais un avertissement InconsistentVersionWarning peut apparaître si la version de scikit-learn est différente. |
| après `pip install scikit-learn==1.8.0` | La prédiction s'exécute avec la version de scikit-learn utilisée pour l'entraînement. Résultat attendu : « Probabilité de panne : 95 % (ALERTE) ». |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?
L'avertissement InconsistentVersionWarning apparaît lorsqu'un modèle de machine learning a été entraîné et sauvegardé avec une version de scikit-learn différente de celle utilisée pour le charger. Cette différence peut provoquer des problèmes de compatibilité et rendre les prédictions moins fiables. Dans le fichier models/model_info.json, l'information à vérifier est la version de scikit-learn enregistrée lors de l'entraînement, notamment le champ :
"sklearn_version": "1.8.0"
L'installation de la même version permet de retrouver un environnement compatible avec celui utilisé pour créer le modèle.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   requirements.txt favorise la reproductibilité, tandis que pyproject.toml facilite l'installation et la distribution du package dans différents environnements.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   La commande pip install -e . effectue une installation éditable. Elle permet d'utiliser directement les fichiers sources du projet. Les modifications du code sont visibles sans réinstallation. La commande pip install dist\maintai-0.2.0-py3-none-any.whl installe une distribution construite du package. Le code est copié dans l'environnement Python et les modifications du dossier source ne sont pas automatiquement prises en compte.
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   …

