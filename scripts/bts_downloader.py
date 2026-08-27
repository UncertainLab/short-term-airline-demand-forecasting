import re
import shutil
import time
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pyarrow.csv as csv
import pyarrow.parquet as pq
import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BTSDownloader:
  """Télécharge et prépare les données DB1B et DB1C du BTS."""

  def __init__(self):
    """Initialise les chemins, URLs et sessions HTTP."""
    self.base_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    self.db1b_url = "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_{table}_{year}_{period}.zip"
    self.db1c_url = "https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data-{table}"

    # Session standard utilisée pour les anciens fichiers DB1B.
    self.session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 104])
    self.session.mount("https://", HTTPAdapter(max_retries=retries))

    self.session.headers.update({
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    })

    # Session imitant Chrome nécessaire pour accéder aux pages et fichiers DB1C.
    self.db1c_session = curl_requests.Session(impersonate="chrome")

  # ------------------------------------------------------------------
  # DB1B
  # ------------------------------------------------------------------
  def _convert_file(self, zip_path, parquet_path):
    """Extrait le CSV d'une archive DB1B et le convertit en Parquet."""
    with zipfile.ZipFile(zip_path) as archive:
      csv_file = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
      archive.extract(csv_file, zip_path.parent)

    csv_path = zip_path.parent / csv_file

    # Lecture et écriture par blocs pour limiter l'utilisation de la mémoire.
    reader = csv.open_csv(csv_path, read_options=csv.ReadOptions(block_size=64 * 1024 * 1024))
    writer = None

    try:
      for batch in reader:
        if writer is None:
          writer = pq.ParquetWriter(parquet_path, batch.schema, compression="snappy")

        writer.write_batch(batch)

    finally:
      if writer is not None:
        writer.close()

  def _download_db1b_file(self, url, parquet_path):
    """Télécharge une archive DB1B puis la convertit en Parquet."""
    if parquet_path.exists():
      print(f"[IGNORÉ] Fichier déjà présent : {parquet_path.name}")
      return True

    print(f"[TÉLÉCHARGEMENT] {url}")

    try:
      response = self.session.get(url, stream=True, timeout=(30, 3600))

      if response.status_code == 404:
        print(f"[ABSENT] Fichier non disponible : {url}")
        return False

      response.raise_for_status()
      parquet_path.parent.mkdir(parents=True, exist_ok=True)

      # Le ZIP et le CSV sont stockés uniquement dans un dossier temporaire.
      with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "data.zip"

        with open(zip_path, "wb") as file:
          for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
              file.write(chunk)

        self._convert_file(zip_path, parquet_path)

      print(f"[TERMINÉ] Fichier créé : {parquet_path.name}")
      time.sleep(1)

      return True

    except Exception as error:
      print(f"[ERREUR] Échec du traitement de {url} : {repr(error)}")

      if parquet_path.exists():
        parquet_path.unlink()

      return False

  def download_db1b(self, start_year=1993, end_year=2025, tables=("ticket", "market", "coupon")):
    """Télécharge les tables trimestrielles DB1B demandées."""
    print("--- Téléchargement DB1B ---")

    for table in tables:
      table_name = table.upper()
      bts_table = f"DB1B{table.capitalize()}"

      for year in range(start_year, end_year + 1):
        for quarter in range(1, 5):
          # DB1B est disponible jusqu'au deuxième trimestre 2025.
          if year == 2025 and quarter > 2:
            continue

          url = self.db1b_url.format(table=bts_table, year=year, period=quarter)
          parquet_path = self.base_dir / table_name / "DB1B" / f"DB1B.{table_name}.{year}.{quarter}.parquet"
          self._download_db1b_file(url, parquet_path)

  # ------------------------------------------------------------------
  # DB1C
  # ------------------------------------------------------------------
  def _download_db1c_file(self, url, parquet_path):
    """Télécharge une archive DB1C et extrait le Parquet qu'elle contient."""
    if parquet_path.exists():
      print(f"[IGNORÉ] Fichier déjà présent : {parquet_path.name}")
      return True

    print(f"[TÉLÉCHARGEMENT] {url}")

    try:
      parquet_path.parent.mkdir(parents=True, exist_ok=True)

      with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "data.zip"

        response = self.db1c_session.get(url, stream=True, timeout=3600)
        response.raise_for_status()

        with open(zip_path, "wb") as file:
          for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
              file.write(chunk)

        # Les nouvelles archives DB1C contiennent directement un fichier Parquet.
        with zipfile.ZipFile(zip_path) as archive:
          parquet_file = next(
            (name for name in archive.namelist() if name.lower().endswith(".parquet")),
            None,
          )

          if parquet_file is None:
            raise ValueError("Aucun fichier Parquet trouvé dans l'archive")

          with archive.open(parquet_file) as source, open(parquet_path, "wb") as destination:
            shutil.copyfileobj(source, destination)

      print(f"[TERMINÉ] Fichier créé : {parquet_path.name}")
      time.sleep(2)

      return True

    except Exception as error:
      print(f"[ERREUR] Échec du traitement de {url} : {repr(error)}")

      if parquet_path.exists():
        parquet_path.unlink()

      return False

  @staticmethod
  def _extract_year_month(text):
    """Extrait une année et un mois au format AAAAMM depuis un texte."""
    match = re.search(r"(\d{4})[._-]?(\d{2})(?!\d)", text)

    if not match:
      return None, None

    year, month = int(match.group(1)), int(match.group(2))

    if not (1 <= month <= 12):
      return None, None

    return year, month

  def download_db1c(self, start_year=2025, end_year=2026, tables=("ticket", "market", "coupon", "segment", "product")):
    """Télécharge les tables mensuelles DB1C demandées depuis les pages du BTS."""
    print("--- Téléchargement DB1C ---")

    for table in tables:
      table_name = table.upper()
      page_url = self.db1c_url.format(table=table)

      print(f"[TABLE] {table_name}")

      try:
        response = self.db1c_session.get(page_url, timeout=30)
        response.raise_for_status()

      except Exception as error:
        print(f"[ERREUR] Impossible d'accéder à {page_url} : {repr(error)}")
        continue

      soup = BeautifulSoup(response.text, "html.parser")
      links_found = 0

      # Recherche des archives ZIP proposées sur la page de la table.
      for link in soup.find_all("a", href=True):
        href = link["href"]

        if not href.lower().endswith(".zip"):
          continue

        full_url = urljoin(page_url, href)
        raw_filename = href.split("/")[-1].split("?")[0]

        # L'année et le mois sont normalement présents dans le nom du fichier.
        year, month = self._extract_year_month(raw_filename)
        parent_text = link.parent.get_text(" ", strip=True) if link.parent else ""

        # Utilisation du texte autour du lien comme solution de secours.
        if year is None:
          year, month = self._extract_year_month(parent_text)

        if year is not None and (year < start_year or year > end_year):
          continue

        if year is not None and month is not None:
          filename_stub = f"DB1C.{table_name}.{year}.{month}"
        else:
          clean_name = parent_text.replace(":", "").replace("Download", "").strip()
          clean_name = "".join(c if c.isalnum() else "_" for c in clean_name)
          clean_name = re.sub(r"_+", "_", clean_name).strip("_") or "unknown"
          filename_stub = f"DB1C.{table_name}.{clean_name}"
          print(f"[AVERTISSEMENT] Période indéterminée pour {raw_filename!r}. Nom utilisé : {filename_stub!r}")

        parquet_path = self.base_dir / table_name / "DB1C" / f"{filename_stub}.parquet"

        links_found += 1
        self._download_db1c_file(full_url, parquet_path)

      if links_found == 0:
        print(f"[AVERTISSEMENT] Aucun fichier ZIP trouvé pour la table {table_name}.")


if __name__ == "__main__":
  downloader = BTSDownloader()

  # DB1B
  downloader.download_db1b(start_year=2000, end_year=2019, tables=("market",))

  # DB1C
  # downloader.download_db1c(start_year=2026, end_year=2026, tables=("market",))