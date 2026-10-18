# Uber NYC — Analyse des mobilités

Application Streamlit en français : quatre pages analytiques et une page À propos. Les graphiques, KPI et conclusions suivent les filtres et sont recalculés à partir des CSV. Aucun chiffre n'est extrait des captures.

## Lien de l'application Streamlit avec les Captures Power Bi : 

https://ubernyc-powerbi.streamlit.app

## Démarrer

Depuis le dossier décompressé `uber_nyc`, ouvrir un terminal :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Ouvrir l'adresse locale affichée par Streamlit. Le projet est fourni avec les données et les quatre captures, déjà nommées pour leur affichage.

## Contenu

- `app.py` : interface, graphiques, filtres et conclusions dynamiques.
- `analytics.py` : lecture, contrôles et calculs pondérés.
- `data/` : `fact_activite.csv`, `dim_zone.csv`, `audit_qualite.csv`.
- `captures_power_bi/` : quatre captures originales.
- `ANALYSE.md` : conclusions sur l'ensemble janvier–février 2025.
- `tests.py` : vérification des agrégations et des cas limites.
- `.streamlit/config.toml` : thème.


## Sources

- https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf
- https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
