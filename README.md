# Prévision structurelle de la demande à court terme pour le transport aérien et identification des marchés origine-destination latents

Projet de recherche d'exploration des données ouvertes DB1C du *Bureau of Transportation Statistics* pour analyser la structure de la demande en transport aérien sur un horizon court terme de 14 à 365 jours avant le vol.

L'objectif à terme est l'estimation de la demande par paire origine-destination du marché canadien grâce à des séries temporelles.

+ `_targets.R` est le *pipeline* reproductible du projet
+ `data` contient les données brutes, partitionnées et agrégées
+ `docs` contient des documents pour comprendre les données, références et procédures utilisées
+ `outputs` contient des fichiers générés par les scripts comme les résumés de sorties, tracés et rapports compilés de R
+ `R` contient des fonctions utiles au *pipeline*, l'analyse descriptive et aux tracés
+ `renv` contient l'environnement portable R réstauré grâce à la commande ``renv::restore()``
+ `renv.lock` est le verrou de dépendances R
+ `reports` contient les fichiers des sorties générés par Quarto
+ `scripts` contient les programmes principaux

À ce stade, le projet est en construction, les premiers exécutables ainsi qu'un guide d'installation seront ajoutés prochainement.