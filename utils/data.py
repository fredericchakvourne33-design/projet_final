# ============================================================
# utils/data.py
# Chargement et préparation des données pour app.py
#
# Trois fichiers sont produits par Analyse_Eploratoire.ipynb :
#   - data/predictions_2026.csv        : volume prévu par province (annuel)
#   - data/districts_risque_2026.csv   : score de risque moyen par district
#   - data/villages_risque_2026.csv    : score de risque moyen par village
# ============================================================

from pathlib import Path

import pandas as pd

CHEMIN_PREDICTIONS = Path("data/predictions_2026.csv")
CHEMIN_DISTRICTS = Path("data/districts_risque_2026.csv")
CHEMIN_VILLAGES = Path("data/villages_risque_2026.csv")

ORDRE_MOIS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

# Les 4 facteurs de risque connus (taux historiques 2022-2025, calculés
# par district/village dans Analyse_Eploratoire.ipynb), dans l'ordre où
# ils doivent être affichés dans l'application.
COLONNES_FACTEURS = [
    "Détection tardive",
    "Animal non attaché",
    "Source d'eau contaminée",
    "Infection non isolée",
]


def _charger_csv(chemin: Path) -> pd.DataFrame:
    """Charge un CSV en retournant un DataFrame vide (jamais une exception)
    si le fichier est introuvable ou illisible — chaque appelant décide
    comment réagir à l'absence de données plutôt que de planter ici."""
    if not chemin.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(chemin, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()


def charger_predictions(chemin: Path = CHEMIN_PREDICTIONS) -> pd.DataFrame:
    """Charge le volume de cas prévu par province pour 2026."""
    return _charger_csv(chemin)


def charger_districts_risque(chemin: Path = CHEMIN_DISTRICTS) -> pd.DataFrame:
    """Charge le classement de risque par district pour 2026."""
    return _charger_csv(chemin)


def charger_villages_risque(chemin: Path = CHEMIN_VILLAGES) -> pd.DataFrame:
    """Charge le classement de risque par village pour 2026."""
    return _charger_csv(chemin)


def preparer_predictions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les colonnes du fichier de prévisions de volume."""
    if df.empty:
        return df

    df = df.copy()

    if "Infections_prevues" not in df.columns and "Infections_prevues_2026" in df.columns:
        df = df.rename(columns={"Infections_prevues_2026": "Infections_prevues"})

    if "Infections_prevues" in df.columns:
        df["Infections_prevues"] = pd.to_numeric(
            df["Infections_prevues"], errors="coerce"
        ).fillna(0)

    if "Province" in df.columns:
        df["Province"] = df["Province"].astype(str).str.strip()

    return df


def preparer_risque(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les colonnes d'un fichier de risque (district ou village) :
    types numériques et arrondis lisibles pour l'affichage."""
    if df.empty:
        return df

    df = df.copy()
    for col in ("risque_moyen_2026", "risque_max_2026", *COLONNES_FACTEURS):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Province" in df.columns:
        df["Province"] = df["Province"].astype(str).str.strip()

    return df


def ordonner_mois(df: pd.DataFrame) -> pd.DataFrame:
    """Ordonne les lignes selon le calendrier si une colonne "Mois" existe.
    Sans effet (retourne le DataFrame inchangé) si cette colonne est
    absente, ce qui est le cas du fichier de prévisions province actuel
    (granularité annuelle, pas mensuelle)."""
    if df.empty or "Mois" not in df.columns:
        return df

    df = df.copy()
    df["Mois"] = pd.Categorical(df["Mois"], categories=ORDRE_MOIS, ordered=True)
    return df.sort_values("Mois")