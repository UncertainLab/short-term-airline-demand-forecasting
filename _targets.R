# Pour voir les étapes du pipeline à faire taper targets::tar_outdated(), pour lancer le pipeline faire targets::tar_make() pour invalider les fichiers si l'on change de période ou ajoute des fichiers targets::tar_invalidate(DB1C_mkt_files) ou targets::tar_invalidate(DB1B_mkt_files)
library(targets)
library(arrow)

# Packages chargés automatiquement dans chaque cible
tar_option_set(packages = c("arrow", "data.table", "dplyr", "fs", "purrr"))

# Charge les fonctions définies dans le répertoire R/.
tar_source("R/")

# Déclaration du pipeline reproductible
list(
  # # Fichiers bruts DB1C MARKET à intégrer au pipeline
  # tar_target(
  #   DB1C_mkt_files,
  #   dir_ls(
  #     "data/raw/MARKET/DB1C/",
  #     regexp = "DB1C\\.MARKET\\.[0-9]{4}\\..+\\.parquet$"
  #   ),
  #   format = "file"
  # ),

  # # Repartitionne les fichiers DB1C MARKET par année et mois
  # tar_target(
  #   DB1C_mkt_partition,
  #   {
  #     open_dataset(DB1C_mkt_files) |>
  #       write_dataset(
  #         path = "data/interim/MARKET/DB1C",
  #         format = "parquet",
  #         partitioning = c("RpYear", "RpMonth"),
  #         existing_data_behavior = "delete_matching"
  #       )

  #     "data/interim/MARKET/DB1C"
  #   },
  #   format = "file"
  # ),

  # # Ouvre le jeu de données DB1C MARKET partitionné
  # tar_target(
  #   DB1C_mkt,
  #   {
  #     DB1C_mkt_partition
  #     open_by_cols("data/interim/MARKET/DB1C", c("RpYear", "RpMonth"))
  #   }
  # ),

  # Fichiers bruts DB1B MARKET à intégrer au pipeline
  tar_target(
    DB1B_mkt_files,
    dir_ls(
      "data/raw/MARKET/DB1B/",
      regexp = "DB1B\\.MARKET\\.[0-9]{4}\\.[1-4]\\.parquet$"
    ),
    format = "file"
  ),

  # Repartitionne les fichiers DB1B MARKET par année et trimestre
  tar_target(
    DB1B_mkt_partition,
    {
      db1b_mkt_raw <- open_dataset(DB1B_mkt_files)

      # Ignore les éventuelles colonnes dont le nom est vide.
      valid_cols <- names(db1b_mkt_raw)
      valid_cols <- valid_cols[nzchar(valid_cols)]

      db1b_mkt_raw |>
        select(any_of(valid_cols)) |>
        write_dataset(
          path = "data/interim/MARKET/DB1B",
          format = "parquet",
          partitioning = c("Year", "Quarter"),
          existing_data_behavior = "delete_matching"
        )

      "data/interim/MARKET/DB1B"
    },
    format = "file"
  ),

  # Ouvre le jeu de données DB1B MARKET partitionné
  tar_target(
    DB1B_mkt,
    {
      DB1B_mkt_partition
      open_by_cols("data/interim/MARKET/DB1B", c("Year", "Quarter"))
    }
  ),

  # Fichiers de référence utilisés pour le recodage des variables
  tar_target(
    lookup_files,
    dir_ls(
      "data/external/refs",
      glob = "*ref_*.csv"
    ),
    format = "file"
  ),

  # Charge les tables de référence dans une liste nommée
  tar_target(
    lookups,
    load_lookups(lookup_files)
  )
)
