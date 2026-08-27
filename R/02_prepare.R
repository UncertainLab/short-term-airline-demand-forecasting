library(data.table)
library(fs)


# Charge les fichiers de référence ref_*.csv dans une liste.
load_lookups <- function(files) {
  setNames(
    lapply(files, data.table::fread, showProgress = FALSE),
    gsub("^ref_", "", fs::path_ext_remove(fs::path_file(files)))
  )
}


# Remplace les codes d'une colonne par leur description à partir d'une table de référence.
recode_col <- function(tbl, col, lookup) {
  tbl |>
    left_join(lookup, by = setNames("Code", col), copy = "inline") |>
    mutate(!!sym(col) := Description) |>
    select(-Description)
}


# Applique recode_col() successivement à plusieurs colonnes.
# Chaque colonne de cols doit correspondre à la table de référence de même position dans lookups.
recode_cols <- function(tbl, cols, lookups) {
  for (i in seq_along(cols)) {
    tbl <- recode_col(tbl, cols[i], lookups[[i]])
  }

  tbl
}


# Transforme une table de référence en vecteur nommé Code -> Description.
# Utile notamment pour fournir des labels aux échelles ggplot2.
lookup_vec <- function(lookup) {
  setNames(lookup$Description, lookup$Code)
}
