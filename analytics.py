from pathlib import Path
import numpy as np
import pandas as pd

SUMS = ['nb_courses', 'tarif_base_total', 'versements_chauffeurs_total', 'pourboires_total', 'miles_total', 'duree_secondes_total', 'attente_minutes_total', 'nb_attentes_valides', 'nb_courses_partagees']
DAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

def load_data(root):
    root = Path(root)
    f = pd.read_csv(root / 'fact_activite.csv', parse_dates=['date_course'])
    z = pd.read_csv(root / 'dim_zone.csv')
    required = ['date_course', 'heure', 'LocationID'] + SUMS
    missing = set(required) - set(f.columns)
    if missing:
        raise ValueError(f'Colonnes manquantes : {sorted(missing)}')
    if f[required].isna().any().any():
        raise ValueError('Valeurs manquantes dans les champs de calcul.')
    if f.duplicated(['date_course', 'heure', 'LocationID']).any():
        raise ValueError('Doublons au grain date × heure × zone.')
    if not f.heure.between(0, 23).all() or not (f.heure % 1 == 0).all():
        raise ValueError('Heures invalides.')
    for col in SUMS:
        if not np.isfinite(f[col]).all():
            raise ValueError(f'Valeurs non finies : {col}')
    if (f[['nb_courses', 'nb_attentes_valides', 'miles_total', 'duree_secondes_total', 'attente_minutes_total']] < 0).any().any():
        raise ValueError('Effectifs, distances ou durées négatifs.')
    if (f.nb_attentes_valides > f.nb_courses).any():
        raise ValueError('Attentes valides supérieures aux courses.')
    f = f.merge(z[['LocationID', 'Borough', 'Zone']], on='LocationID', how='left', validate='many_to_one')
    f['Borough'] = f.Borough.fillna('Non renseigné')
    f['Zone'] = f.Zone.fillna('Zone inconnue')
    f['mois'] = f.date_course.dt.strftime('%Y-%m')
    f['jour_num'] = f.date_course.dt.dayofweek
    f['type_jour'] = np.where(f.jour_num >= 5, 'Week-end', 'Semaine')
    return f

def ratio(a, b):
    return a / b if b else np.nan

def metrics(d):
    s = d[SUMS].sum()
    n = s.nb_courses
    return {'Courses': n, 'Tarif de base total ($)': s.tarif_base_total,
        'Tarif moyen ($)': ratio(s.tarif_base_total, n),
        'Durée moyenne (min)': ratio(s.duree_secondes_total, n * 60),
        'Distance moyenne (miles)': ratio(s.miles_total, n),
        'Versement moyen ($)': ratio(s.versements_chauffeurs_total, n),
        'Attente moyenne (min)': ratio(s.attente_minutes_total, s.nb_attentes_valides),
        'Pourboire moyen ($)': ratio(s.pourboires_total, n),
        'Tarif par mile ($)': ratio(s.tarif_base_total, s.miles_total),
        'Versement par minute ($)': ratio(s.versements_chauffeurs_total * 60, s.duree_secondes_total),
        'Attentes valides': s.nb_attentes_valides,
        'Couverture attente (%)': 100 * ratio(s.nb_attentes_valides, n)}

def grouped(d, keys):
    if isinstance(keys, str): keys = [keys]
    rows = []
    for key, sub in d.groupby(keys, observed=True, dropna=False):
        if not isinstance(key, tuple): key = (key,)
        rows.append(dict(zip(keys, key), **metrics(sub)))
    return pd.DataFrame(rows)

def calendar_for(f, months):
    # Toutes les dates disponibles dans la source, AVANT le filtre géographique.
    c = f.loc[f.mois.isin(months), ['date_course', 'jour_num', 'type_jour']].drop_duplicates()
    return c.sort_values('date_course')

def demand(d, calendar):
    counts = calendar.groupby('type_jour').size()
    sums = d.groupby('type_jour').nb_courses.sum().reindex(counts.index, fill_value=0)
    daily_type = (sums / counts).rename('Courses / jour').reset_index()
    idx = pd.MultiIndex.from_product([counts.index, range(24)], names=['type_jour', 'heure'])
    h = d.groupby(['type_jour', 'heure']).nb_courses.sum().reindex(idx, fill_value=0).reset_index()
    h['Courses / jour et heure'] = h.nb_courses / h.type_jour.map(counts)
    day_counts = calendar.groupby('jour_num').size()
    matrix = d.pivot_table(index='jour_num', columns='heure', values='nb_courses', aggfunc='sum', fill_value=0)
    matrix = matrix.reindex(index=range(7), columns=range(24), fill_value=0).div(day_counts.reindex(range(7)), axis=0)
    matrix.index = DAYS
    return daily_type, h, matrix

def fmt(n, digits=2):
    if pd.isna(n): return '—'
    return f'{n:,.{digits}f}'.replace(',', '\u202f').replace('.', ',')
