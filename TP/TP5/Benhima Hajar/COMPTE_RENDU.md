# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** …  ·  **Membres :** Benhima Hajar  ·  **Date :** 17/11/2026

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
5 failed, 27 passed
```

Quels tests échouent, et pourquoi ?

Les 5 tests de `tests/test_tracking.py`. `log_run` n'était pas encore écrite : elle renvoyait `""` et n'enregistrait aucun run.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant : vers le dossier du TP4. Après : vers le dossier du TP5.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, name="model", input_example=X_example,
                                 skops_trusted_types=TRUSTED_TYPES)
    return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 32.41s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | **0.838** | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --model forest --threshold 0.2` | 0.831 | 0.479 | 0.854 |

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

La régression logistique avec le seuil 0.2 : c'est elle qui a le meilleur recall (0.838), donc elle rate le moins de pannes. On accepte en échange plus de fausses alertes. La forêt n'est pas meilleure : au même seuil, elle a un recall un peu plus bas et une precision plus basse.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0`. Au TP4, un modèle chargé avec une autre version de scikit-learn pouvait mal marcher. Maintenant, la bonne version est enregistrée avec le modèle.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans `mlflow.db` (paramètres, métriques) et `mlruns/` (modèles), dans `TP/TP5`.
 Non, ils ne vont pas dans Git : ce sont des fichiers lourds (exclus par le `.gitignore`).

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: b7fec4274774842dc1f48202c6013490
  size: 121814
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

C'est la même valeur. On sait donc sur quelles données chaque run a été entraîné.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Le CSV peut être gros, et Git garderait chaque version pour toujours. Le `.dvc` n'est qu'un petit reçu. Le vrai fichier est gardé par DVC.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data/sensors.csv.dvc:
	changed outs:
		modified:           data/sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | cb9875b | b7fec427 | 5000 |
| v2 | 897b1f5 | 31ef5ebb | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

5000 lignes sur la v1. Après `git checkout HEAD -- data/sensors.csv.dvc` et `dvc checkout`, on retrouve 8000 lignes (v2).

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

DVC récupère le fichier depuis le stockage (`1 file fetched and 1 file added`). On retrouve `data/sensors.csv` avec 8000 lignes.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | b7fec427 | 4000 | 0.750 | 0.622 |
| v2 | 31ef5ebb | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Les données de test ne sont pas les mêmes (autre taille, autre graine), donc les scores ne se comparent pas directement. Pour comparer deux modèles, il faut les tester sur les mêmes données.

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : régression logistique, seuil 0.2. Run `ac44761c69b6460895a49a341ccbbfdc`, `data_md5` = `b7fec4274774842dc1f48202c6013490` (données v1).

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   Git versionne le code (et les reçus `.dvc`). DVC versionne les fichiers de données. MLflow garde chaque entraînement : paramètres, métriques, modèle et versions des bibliothèques.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage est un dossier de mon PC : son chemin ne doit pas aller dans Git (il est écrit dans `.dvc/config.local`). Pour partager, il faut un stockage commun (S3, Google Drive, serveur) ajouté sans `--local`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le code : dans Git. Les données : dans DVC (le reçu dans Git, le fichier dans le stockage). Le modèle : dans MLflow (un run avec son identifiant et son `requirements.txt`).

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : …
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non

## 8. Ce qui reste flou

…
