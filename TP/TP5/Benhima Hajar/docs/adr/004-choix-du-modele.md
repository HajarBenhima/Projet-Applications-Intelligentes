# ADR 004 : Choix du modèle et du seuil de MaintAI

Date : 17/11/2026 · Auteurs : Benhima Hajar

## Contexte
MaintAI doit prévenir les pannes. Une panne manquée coûte plus cher qu'une fausse alerte : le recall est la métrique principale.

## Options étudiées
Runs MLflow (expérience `maintai`, données v1) :

| Option | recall | precision | accuracy |
|---|---|---|---|
| Régression logistique, C=1.0, seuil 0.3 | 0.750 | 0.622 | 0.904 |
| Régression logistique, C=0.01, seuil 0.3 | 0.691 | 0.653 | 0.908 |
| **Régression logistique, C=1.0, seuil 0.2** | **0.838** | 0.543 | 0.882 |
| Forêt aléatoire, seuil 0.3 | 0.728 | 0.562 | 0.886 |
| Forêt aléatoire, seuil 0.2 | 0.831 | 0.479 | 0.854 |

## Décision
Régression logistique (C=1.0) avec le seuil 0.2 : c'est le meilleur recall (0.838). La forêt n'apporte rien de plus et elle est plus lourde.

- Run MLflow : `ac44761c69b6460895a49a341ccbbfdc`
- data_md5 : `b7fec4274774842dc1f48202c6013490` (données v1, 5000 lignes, commit `cb9875b`)

## Conséquences
- On accepte plus de fausses alertes (precision 0.543 au lieu de 0.622).
- On peut retrouver le modèle (run MLflow) et ses données (DVC).
- À surveiller : la dérive des données. Il faudra ré-entraîner et refaire la comparaison sur les mêmes données de test.
