from pathlib import Path
from html import escape
import pandas as pd
import plotly.express as px
import streamlit as st
from analytics import load_data, metrics, grouped, calendar_for, demand, fmt

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Uber NYC | Analyse des mobilités', page_icon='🚕', layout='wide')
st.markdown("""<style>
.stApp {background:#f4f6fa;color:#172b4d;}
.block-container {max-width:1500px;padding:2.4rem 3rem 3rem;}
h1 {font-size:2.6rem!important;letter-spacing:-1.3px;font-weight:750!important;}
h1,h2,h3 {color:#132744;} h3 {font-size:1.1rem!important;}
[data-testid="stSidebar"] {background:#ffffff;border-right:1px solid #e6ebf2;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:5px 0;}
[data-testid="stMetric"] {background:white;border:1px solid #e4eaf3;border-radius:16px;padding:20px 22px;box-shadow:0 4px 16px #15294a05;}
[data-testid="stMetricLabel"] {color:#63738d;font-size:13px;}
[data-testid="stMetricValue"] {color:#102b52;font-weight:700;letter-spacing:-1px;}
[data-testid="stPlotlyChart"] {background:white;border:1px solid #e5eaf2;border-radius:18px;overflow:hidden;padding:8px;box-shadow:0 5px 20px #172b4d04;}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
[data-testid="stExpander"] {background:#ffffff;border-radius:14px;}
[data-testid="stMain"] [data-testid="stRadio"] > div[role="radiogroup"] {display:flex;gap:8px;flex-wrap:wrap;background:#ffffff;padding:10px;border:1px solid #e5eaf2;border-radius:16px;margin-bottom:14px;}
[data-testid="stMain"] [data-testid="stRadio"] label {background:#f3f6fb;padding:10px 18px!important;border-radius:10px;cursor:pointer;margin:0!important;transition:background .15s;}
[data-testid="stMain"] [data-testid="stRadio"] label:hover {background:#e7efff;}
[data-testid="stMain"] [data-testid="stRadio"] label:has(input:checked) {background:#dce9ff;color:#174c9b;box-shadow:inset 0 -2px #3977df;}
.eyebrow {font-size:11px;font-weight:750;letter-spacing:2px;color:#3c6de0;text-transform:uppercase;margin:8px 0;}
.insights {background:linear-gradient(115deg,#e9f1ff,#edf8f5);border:1px solid #d5e4f5;border-left:4px solid #3977df;border-radius:16px;padding:22px 26px;margin:20px 0 27px;}
.insights-title {color:#214f86;font-size:12px;text-transform:uppercase;letter-spacing:1.5px;font-weight:750;margin-bottom:12px;}
.insights ul {margin:0;padding-left:20px;color:#243c5c;}
.insights li {padding:4px 0;line-height:1.65;font-size:15px;}
@media(max-width:700px){.block-container{padding:1.2rem;} h1{font-size:2rem!important;}.insights{padding:18px;}}
</style>""", unsafe_allow_html=True)
COLORS = {'Bronx':'#3e9afb','Brooklyn':'#303fac','EWR':'#ea865c','Manhattan':'#892b93','Queens':'#e852b0','Staten Island':'#8b65d1'}
px.defaults.color_discrete_sequence = ['#2685ed','#2639a3','#20a697','#a47bdb']
px.defaults.color_discrete_map = COLORS

@st.cache_data(show_spinner='Lecture des données…')
def cached_data(signature):
    return load_data(ROOT / 'data')

pages = ['Vue d’ensemble', 'Demande et horaires', 'Géographie', 'Trajets et finances', 'À propos']
st.sidebar.title('UBER NYC')
st.sidebar.caption('ANALYSE DES MOBILITÉS · 2025')
page = st.radio('Navigation', pages, horizontal=True, label_visibility='collapsed', key='navigation')
try:
    paths = [ROOT / 'data' / n for n in ['fact_activite.csv', 'dim_zone.csv']]
    f = cached_data(tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in paths))
except (OSError, ValueError, KeyError) as e:
    st.error(f'Impossible de charger les CSV du dossier data : {e}')
    st.stop()
months = st.sidebar.multiselect('Mois', sorted(f.mois.unique()), default=sorted(f.mois.unique()))
boroughs = st.sidebar.multiselect('Boroughs', sorted(f.Borough.unique()), default=sorted(f.Borough.unique()))
st.sidebar.caption('Les conclusions et les graphiques suivent ces filtres. Les captures Power BI sont fixes.')

def chart(fig):
    fig.update_layout(template='plotly_white', font=dict(family='Arial',size=13,color='#50627b'),
        title=dict(font=dict(size=17,color='#172e50'),x=0.03,y=0.95),
        paper_bgcolor='white',plot_bgcolor='white',height=420,
        margin=dict(l=25,r=25,t=75,b=55),
        legend=dict(orientation='h',yanchor='top',y=-0.2,x=0,title_text=''),
        hoverlabel=dict(bgcolor='#142d50',font_color='white'),separators=', ')
    fig.update_xaxes(gridcolor='#edf1f7',zeroline=False)
    fig.update_yaxes(gridcolor='#edf1f7',zeroline=False)
    st.plotly_chart(fig, use_container_width=True, theme=None,
        config={'displaylogo':False,'displayModeBar':False,'scrollZoom':False,'responsive':True})

def cards(m, names):
    cols = st.columns(len(names))
    for col, name in zip(cols, names):
        col.metric(name, fmt(m[name], 0 if name in ['Courses','Attentes valides'] else 2))

def insight_box(items, title='À retenir'):
    bullets=''.join('<li>'+escape(item)+'</li>' for item in items)
    st.markdown('<section class="insights"><div class="insights-title">'+escape(title)+'</div><ul>'+bullets+'</ul></section>',unsafe_allow_html=True)

def page_insights(page,d,c,m):
    items=[]
    monthly=grouped(d,'mois').sort_values('mois')
    if page==pages[0]:
        b=grouped(d,'Borough').sort_values('Courses',ascending=False).iloc[0]
        items.append(f"{b.Borough} concentre {fmt(100*b.Courses/m['Courses'])} % des courses de votre sélection.")
        if len(monthly)>1:
            a,z=monthly.iloc[0],monthly.iloc[-1]
            days=c.assign(mois=c.date_course.dt.strftime('%Y-%m')).groupby('mois').size()
            change=100*((z.Courses/days[z.mois])/(a.Courses/days[a.mois])-1)
            items.append(f"De {a.mois} à {z.mois}, les courses par jour {'augmentent' if change>=0 else 'diminuent'} de {fmt(abs(change))} %. Cette comparaison tient compte de la durée des mois.")
        daily=d.groupby('date_course').nb_courses.sum()
        items.append(f"Le jour le plus actif est le {daily.idxmax():%d/%m/%Y} : {fmt(daily.max(),0)} courses.")
    elif page==pages[1]:
        t,h,_=demand(d,c);v=t.set_index('type_jour')['Courses / jour']
        if {'Semaine','Week-end'}.issubset(v.index) and v['Semaine']>0:
            delta=100*(v['Week-end']/v['Semaine']-1)
            items.append(f"Un jour de week-end compte {fmt(abs(delta))} % de courses {'en plus' if delta>=0 else 'en moins'} qu’un jour de semaine.")
        for typ in h.type_jour.unique():
            sub=h[h.type_jour.eq(typ)];peak=sub.loc[sub['Courses / jour et heure'].idxmax()]
            items.append(f"{typ} : le pic est à {int(peak.heure)} h, avec {fmt(peak['Courses / jour et heure'],0)} courses en moyenne sur ce créneau.")
        items.append('Les besoins varient selon le jour et l’heure : un seul profil horaire ne suffit pas pour organiser l’activité.')
    elif page==pages[2]:
        z=grouped(d,['LocationID','Zone','Borough']).sort_values('Courses',ascending=False)
        items.append(f"{z.iloc[0].Zone} est la zone de départ la plus active : {fmt(z.iloc[0].Courses,0)} courses.")
        items.append(f"Les dix premières zones rassemblent {fmt(100*z.head(10).Courses.sum()/m['Courses'])} % des courses.")
        b=grouped(d,'Borough');ok=b[(b['Attentes valides']>=1000)&(b['Couverture attente (%)']>=95)]
        if not ok.empty:
            row=ok.loc[ok['Attente moyenne (min)'].idxmax()]
            items.append(f"Parmi les boroughs avec au moins 1 000 attentes valides et 95 % de couverture, {row.Borough} affiche l’attente la plus longue : {fmt(row['Attente moyenne (min)'])} min.")
        n=d.loc[d.LocationID.eq(1),'nb_courses'].sum()
        if 0<n<1000:items.append(f"EWR ne compte que {fmt(n,0)} course(s). C’est trop peu pour juger la performance de cet aéroport.")
    else:
        if len(monthly)>1:
            a,z=monthly.iloc[0],monthly.iloc[-1]
            for label,name,unit in [('Le tarif moyen','Tarif moyen ($)','$'),('L’attente moyenne','Attente moyenne (min)','min')]:
                if pd.notna(a[name]) and a[name]>0:
                    delta=100*(z[name]/a[name]-1)
                    items.append(f"{label} passe de {fmt(a[name])} à {fmt(z[name])} {unit} entre {a.mois} et {z.mois} ({'+' if delta>=0 else ''}{fmt(delta)} %).")
        else:
            items.append(f"Une course coûte en moyenne {fmt(m['Tarif moyen ($)'])} $ de tarif de base et dure {fmt(m['Durée moyenne (min)'])} minutes.")
        items.append('Un tarif moyen plus élevé peut venir de trajets différents : cela ne prouve pas une hausse des prix à trajet identique.')
        items.append('Le versement chauffeur par minute de trajet n’est pas un salaire net : les frais et le temps entre les courses ne sont pas inclus.')
    insight_box(items)

def about():
    st.markdown('<div class="eyebrow">La démarche</div>',unsafe_allow_html=True)
    st.title('À propos du projet')
    insight_box(['Des données publiques NYC TLC pour comprendre les courses Uber à New York.', 'Une première analyse réalisée dans Power BI, puis une interface Streamlit pour partager les résultats.', 'Des indicateurs recalculés depuis les CSV ; les captures conservent la trace du rapport initial.'], 'Le projet en trois points')
    st.markdown('''### Comprendre l’activité, puis partager les résultats
Ce projet étudie les courses Uber à New York : leur répartition dans le temps et l’espace, les délais de prise en charge et les caractéristiques économiques des trajets. L’objectif est de repérer des rythmes d’activité et des territoires à approfondir, sans attribuer de causes que les données ne permettent pas de démontrer.

### Des données publiques à une application interactive
Les données sources sont les **High Volume For-Hire Vehicle Trip Records** de la **NYC Taxi & Limousine Commission (TLC)**, avec le référentiel des Taxi Zones.

1. Préparation et agrégation des données dans un pipeline Python / DuckDB décrit dans le projet initial.
2. Construction d’une table d’activité au grain **date × heure × zone de départ**, reliée au référentiel des zones.
3. Modélisation et premières analyses dans **Power BI**, avec des mesures DAX et quatre pages de rapport.
4. Recréation des graphiques en **Python, Streamlit et Plotly**, pour partager les résultats dans une interface consultable et filtrable.

Cette version repart des CSV fournis ; elle ne relance pas la préparation des Parquet bruts. Le fichier d’audit identifie le périmètre comme Uber. Le filtre fournisseur, les critères d’exclusion et la formule amont du délai ne peuvent pas être vérifiés sans le script initial.

[Source officielle TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) · [Dictionnaire HVFHV](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf)
''')
    st.write(f'**Périmètre des CSV :** {f.date_course.min():%d/%m/%Y} au {f.date_course.max():%d/%m/%Y} · {fmt(f.nb_courses.sum(),0)} courses · {fmt(len(f),0)} lignes agrégées.')

    st.subheader('Les quatre rapports Power BI d’origine')
    st.caption('Archives visuelles : leurs filtres peuvent différer de la sélection actuelle. Tous les chiffres interactifs sont recalculés depuis les CSV.')
    for name, filename in zip(pages[:4], ['01_vue_ensemble.png','02_demande.png','03_geographie.png','04_finances.png']):
        with st.expander(name):
            path = ROOT / 'captures_power_bi' / filename
            if path.exists(): st.image(str(path), caption=name, width='stretch')
            else: st.warning(f'Capture absente : {filename}')

if page == 'À propos':
    about()
    st.stop()
if not months or not boroughs:
    st.info('Sélectionne au moins un mois et un borough pour explorer les résultats.')
    st.stop()
d = f[f.mois.isin(months) & f.Borough.isin(boroughs)].copy()
if d.empty or d.nb_courses.sum() == 0:
    st.info('Aucune course pour cette sélection.')
    st.stop()
c = calendar_for(f, months)
m = metrics(d)
st.markdown('<div class="eyebrow">Uber NYC · Tableau de bord</div>',unsafe_allow_html=True)
st.title(page)
st.caption('NYC TLC · ' + ', '.join(months) + ' · ' + ', '.join(boroughs))
if any(len(f.loc[f.mois.eq(month), 'date_course'].unique()) != pd.Period(month).days_in_month for month in months):
    st.warning('Au moins un mois est incomplet : les moyennes utilisent uniquement les dates disponibles dans la source.')

page_insights(page,d,c,m)

if page == pages[0]:
    m['Courses / jour'] = m['Courses'] / len(c)
    cards(m, ['Courses', 'Courses / jour', 'Tarif moyen ($)', 'Durée moyenne (min)'])
    st.caption('Tarif de base cumulé : ' + fmt(m['Tarif de base total ($)']) + ' $ — ce montant ne représente pas le chiffre d’affaires net d’Uber.')
    daily = d.groupby('date_course').nb_courses.sum().reindex(c.date_course, fill_value=0).rename('Courses').reset_index()
    b = grouped(d, 'Borough').sort_values('Courses', ascending=False)
    left,right = st.columns([1.4,1])
    with left: chart(px.line(daily, x='date_course', y='Courses', title='Évolution quotidienne', labels={'date_course':'Date'}))
    with right: chart(px.bar(b.sort_values('Courses'), x='Courses', y='Borough', orientation='h', title='Répartition par borough'))
    monthly = grouped(d, 'mois').sort_values('mois')
    counts = c.assign(mois=c.date_course.dt.strftime('%Y-%m')).groupby('mois').size()
    monthly['Jours observés'] = monthly.mois.map(counts)
    monthly['Courses / jour'] = monthly.Courses/monthly['Jours observés']
    st.dataframe(monthly[['mois','Courses','Jours observés','Courses / jour','Tarif moyen ($)']], hide_index=True, width='stretch')

elif page == pages[1]:
    types,h,heat = demand(d,c)
    hourly = d.groupby('heure').nb_courses.sum().reindex(range(24),fill_value=0).rename('Courses').reset_index()
    l,r = st.columns([1.4,1])
    with l: chart(px.bar(hourly,x='heure',y='Courses',title='Courses par heure',labels={'heure':'Heure de départ'}))
    with r: chart(px.bar(types,x='type_jour',y='Courses / jour',title='Un jour moyen : semaine et week-end',labels={'type_jour':''}))
    chart(px.line(h,x='heure',y='Courses / jour et heure',color='type_jour',title='Profils horaires normalisés',labels={'heure':'Heure de départ','type_jour':'Type de jour'}))
    chart(px.imshow(heat,aspect='auto',color_continuous_scale='Blues',labels=dict(x='Heure de départ',y='Jour',color='Courses moyennes'),title='Activité moyenne par créneau et jour de semaine'))
    st.caption('Les cellules sans jour correspondant sont vides. Les volumes horaires portent sur l’heure de départ, pas nécessairement sur l’heure de demande.')

elif page == pages[2]:
    cards(m,['Courses','Attente moyenne (min)','Couverture attente (%)'])
    zones=grouped(d,['LocationID','Zone','Borough'])
    top=zones.nlargest(10,'Courses').sort_values('Courses')
    top['Zone affichée']=top.Zone+' · '+top.LocationID.astype(str)
    chart(px.bar(top,x='Courses',y='Zone affichée',orientation='h',title='Les dix zones de départ les plus actives'))
    a,b,cc=st.columns(3)
    level=a.selectbox('Chaque point représente', ['Borough','Zone'])
    minimum=b.number_input('Minimum d’attentes valides',min_value=1,value=1000,step=100)
    coverage=cc.slider('Couverture minimale (%)',0,100,95)
    g=zones if level=='Zone' else grouped(d,'Borough')
    eligible=g[(g['Attentes valides']>=minimum)&(g['Couverture attente (%)']>=coverage)]
    st.caption(f'{len(eligible)} / {len(g)} groupes affichés. Seuils exploratoires, sans garantie de précision statistique.')
    if not eligible.empty:
        chart(px.scatter(eligible,x='Attente moyenne (min)',y='Tarif moyen ($)',size='Courses',color='Borough',hover_name='Zone' if level=='Zone' else 'Borough',hover_data=['Courses','Attentes valides','Couverture attente (%)'],size_max=85 if level=='Borough' else 40, title='Attente et tarif moyen par '+('borough' if level=='Borough' else 'zone'), color_discrete_map=COLORS))
    else: st.info('Aucun groupe ne satisfait les seuils sélectionnés.')
    st.subheader('Zoom aéroports : effectifs et couverture')
    ewr=d.loc[d.LocationID.eq(1), 'nb_courses'].sum()
    if 0 < ewr < 1000:
        st.caption(f'EWR : seulement {fmt(ewr,0)} course(s) dans cette sélection. Son attente moyenne ne permet pas de caractériser la performance de cet aéroport.')
    airport=d[d.LocationID.isin([1,132,138])]
    if not airport.empty:
        st.dataframe(grouped(airport,['Zone','mois'])[['Zone','mois','Courses','Attentes valides','Couverture attente (%)','Attente moyenne (min)','Tarif moyen ($)']],hide_index=True,width='stretch')
    with st.expander('Toutes les zones'):
        st.dataframe(zones,hide_index=True,width='stretch')

elif page == pages[3]:
    cards(m,['Tarif moyen ($)','Durée moyenne (min)','Distance moyenne (miles)','Versement moyen ($)','Attente moyenne (min)'])
    small=grouped(d,'Borough')
    small=small[small.Courses < 1000]
    if not small.empty:
        st.caption('Effectifs faibles — ne pas interpréter ces moyennes comme des performances représentatives : ' + ', '.join(f'{r.Borough} ({fmt(r.Courses,0)} courses)' for _,r in small.iterrows()))
    bm=grouped(d,['Borough','mois']); monthly=grouped(d,'mois').sort_values('mois'); b=grouped(d,'Borough')
    for col,name in zip(st.columns(3),['Tarif moyen ($)','Attente moyenne (min)','Pourboire moyen ($)']):
        with col:
            st.subheader(name)
            table=bm.pivot(index='Borough',columns='mois',values=name)
            table['Total pondéré']=b.set_index('Borough')[name]
            total=monthly.set_index('mois')[name].to_dict();total['Total pondéré']=m[name]
            table.loc['Ensemble']=pd.Series(total)
            st.dataframe(table.round(2),width='stretch')
    for cols,source,category,names in [(st.columns(2),monthly,'mois',['Tarif moyen ($)','Attente moyenne (min)']),(st.columns(2),b,'Borough',['Tarif par mile ($)','Versement par minute ($)'])]:
        for col,name in zip(cols,names):
            with col: chart(px.bar(source.sort_values(name) if category=='Borough' else source,x=name,y=category,orientation='h',title=name))

st.caption('Source : NYC TLC · Calculs sur les CSV fournis · Méthodologie et archives Power BI dans « À propos ».')
