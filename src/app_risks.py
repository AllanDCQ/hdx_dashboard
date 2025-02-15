import os
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, MetaData, select, and_
from dash import dcc, html


INDICATORS_MAPPING = {
    "NT_ANT_WHZ_PO2": "Weight-for-height >+2 SD (overweight)",
    "NT_BW_LBW": "Prevalence of low birth weight among <br> new-borns",
    "WS_PPL_W-PRE": "Proportion of population using safely managed <br> drinking water services",
    "WS_PPL_W-B": "Proportion of population using basic drinking water services"
}

def generate_factors_risk_status_page(selected_countries_list, selected_year):
    """
    Generate the risk status page for the selected countries and year.

    :param selected_countries_list: List of selected countries with their alpha3 codes.
    :type selected_countries_list: list of dict
    :param selected_year: The selected year for which the data is to be displayed.
    :type selected_year: List[int]
    :return: A list of Dash HTML components representing the risk status page.
    :rtype: list
    """
    # Obtenir les codes pays au format correct
    country_codes = [c["alpha3"].upper() for c in selected_countries_list] if selected_countries_list else None

    df = get_risk_factors_data(country_codes,selected_year) if country_codes else get_risk_factors_data()
    if df.empty:
        return html.Div("No data available for selected countries")

    # Récupération des noms des pays
    country_names = get_country_names()
    df['country_name'] = df['id_country'].map(country_names)

    # Création des graphiques
    # 1. Graphique en haut à droite - Line plot pour Weight-for-height
    weight_height_df = df[df['id_indicator'] == 'NT_ANT_WHZ_PO2']
    # Tri des données par année avant de créer le graphique
    weight_height_df = weight_height_df.sort_values(by=['year_recorded'])
    fig1 = px.line(weight_height_df,
                   x='year_recorded',
                   y='value',
                   color='country_name',
                   title=INDICATORS_MAPPING['NT_ANT_WHZ_PO2'],
                   markers=True,
                   line_shape='linear')

    # Ajustement du titre pour qu'il passe à la ligne
    fig1.update_layout(
        title={
            'text': INDICATORS_MAPPING['NT_ANT_WHZ_PO2'],
            'yanchor': 'top',
            'y': 0.95,
            'xanchor': 'center',
            'x': 0.5,
            'pad': {'t': 20}
        },
        margin=dict(t=80),  # Ajout d'un espace supérieur pour le titre
        xaxis_title='Year',
        yaxis_title='Value',
        legend_title='Country',
        font=dict(size=12, family='Arial, sans-serif'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    figures_bottom = []

    # Graphique en barres groupées pour la prévalence de bas poids chez les nouveau-nés
    lbw_df = df[df['id_indicator'] == 'NT_BW_LBW']
    fig_lbw = px.bar(lbw_df,
                     x='year_recorded',
                     y='value',
                     color='country_name',
                     barmode='group',
                     title=INDICATORS_MAPPING['NT_BW_LBW'])
    fig_lbw.update_layout(
        title={
            'text': INDICATORS_MAPPING['NT_BW_LBW'],
            'yanchor': 'top',
            'y': 0.95,
            'xanchor': 'center',
            'x': 0.5,
            'pad': {'t': 20}
        },
        margin=dict(t=80),  # Ajout d'un espace supérieur pour le titre
        xaxis_title='Year',
        yaxis_title='Proportion (%)',
        legend_title='Country',
        font=dict(size=12, family='Arial, sans-serif'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.15,  # Espacement entre les barres des pays
        bargroupgap=0.1  # Espacement entre les barres des années
    )
    figures_bottom.append(fig_lbw)

    # Graphique en nuage de points pour la proportion de population ayant accès à l'eau potable sûre
    wpre_df = df[df['id_indicator'] == 'WS_PPL_W-PRE']
    fig_wpre = px.scatter(wpre_df,
                          x='year_recorded',
                          y='value',
                          size='value',
                          color='country_name',
                          title=INDICATORS_MAPPING['WS_PPL_W-PRE'])
    fig_wpre.update_layout(
        title={
            'text': INDICATORS_MAPPING['WS_PPL_W-PRE'],
            'yanchor': 'top',
            'y': 0.95,
            'xanchor': 'center',
            'x': 0.5,
            'pad': {'t': 20}
        },
        margin=dict(t=80),  # Ajout d'un espace supérieur pour le titre
        xaxis_title='Year',
        yaxis_title='Proportion (%)',
        legend_title='Country',
        font=dict(size=12, family='Arial, sans-serif'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    figures_bottom.append(fig_wpre)

    # Graphique en histogramme pour la proportion de population ayant accès à l'eau potable de base
    wb_df = df[df['id_indicator'] == 'WS_PPL_W-B']
    fig_wb = px.histogram(wb_df,
                          x='year_recorded',
                          y='value',
                          color='country_name',
                          barmode='group',
                          title=INDICATORS_MAPPING['WS_PPL_W-B'],
                          labels={'year_recorded': 'Year', 'value': 'Proportion (%)', 'country_name': 'Country'},
                          category_orders={"year_recorded": sorted(wb_df['year_recorded'].unique())})
    fig_wb.update_layout(
        title={
            'text': INDICATORS_MAPPING['WS_PPL_W-B'],
            'yanchor': 'top',
            'y': 0.95,
            'xanchor': 'center',
            'x': 0.5,
            'pad': {'t': 20}
        },
        margin=dict(t=80),  # Ajout d'un espace supérieur pour le titre
        xaxis_title='Year',
        yaxis_title='Proportion (%)',
        legend_title='Country',
        font=dict(size=12, family='Arial, sans-serif'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.15,  # Espacement entre les barres des années
        bargroupgap=0.1  # Espacement entre les barres des pays
    )
    figures_bottom.append(fig_wb)

    # -------------------------------------------------------- Map --------------------------------------------------- #
    map_div = html.Div([
        dcc.Loading(
            id="loading-indicator",
            type="circle",
            children=[
                dcc.Graph(
                    id="world-map",
                    config={'scrollZoom': True, 'displayModeBar': False},
                    figure={},
                    selectedData=None
                )
            ]
        )
    ], className="responsive-map_risk")
    # ---------------------------------------------------------------------------------------------------------------- #


    row_1 = html.Div([
        map_div,
        dcc.Graph(figure=fig1, className="responsive-column_risk-1"),
    ], className="responsive-row_risk")

    row_2 = html.Div([
        dcc.Graph(figure=fig_wpre, className="responsive-column_risk-2"),
        dcc.Graph(figure=fig_lbw, className="responsive-column_risk-2"),
        dcc.Graph(figure=fig_wb, className="responsive-column_risk-2"),
    ], className="responsive-row_risk")

    layout = html.Div([
        row_1,
        row_2,
    ])


    # Layout complet
    return layout


def get_risk_factors_data(country_codes=None,selected_year=None):
    """
    Fetches risk factors data from the database.

    :param country_codes: List of country codes to filter the data. If None, fetches data for all countries.
    :type country_codes: list of str or None
    :param selected_year: The selected year for which the data is to be fetched.
    :type selected_year: List[int]
    :return: DataFrame containing the risk factors data.
    :rtype: pandas.DataFrame
    """

    engine = create_engine(os.getenv("DATABASE_URL"))
    metadata = MetaData()
    metadata.reflect(bind=engine)

    try:
        timed_indicators = metadata.tables['Timed_Indicators']
    except KeyError:
        print("La table 'Timed_Indicators' n'a pas été trouvée dans la base de données.")
        return pd.DataFrame()

    # Constitution du ou des filtres
    indicator_filter = timed_indicators.c.id_indicator.in_(INDICATORS_MAPPING.keys())
    if country_codes:
        country_codes = [code.lower() for code in country_codes]  # Convertir en minuscules
        country_filter = timed_indicators.c.id_country.in_(country_codes)
        year_filter = timed_indicators.c.year_recorded.between(selected_year[0], selected_year[1])
        final_filter = and_(country_filter, indicator_filter,year_filter)
    else:
        final_filter = indicator_filter

    stmt = select(
        timed_indicators.c.id_country,
        timed_indicators.c.year_recorded,
        timed_indicators.c.id_indicator,
        timed_indicators.c.value,
        timed_indicators.c.sexe
    ).where(final_filter)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(stmt, conn)
            return df
    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête : {e}")
        return pd.DataFrame()

def get_country_names():
    """
    Fetches the country names from the database.

    :return: A dictionary mapping country codes to country names.
    :rtype: dict
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    metadata = MetaData()
    metadata.reflect(bind=engine)

    try:
        country_table = metadata.tables['Country']
    except KeyError:
        print("La table 'Country' n'a pas été trouvée dans la base de données.")
        return {}

    stmt = select(country_table.c.id_country, country_table.c.country_name)
    with engine.connect() as conn:
        result = conn.execute(stmt).fetchall()

    return {row[0]: row[1] for row in result}

def get_available_years_and_countries():
    """
    Fetches the available years and countries from the database.

    :return: A tuple containing a list of available years and a list of available countries.
    :rtype: tuple
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    metadata = MetaData()
    metadata.reflect(bind=engine)

    try:
        timed_indicators = metadata.tables['Timed_Indicators']
    except KeyError:
        print("La table 'Timed_Indicators' n'a pas été trouvée dans la base de données.")
        return [], []

    with engine.connect() as conn:
        years = conn.execute(select(timed_indicators.c.year_recorded.distinct())).fetchall()
        countries = conn.execute(select(timed_indicators.c.id_country.distinct())).fetchall()

    years = [year[0] for year in years]
    countries = [country[0] for country in countries]
    return years, countries