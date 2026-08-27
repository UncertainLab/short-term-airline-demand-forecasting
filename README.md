# Prévision structurelle de la demande à court terme pour le transport aérien et identification des marchés origine-destination latents

Projet de recherche exploratoire utilisant les données ouvertes de l'enquête DB1B du *Bureau of Transportation Statistics* afin d'analyser la structure de la demande de transport aérien à court terme, sur un horizon de 14 à 365 jours avant le vol.

L'objectif à terme est d'estimer la demande par paire origine-destination sur le marché canadien à l'aide de séries temporelles.

Actuellement, l'estimation est réalisée sur le marché domestique des États-Unis à partir de la table DB1B *Market*.

* `_targets.R` contient le *pipeline* reproductible du projet, exécuté avec la commande `targets::tar_make()` ;

* `analysis` contient les notebooks R utilisés pour l'analyse des données, la modélisation et la prédiction ;

* `data` contient les données brutes, partitionnées et agrégées, ainsi que les tables de référence, les régresseurs et les autres données utiles au projet ;

* `docs` contient les documents utiles à la compréhension des données ;

* `outputs` contient les fichiers générés, notamment les tracés et les rapports R compilés ;

* `R` contient les fonctions utilisées dans les programmes d'analyse descriptive pour transformer les données et appliquer les tables de référence ;

* `renv` contient l'environnement R portable, restauré avec la commande `renv::restore()` ;

* `renv.lock` contient le verrouillage des dépendances R ;

* `scripts` contient le programme permettant de récupérer les données DB1B et DB1C.

## Guide d'utilisation

### Récupération des données

Le programme `scripts/bts_downloader.py` permet de télécharger les données DB1B et DB1C depuis le *Bureau of Transportation Statistics*.

Les données téléchargées sont enregistrées dans `data/raw`, puis peuvent être partitionnées et transformées à l'aide du *pipeline* `_targets.R`.

### Reproduction des traitements

Ouvrir le répertoire en tant que projet R, puis restaurer l'environnement avec la commande :

```r
renv::restore()
```

Le *pipeline* reproductible peut ensuite être exécuté avec la commande :

```r
targets::tar_make()
```

Cette commande réalise les traitements définis dans `_targets.R`, notamment la préparation, la partition et l'agrégation des données nécessaires aux analyses.

### Exécution des analyses

Les notebooks présents dans `analysis` regroupent les différentes étapes de l'analyse. Ils peuvent être exécutés individuellement une fois les données préparées avec le *pipeline* `_targets.R`.

Les fichiers générés par les analyses, notamment les figures et les rapports compilés, sont enregistrés dans `outputs`.