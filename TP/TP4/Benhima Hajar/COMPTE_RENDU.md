# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** 22  ·  **Membres :** BENHIMA Hajar  ·  **Date :** 10.Nov.2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed, 1 warning in 4.70s
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py` :
- `test_installed_version_matches_the_code` : `maintai` n'est pas encore installé, donc pip ne connaît pas sa version.
- `test_command_is_declared` : la commande `maintai-predict` n'existe pas encore .

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
    "scikit-learn>=1.5",
    "joblib>=1.4",
    "httpx>=0.27",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

Parce que le code de base n'en a pas besoin. `pytest` sert seulement aux développeurs, `fastapi` seulement pour l'API. On les installe à la demande : `pip install -e ".[api,dev]"`.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne de machines à partir de relevés de capteurs
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning in 3.78s
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

```
Probabilité de panne : 95 % (ALERTE)
.../maintai-starter-tp4/maintai/__init__.py
```

Python trouve le code dans le dossier du projet (`TP4/maintai/`).

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui . En mode éditable, pip ne copie pas le code : il pointe vers nos fichiers. Chaque lancement relit donc le code modifié.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
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
```

Non, `packages.find` avec `include = ["maintai*"]` ne prend que le dossier `maintai/`. Le wheel contient le code seulement , le modèle se livre à part.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : .../essai/.venv/lib/site-packages/models/model.joblib` + « indiquez son dossier dans MAINTAI_MODELS_DIR » |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | `InconsistentVersionWarning: Trying to unpickle estimator Pipeline from version 1.8.0 when using version 1.9.1` puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)` |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

Le wheel demande `scikit-learn>=1.5`, donc pip a installé la dernière version (1.9.1). Mais le modèle a été entraîné et sauvegardé avec la 1.8.0. Relire un modèle avec une autre version peut donner des erreurs. La ligne qui l'explique : `"sklearn_version": "1.8.0"`.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` fige les versions exactes : on refait le même environnement que celui du modèle. `dependencies` donne des versions minimales : le package peut s'installer à côté d'autres packages.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `-e .` pose un lien vers notre dossier. Le wheel est une copie figée du code (pour livrer).
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   C'est une commande du terminal reliée à une fonction Python. pip crée le fichier à l'installation, dans `.venv/bin/maintai-predict`.

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? non (le `.gitignore` les exclut, comme `.venv/` et `models/`)

## 6. Ce qui reste flou


