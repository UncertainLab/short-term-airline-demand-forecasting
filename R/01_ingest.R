library(arrow)
library(data.table)
library(dplyr)
library(fs)


# Ouvre un jeu de données Parquet partitionné selon les colonnes indiquées.
open_by_cols <- function(dir, cols) {
  open_dataset(dir, partitioning = cols, format = "parquet", hive_style = TRUE)
}


# Applique les types R adaptés aux variables MARKET DB1B ou DB1C après collect().
# Les conversions sont réalisées uniquement pour les colonnes présentes dans dt.
type_market <- function(dt) {
  # Variables ordinales dont l'ordre des modalités doit être conservé
  .ordinal <- list(
    RpQuarter = 1:4,
    SchFlQuarter = 1:4,
    RpMonth = 1:12,
    SchFlMonth = 1:12,

    Quarter = 1:4
    # MktDistanceGroup = 1:?
  )

  for (col in names(.ordinal)) {
    if (col %in% names(dt)) {
      set(
        dt,
        j = col,
        value = factor(dt[[col]], levels = .ordinal[[col]], ordered = TRUE)
      )
    }
  }

  # "Null" est converti en NA avant la création du facteur ordinal
  if ("PurchaseWindowGroup" %in% names(dt)) {
    set(
      dt,
      j = "PurchaseWindowGroup",
      value = factor(
        fifelse(
          dt[["PurchaseWindowGroup"]] == "Null",
          NA_character_,
          dt[["PurchaseWindowGroup"]]
        ),
        levels = c("21AP", "2290", "91UP"),
        ordered = TRUE
      )
    )
  }

  # Variables qualitatives nominales
  nominal_cols <- intersect(
    c(
      "OriginAirportID",
      "OriginAirportSeqID",
      "OriginCityMarketID",
      "Origin",
      "OriginCountry",
      "OriginStateFips",
      "OriginState",
      "OriginStateName",
      "OriginWac",
      "DestAirportID",
      "DestAirportSeqID",
      "DestCityMarketID",
      "Dest",
      "DestCountry",
      "DestStateFips",
      "DestState",
      "DestStateName",
      "DestWac",
      "RpCarrierAirlineID",
      "RpCarrier",
      "IssuingCarrierAirlineID",
      "IssuingCarrier",
      "MktCarrierAirlineID",
      "MktCarrier",
      "OpCarrierAirlineID",
      "OpCarrier",
      "MktGeoType",
      "ItinGeoType",
      "MktDistanceGroup",

      "RPCarrier",
      "TkCarrier",
      "BulkFare"
    ),
    names(dt)
  )

  if (length(nominal_cols)) {
    dt[, (nominal_cols) := lapply(.SD, as.factor), .SDcols = nominal_cols]
  }

  # Variables binaires
  bool_cols <- intersect(
    c(
      "MktCarrierChange",
      "OpCarrierChange",
      "V_Yield",
      "Nonstop",
      # "Break_LegacyLogic",

      "TkCarrierChange"
    ),
    names(dt)
  )

  if (length(bool_cols)) {
    dt[, (bool_cols) := lapply(.SD, as.logical), .SDcols = bool_cols]
  }

  # Variables numériques continues
  double_cols <- intersect(
    c(
      "MktAmount",
      "MktTax",

      "MktFare"
    ),
    names(dt)
  )

  if (length(double_cols)) {
    dt[, (double_cols) := lapply(.SD, as.double), .SDcols = double_cols]
  }

  # Variables numériques entières
  integer_cols <- intersect(
    c(
      "MktCoupons",
      "SchFlYr",
      "TotalDistance",
      "MilesTraveled",
      "NonStopMiles",
      "RpYear",

      "Passengers",
      "MktDistance",
      "MktMilesFlown",
      "Year"
    ),
    names(dt)
  )

  if (length(integer_cols)) {
    dt[, (integer_cols) := lapply(.SD, as.integer), .SDcols = integer_cols]
  }

  dt
}
