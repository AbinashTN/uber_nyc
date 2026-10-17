# Uber NYC — Analyse des mobilités

Application Streamlit en français : quatre pages analytiques et une page À propos. Les graphiques, KPI et conclusions suivent les filtres et sont recalculés à partir des CSV. Aucun chiffre n'est extrait des captures.

## Démarrer sur Mac

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

Les chemins sont relatifs au fichier app.py. Remplacer les CSV en conservant leur schéma recharge les calculs (cache basé sur la taille et la date de modification). La page À propos conserve la provenance et la documentation de ce projet initial. À mettre à jour si le périmètre source change.

## Calculs et limites

Sommes / effectifs : pas de moyenne simple de moyennes. Les attentes utilisent `nb_attentes_valides`. Pour les profils temporels, le nombre de jours est calculé sur la source avant le filtre géographique. Un mois incomplet est signalé ; aucune date source absente n'est inventée.

Le seuil géographique par défaut (1 000 attentes et 95 % de couverture) sert à l'exploration et n'est pas un test statistique. EWR ne contient que deux courses dans cette version. Les matrices financières montrent les données brutes agrégées, avec un avertissement pour les faibles effectifs.

Le script amont n'a pas été fourni : les règles exactes d'exclusion, le filtrage du fournisseur et la définition d'attente valide restent à documenter. On ne peut pas calculer les médianes et percentiles individuels à partir des agrégats.

## Partage

Le projet est livré sous forme de code exécutable, sans déploiement public. Pour un hébergement compatible Streamlit, utiliser `app.py` comme point d'entrée, `requirements.txt` pour les dépendances et conserver les dossiers de données et de captures. Aucune clé ni aucun compte n'est nécessaire pour l'exécution locale.

## Sources

- https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf
- https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart

## Vérifications réalisées

Quatre tests de calcul passent : cohérence avec l'audit, pondération des attentes, normalisation du calendrier et données rares/vides. Les cinq pages ont été exécutées avec `streamlit.testing.v1.AppTest`, ainsi que les filtres EWR seul et sélection vide, sans exception. Ces vérifications portent sur l'exécution et les calculs ; elles ne remplacent pas une inspection graphique dans le navigateur de l'utilisateur.

Pour relancer les contrôles de calcul : `python tests.py`.

## Mise à jour visuelle

- Conclusions simplifiées en puces, dans un encadré coloré en tête de chaque page.
- Cartes arrondies, palette cohérente, graphiques sur fond blanc et barre d'outils visuelle allégée.
- Nuage de points par borough par défaut, comme le rapport Power BI initial ; exploration par zone toujours disponible.
- Appel Plotly adapté à Streamlit 1.50.0 : `use_container_width=True` et options dans `config`, sans argument `width` transmis aux options Plotly obsolètes.
- Les cinq pages et les filtres ont été revérifiés avec AppTest ; aucun avertissement de dépréciation Plotly constaté.

Pour mettre à jour votre installation existante, remplacer `app.py` et `.streamlit/config.toml`, puis relancer `python -m streamlit run app.py`. Conserver la version de Streamlit indiquée dans `requirements.txt`.
