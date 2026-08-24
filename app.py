# Système intelligent de surveillance de la maladie de ver de guinée — Tchad
# Tableau de bord : prévision 2026 par province,
# districts et villages à risque.

from datetime import date

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data import (
    charger_predictions,
    charger_districts_risque,
    charger_villages_risque,
    preparer_predictions,
    preparer_risque,
    ordonner_mois,
    COLONNES_FACTEURS,
)
# Configuration

st.set_page_config(
    page_title="Surveillance Dracunculose - Tchad",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

NUM_BULLETIN = "AIGW/TD-2026"

# Palette — identité visuelle inspirée des bulletins
TEAL = "#0E4B47"
TEAL_CLAIR = "#DCEAE8"
OCRE = "#C68A2E"
ROUGE = "#A6301E"
VERT = "#3F7A5C"
ENCRE = "#1C2B27"
FOND = "#F7F5F0"
MUTEE = "#66716B"

# CSS

st.markdown(
f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif;
    color: {ENCRE};
}}
.stApp {{ background-color: {FOND}; }}

section[data-testid="stSidebar"] {{
    background-color: {TEAL};
}}
section[data-testid="stSidebar"] * {{
    color: #F2F6F5 !important;
}}
section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
    background-color: rgba(255,255,255,0.08);
    color: #F2F6F5 !important;
    border-color: rgba(255,255,255,0.25);
}}

.bulletin-entete {{
    border-top: 4px solid {TEAL};
    border-bottom: 1px solid #D8D3C6;
    padding: 0.6rem 0 0.9rem 0;
    margin-bottom: 1.2rem;
}}
.bulletin-eyebrow {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    color: {MUTEE};
    text-transform: uppercase;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
}}
.bulletin-titre {{
    font-size: 1.9rem;
    font-weight: 700;
    color: {TEAL};
    margin: 0.15rem 0 0.1rem 0;
    line-height: 1.2;
}}
.bulletin-soustitre {{
    font-size: 0.95rem;
    color: {MUTEE};
}}

.carte-kpi {{
    background: #FFFFFF;
    border-left: 4px solid {TEAL};
    border-radius: 4px;
    padding: 0.7rem 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}
.carte-kpi .kpi-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: {MUTEE};
}}
.carte-kpi .kpi-valeur {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: {ENCRE};
    line-height: 1.3;
}}

.entete-section {{
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
    margin: 1.7rem 0 0.5rem 0;
}}
.entete-section .num {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    color: {OCRE};
}}
.entete-section .titre {{
    font-size: 1.15rem;
    font-weight: 600;
    color: {TEAL};
}}
.entete-section hr {{
    flex-grow: 1;
    border: none;
    border-top: 1px solid #D8D3C6;
    margin: 0;
}}

.alerte {{
    border-left: 4px solid;
    border-radius: 4px;
    padding: 0.55rem 0.9rem;
    margin-bottom: 0.5rem;
    background: #FFFFFF;
    font-size: 0.92rem;
}}
.alerte-eleve {{ border-color: {ROUGE}; }}
.alerte-eleve .badge {{ color: {ROUGE}; }}
.alerte-succes {{ border-color: {VERT}; }}
.alerte-succes .badge {{ color: {VERT}; }}
.alerte .badge {{
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 0.7rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-right: 0.4rem;
}}

.pied-page {{
    font-size: 0.78rem;
    color: {MUTEE};
    border-top: 1px solid #D8D3C6;
    padding-top: 0.7rem;
    margin-top: 1.4rem;
}}
</style>
""",
    unsafe_allow_html=True,
)


def carte_kpi(label, valeur):
    st.markdown(
        f'<div class="carte-kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-valeur">{valeur}</div></div>',
        unsafe_allow_html=True,
    )


def entete_section(numero, titre):
    st.markdown(
        f'<div class="entete-section"><span class="num">{numero}</span>'
        f'<span class="titre">{titre}</span><hr></div>',
        unsafe_allow_html=True,
    )


def alerte(niveau, html):
    classe = "alerte-eleve" if niveau == "eleve" else "alerte-succes"
    badge = "Risque élevé" if niveau == "eleve" else "Aucune alerte"
    st.markdown(
        f'<div class="alerte {classe}"><span class="badge">{badge}</span>{html}</div>',
        unsafe_allow_html=True,
    )


def facteurs_dominants_texte(ligne, seuil=0.20, top_n=2):
    """Retourne une courte phrase citant les facteurs de risque les plus
    présents historiquement dans cette zone (ex. 'Infection non isolée
    (42 %), Animal non attaché (35 %)'), ou une chaîne vide si aucun
    facteur ne dépasse le seuil."""
    valeurs = [(f, ligne[f]) for f in COLONNES_FACTEURS if f in ligne.index and pd.notna(ligne[f])]
    valeurs = [(f, v) for f, v in valeurs if v >= seuil]
    valeurs.sort(key=lambda x: x[1], reverse=True)
    if not valeurs:
        return ""
    parties = [f"{nom} ({v:.0%})" for nom, v in valeurs[:top_n]]
    return " · ".join(parties)



#  bulletin épidémiologique

st.markdown(
f"""
<div class="bulletin-entete">
    <div class="bulletin-eyebrow">
        <span>Système de surveillance épidémiologique — République du Tchad</span>
        <span>Bulletin n° {NUM_BULLETIN} · {date.today().strftime('%d/%m/%Y')}</span>
    </div>
    <div class="bulletin-titre">🩺 Surveillance de la dracunculose — infections animales</div>
    <div class="bulletin-soustitre">Prévisions 2026 — volume par province, districts et villages à risque</div>
</div>
""",
    unsafe_allow_html=True,
)

# Chargement

df_provinces = preparer_predictions(charger_predictions())
df_provinces = ordonner_mois(df_provinces)

df_districts = preparer_risque(charger_districts_risque())
df_villages = preparer_risque(charger_villages_risque())


if df_provinces.empty:
    st.error(
        "Aucune donnée de prévision 2026 n'a été trouvée.\n\n"
        "Veuillez exécuter le notebook `Analyse_Eploratoire.ipynb` en entier : "
        "il génère automatiquement `data/predictions_2026.csv`, "
        "`data/districts_risque_2026.csv` et `data/villages_risque_2026.csv`."
    )
    st.stop()


# SIDEBAR — filtres


st.sidebar.markdown("### 📂 Données")
st.sidebar.markdown("**Année**")
st.sidebar.info("2026")

if "Province" in df_provinces.columns:
    provinces = sorted(df_provinces["Province"].dropna().unique().tolist())
    province_selection = st.sidebar.multiselect("Province", provinces, default=provinces)
    df_prov_filtre = df_provinces[df_provinces["Province"].isin(province_selection)]
else:
    province_selection = []
    df_prov_filtre = df_provinces

df_dist_filtre = (
    df_districts[df_districts["Province"].isin(province_selection)]
    if not df_districts.empty and "Province" in df_districts.columns
    else df_districts
)
df_vill_filtre = (
    df_villages[df_villages["Province"].isin(province_selection)]
    if not df_villages.empty and "Province" in df_villages.columns
    else df_villages
)


#  Indicateurs clés

total_infections = int(df_prov_filtre["Infections_prevues"].sum()) if "Infections_prevues" in df_prov_filtre.columns else 0
nb_provinces = df_prov_filtre["Province"].nunique() if "Province" in df_prov_filtre.columns else 0

colonnes_kpi = [
    ("🦠 Infections prévues 2026", f"{total_infections:,}".replace(",", " ")),
    ("📍 Provinces", nb_provinces),
]
if not df_dist_filtre.empty:
    colonnes_kpi.append(("🏥 Districts suivis", df_dist_filtre["District"].nunique()))
if not df_vill_filtre.empty:
    colonnes_kpi.append(("🌍 Villages suivis", df_vill_filtre["Village"].nunique()))

colonnes = st.columns(len(colonnes_kpi))
for col, (label, valeur) in zip(colonnes, colonnes_kpi):
    with col:
        carte_kpi(label, valeur)

#  Évolution / répartition par province


entete_section("01", "Volume prévu par province — 2026")

if "Mois" in df_prov_filtre.columns:
    evolution = (
        df_prov_filtre.groupby("Mois", observed=True)["Infections_prevues"]
        .sum()
        .reset_index()
    )
    fig = px.line(
        evolution, x="Mois", y="Infections_prevues", markers=True,
        labels={"Mois": "Mois", "Infections_prevues": "Infections prévues"},
        color_discrete_sequence=[TEAL],
    )
    fig.update_layout(height=380, template="plotly_white", font_family="IBM Plex Sans")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(
        "Le modèle actuel produit une prévision **annuelle** par province "
        "(pas de détail mensuel à cette échelle)."
    )

province_data = (
    df_prov_filtre.groupby("Province")["Infections_prevues"]
    .sum()
    .reset_index()
    .sort_values("Infections_prevues", ascending=False)
)
fig_province = px.bar(
    province_data, x="Province", y="Infections_prevues", text_auto=True,
    labels={"Province": "Province", "Infections_prevues": "Infections prévues"},
    color_discrete_sequence=[TEAL],
)
fig_province.update_layout(template="plotly_white", height=420, font_family="IBM Plex Sans")
fig_province.update_traces(marker_line_width=0)
st.plotly_chart(fig_province, use_container_width=True)

with st.expander("Tableau détaillé par province"):
    tab = province_data.copy()
    tab["Infections_prevues"] = tab["Infections_prevues"].round().astype(int)
    tab = tab.rename(columns={"Infections_prevues": "Infections prévues 2026"})
    st.dataframe(tab, use_container_width=True, hide_index=True)



# Districts à risque 2026

entete_section("02", "Districts à risque — 2026")

if df_districts.empty:
    st.warning(
        "Aucune donnée de risque district trouvée. Exécutez "
        "`Analyse_Eploratoire.ipynb` en entier pour générer "
        "`data/districts_risque_2026.csv`."
    )
else:
    seuil_d = (
        df_dist_filtre["risque_moyen_2026"].quantile(0.75)
        if len(df_dist_filtre) > 3 else df_dist_filtre["risque_moyen_2026"].median()
    )
    a_risque_d = df_dist_filtre[df_dist_filtre["risque_moyen_2026"] >= seuil_d].sort_values(
        "risque_moyen_2026", ascending=False
    )

    col_a, col_b = st.columns([3, 2])
    with col_a:
        top = df_dist_filtre.sort_values("risque_moyen_2026", ascending=False).head(12)
        fig_d = px.bar(
            top, x="risque_moyen_2026", y="District", orientation="h",
            labels={"risque_moyen_2026": "Score de risque moyen 2026", "District": ""},
            color_discrete_sequence=[OCRE],
        )
        fig_d.update_layout(template="plotly_white", height=420, font_family="IBM Plex Sans",
                             yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_d, use_container_width=True)

    with col_b:
        st.markdown("**Districts signalés (quart supérieur)**")
        if a_risque_d.empty:
            alerte("succes", "Aucun district ne se distingue nettement dans la sélection actuelle.")
        else:
            for _, ligne in a_risque_d.head(8).iterrows():
                facteurs_txt = facteurs_dominants_texte(ligne)
                complement = f"<br><span style='color:{MUTEE};font-size:0.85em;'>Facteurs dominants : {facteurs_txt}</span>" if facteurs_txt else ""
                alerte(
                    "eleve",
                    f"<b>{ligne['District']}</b> ({ligne.get('Province','')}) — "
                    f"score {ligne['risque_moyen_2026']:.3f}, pic attendu en "
                    f"{ligne.get('mois_pic_2026', 'n.d.')}.{complement}"
                )

    st.markdown("**Facteurs de risque — moyenne sur les districts sélectionnés**")
    moyennes_facteurs_d = df_dist_filtre[COLONNES_FACTEURS].mean().reset_index()
    moyennes_facteurs_d.columns = ["Facteur", "Taux historique"]
    moyennes_facteurs_d = moyennes_facteurs_d.sort_values("Taux historique", ascending=True)
    fig_fact_d = px.bar(
        moyennes_facteurs_d, x="Taux historique", y="Facteur", orientation="h",
        text_auto=".0%", color_discrete_sequence=[TEAL],
    )
    fig_fact_d.update_layout(
        template="plotly_white", height=260, font_family="IBM Plex Sans",
        xaxis_tickformat=".0%", margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_fact_d, use_container_width=True)
    st.caption(
        "Taux calculé sur l'historique 2022-2025 des districts actuellement sélectionnés "
        "(part des infections présentant chaque facteur), pas une prévision."
    )

    with st.expander("Classement complet des districts (2026)"):
        st.dataframe(
            df_dist_filtre.sort_values("risque_moyen_2026", ascending=False).round(4),
            use_container_width=True, hide_index=True,
        )
    st.caption(
        "Score = probabilité moyenne, sur les 12 mois de 2026, qu'au moins un cas "
        "survienne dans le district (modèle Gradient Boosting, validé sur 2025 — "
        "AUC 0,786, PR-AUC 0,477). Le seuil « signalé » correspond au quart des "
        "districts les plus exposés dans la sélection courante."
    )

# Villages à risque 2026

entete_section("03", "Villages à risque — 2026")

if df_villages.empty:
    st.warning(
        "Aucune donnée de risque village trouvée. Exécutez "
        "`Analyse_Eploratoire.ipynb` en entier pour générer "
        "`data/villages_risque_2026.csv`."
    )
else:
    nb_top = st.slider("Nombre de villages à afficher", 5, 50, 20, 5)
    top_villages = df_vill_filtre.sort_values("risque_moyen_2026", ascending=False).head(nb_top)

    fig_v = px.bar(
        top_villages, x="risque_moyen_2026", y="Village", orientation="h",
        labels={"risque_moyen_2026": "Score de risque moyen 2026", "Village": ""},
        color_discrete_sequence=[ROUGE],
        hover_data=["Province"],
    )
    fig_v.update_layout(
        template="plotly_white", height=max(400, nb_top * 22), font_family="IBM Plex Sans",
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig_v, use_container_width=True)

    st.markdown("**Facteurs de risque — moyenne sur les villages sélectionnés**")
    moyennes_facteurs_v = df_vill_filtre[COLONNES_FACTEURS].mean().reset_index()
    moyennes_facteurs_v.columns = ["Facteur", "Taux historique"]
    moyennes_facteurs_v = moyennes_facteurs_v.sort_values("Taux historique", ascending=True)
    fig_fact_v = px.bar(
        moyennes_facteurs_v, x="Taux historique", y="Facteur", orientation="h",
        text_auto=".0%", color_discrete_sequence=[ROUGE],
    )
    fig_fact_v.update_layout(
        template="plotly_white", height=260, font_family="IBM Plex Sans",
        xaxis_tickformat=".0%", margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_fact_v, use_container_width=True)
    st.caption(
        "Taux calculé sur l'historique 2022-2025 des villages actuellement sélectionnés "
        "(part des infections présentant chaque facteur), pas une prévision."
    )

    with st.expander("Classement complet des villages (2026)"):
        st.dataframe(
            df_vill_filtre.sort_values("risque_moyen_2026", ascending=False).round(4),
            use_container_width=True, hide_index=True,
        )
    st.caption(
        "Score = probabilité moyenne, sur les 12 mois de 2026, qu'au moins un cas "
        "survienne dans le village (même méthodologie qu'au niveau district). "
        "51 % des villages touchés en 2025 n'avaient jamais été touchés "
        "auparavant : ce classement reste une aide à la priorisation, pas une "
        "certitude, en particulier pour les zones sans historique."
    )

# PIED DE PAGE

st.markdown(
f"""
<div class="pied-page">
    Bulletin n° {NUM_BULLETIN} — Système intelligent de surveillance et d'aide à la décision,
    dracunculose animale, Tchad. Les valeurs affichées pour 2026 sont des prévisions produites
    par des modèles de Machine Learning (régression de Poisson pour le volume, Gradient
    Boosting pour le risque spatial), à partir de l'historique de surveillance 2022-2025
    uniquement. À utiliser comme aide à la priorisation, pas comme certitude.
</div>
""",
    unsafe_allow_html=True,
)
