import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

from sqlalchemy import select, create_engine, MetaData, Table, and_
from dash import dcc, html

color_palette = px.colors.qualitative.Plotly
os.environ["DATABASE_URL"] = "postgresql://webscraping_db_user:35RuggWvxnsRNbARA2QmiBqOpo0rVo83@dpg-cughkud6l47c73be2j10-a.frankfurt-postgres.render.com:5432/webscraping_db"


def generate_country_menu(country_data):
    """
    Generate a dropdown menu for selecting countries, organized by regions and subregions.

    :param country_data: A dictionary containing country data organized by region and subregion.
    :return: A list of Dash Bootstrap Components (dbc) DropdownMenu items.
    :rtype: list
    """

    menu_items = []

    for region, subregions in country_data["regions"].items():
        subregion_menus = []

        for subregion, countries in subregions.items():
            if isinstance(countries, list):
                country_items = [
                    dbc.DropdownMenuItem(country["name"], id=country['alpha3'], n_clicks=0) for country in countries
                ]
                subregion_menus.append(
                    dbc.DropdownMenu(
                        label=subregion,
                        children=country_items,
                        direction="right",
                        toggle_style={"width": "100%"}
                    )
                )

        # Region level menu
        menu_items.append(
            dbc.DropdownMenu(
                label=region,
                children=subregion_menus,
                direction="right",
                toggle_style={"width": "100%"}
            )
        )

    return menu_items



def get_country_name_by_alpha3(alpha3, country_data):
    """
    Retrieve the country name based on the alpha3 code from the country data.

    :param alpha3: The alpha3 code of the country.
    :type alpha3: str
    :param country_data: The dictionary containing country data.
    :type country_data: dict
    :return: The name of the country or None if not found.
    :rtype: str or None
    """
    return next((country["name"] for region in country_data["regions"]
                 for subregion in country_data["regions"][region]
                 for country in country_data["regions"][region][subregion]
                 if isinstance(country, dict) and country["alpha3"] == alpha3), None)




INDICATORS_MAPPING = {
        "NT_ANT_WHZ_PO2": "Weight-for-height >+2 SD (overweight)",
        "NT_BW_LBW": "Prevalence of low birth weight among <br> new-borns",
        "WS_PPL_W-PRE": "Proportion of population using safely managed <br> drinking water services",
        "WS_PPL_W-B": "Proportion of population using basic drinking water services"
    }

def generate_factors_risk_status_page(selected_countries_list, selected_year):
    """Génère la page des facteurs de risque"""
    # Obtenir les codes pays au format correct
    country_codes = [c["alpha3"].upper() for c in selected_countries_list] if selected_countries_list else None

    df = get_risk_factors_data(country_codes) if country_codes else get_risk_factors_data()
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

    # 2-4. Les trois graphiques en bas
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

    # Création du layout avec la carte existante
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
    ], style={'width': '100%', 'height': '40vh', 'marginBottom': '60px'})  # Augmentation de marginBottom pour décaler la carte

    # Layout complet
    return [
        # Première rangée avec la carte
        html.Div([
            map_div
        ], style={'display': 'flex', 'flexDirection': 'row', 'marginBottom': '20px'}),

        # Deuxième rangée avec deux graphiques
        html.Div([
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=figures_bottom[0])
            )), width=6, style={'marginRight': '20px'}),
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=figures_bottom[1])
            )), width=6)
        ], style={'display': 'flex', 'flexDirection': 'row', 'marginTop': '60px'}),  # Augmentation de marginTop pour décaler les graphiques

        # Troisième rangée avec deux graphiques
        html.Div([
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=figures_bottom[2])
            )), width=6, style={'marginRight': '20px'}),
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=fig1)
            )), width=6)
        ], style={'display': 'flex', 'flexDirection': 'row', 'marginTop': '40px'})  # Augmentation de marginTop pour décaler les graphiques
    ]


def get_risk_factors_data(country_codes=None):
    """
    Récupère les données des facteurs de risque.
    Si country_codes est fourni, ne récupère que ces pays.
    Sinon, récupère tous les enregistrements pour les indicateurs spécifiés.
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
        final_filter = and_(country_filter, indicator_filter)
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
    Récupère les noms des pays depuis la base de données.
    Retourne un dictionnaire {id_country: country_name}.
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
    Récupère les années et les pays disponibles dans la base de données.
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


#################################################### Health Status Page ################################################


def generate_health_status_page(selected_countries_list, selected_year):
    """
    Generate the health status page layout.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: The layout of the health status page.
    :rtype: dash.development.base_component.Component
    """

    graph3=update_MMR100k_graph(selected_countries_list, selected_year)
    graph4=update_SH_DYN_MORT_graph(selected_countries_list, selected_year)
    graph5=update_SH_DYN_MORT_neo_graph(selected_countries_list, selected_year)
    # Colonne de gauche contenant la carte
    map_column = html.Div([
        # Div pour la carte
        html.Div([
            dcc.Loading(
                id="loading-indicator",
                type="circle",
                children=[
                    dcc.Graph(
                        id="world-map",
                        config={'scrollZoom': True, 'displayModeBar': False},
                        figure={},
                        selectedData=None,
                        style={'height': '40vh', 'width': '100%'}
                    )
                ]
            ),
            graph3

        ], style={'width': '50vh', 'height': '100vh', 'display': 'inline-block',
                  'verticalAlign': 'top', 'overflow': 'hidden'}),

        # Graphiques (droite)
        html.Div([
            graph4,
            graph5
        ], style={'width': '60%', 'height': '40vh', 'display': 'inline-block', 'paddingLeft': '10px'})
    ], style={'display': 'flex', 'width': '100%', 'padding': '2px'})

    # Génération des graphiques
    graph1 = update_WHOSIS_000001_graph(selected_countries_list, selected_year)
    graph2 = update_WHOSIS_000002_graph(selected_countries_list, selected_year)

    # Colonne de droite contenant les graphiques
    graphs_column = html.Div([
        graph1,
        graph2,
    ], style={
        'width': '40%',
        'display': 'flex',
        'flexDirection': 'column',
        'gap': '5px',
        'padding': '5px'
    })

    # Conteneur principal en ligne (deux colonnes)
    layout = html.Div([
        map_column,
        graphs_column
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'width': '100%',
        'height': '100%',
    })

    return layout


#---------------------------------------------------- MMR100k Graph ---------------------------------------------------#

def get_MMR100k_data(selected_countries_list, selected_year):
    """
    Retrieve the MMR100k data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the MMR100k data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "MMR_100k",
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1])
            )
        )
        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_MMR100k_graph(selected_countries_list, selected_year):
    """
    Update the MMR100k graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated MMR100k data.
    :rtype: dash.development.base_component.Component
    """
    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        df = get_MMR100k_data(selected_countries_list, selected_year)
        # Création du graphique avec Plotly
        fig = px.line(
            data_frame=df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les courbes par pays
            custom_data=["id_country"],
            color_discrete_sequence=px.colors.qualitative.G10,
        )

        fig.update_layout(
            title={
                'text': "<b>Maternal mortality ratio</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (per 100k live births)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',  # Centre le titre sur la zone de tracé
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<extra></extra>",
            mode="lines+markers",
            hovertext=None,
            showlegend=True,
        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='health-status-graph', figure=fig, style={'width': '100%', 'height': '40vh'})

#------------------------------------------------- WHOSIS_000001 Graph ------------------------------------------------#

def get_WHOSIS_000001_data(selected_countries_list, selected_year):
    """
    Retrieve the WHOSIS_000001 data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the WHOSIS_000001 data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "WHOSIS_000001",
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
                indicator_table.columns.sexe=="Both sexes"
            )
        )
        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_WHOSIS_000001_graph(selected_countries_list, selected_year):
    """
    Update the WHOSIS_000001 graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated WHOSIS_000001 data.
    :rtype: dash.development.base_component.Component
    """
    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        df = get_WHOSIS_000001_data(selected_countries_list, selected_year)
        # Création du graphique avec Plotly
        fig = px.line(
            data_frame=df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les courbes par pays
            custom_data=["id_country"],
            color_discrete_sequence=px.colors.qualitative.G10,
        )

        fig.update_layout(
            title={
                'text': "<b>Life expectancy at birth</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (years)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<extra></extra>",
            mode="lines+markers",
            showlegend=True,

        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='health-status-graph', figure=fig, style={'width': '100%', 'height': '40vh'})

#------------------------------------------------- WHOSIS_000002 Graph ------------------------------------------------#

def get_WHOSIS_000002_data(selected_countries_list, selected_year):
    """
    Retrieve the WHOSIS_000002 data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the WHOSIS_000002 data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "WHOSIS_000002",
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
                indicator_table.columns.sexe=="Both sexes"
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_WHOSIS_000002_graph(selected_countries_list, selected_year):
    """
    Update the WHOSIS_000002 graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated WHOSIS_000002 data.
    :rtype: dash.development.base_component.Component
    """

    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        df = get_WHOSIS_000002_data(selected_countries_list, selected_year)
        # Création du graphique avec Plotly
        fig = px.line(
            data_frame= df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color_discrete_map=country_to_color,
            color="id_country",
            custom_data=["id_country"],
            color_discrete_sequence=px.colors.qualitative.G10,
        )
        fig.update_layout(
            title={
                'text': "<b>Healthy life expectancy at birth</b>",
                'y': 0.97,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (years)",
            legend_title="Country",
            margin={'t': 30},
            title_xref='paper'
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country:%{customdata[0]}<extra></extra>",
            mode="lines+markers",
            hovertext=None,
            showlegend=True,
        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='health-status-graph', figure=fig,style={'width': '100%', 'height': '40vh'})

#-------------------------------------------------- SH_DYN_MORT Graph -------------------------------------------------#

def get_SH_DYN_MORT_data(selected_countries_list, selected_year):
    """
    Retrieve the SH_DYN_MORT data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the SH_DYN_MORT data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator.in_(["SH.DYN.MORT", "SH.DYN.MORT.FE", "SH.DYN.MORT.MA"]),
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_SH_DYN_MORT_graph(selected_countries_list, selected_year):
    """
    Update the SH_DYN_MORT graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated SH_DYN_MORT data.
    :rtype: dash.development.base_component.Component
    """

    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        # Récupérer les données pour les filles et les garçons
        df = get_SH_DYN_MORT_data(selected_countries_list, selected_year)

        # Filtrer les données pour les filles et les garçons
        df_female = df[df['id_indicator'] == 'SH.DYN.MORT.FE']
        df_male = df[df['id_indicator'] == 'SH.DYN.MORT.MA']

        # Ajouter une colonne 'gender' pour indiquer si c'est pour les filles ou les garçons
        df_female = df_female.assign(gender='Female')
        df_male = df_male.assign(gender='Male')

        # Combiner les DataFrames des filles et des garçons
        df_combined = pd.concat([df_female, df_male])
        df_combined = df_combined.sort_values("id_country")

        # Création du graphique à barres avec Plotly
        fig = px.bar(
            data_frame=df_combined,
            x="year_recorded",  # Année sur l'axe des X
            y="value",  # Taux de mortalité sur l'axe des Y
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les barres par pays
            barmode="group",  # Afficher les barres côte à côte
            custom_data=["id_country", "gender"],
            facet_col=None,  # Pas de facettage, un seul graphique
            color_discrete_sequence=px.colors.qualitative.G10
        )

        fig.update_layout(
            title={
                'text': "<b>Mortality Rate under 5 years</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (per 1,000 live births)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',  # Centre le titre sur la zone de tracé
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<br>Gender: %{customdata[1]}<extra></extra>",
            hovertext=None,
            showlegend=True,
        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='mortality-graph', figure=fig, style={'width': '100%', 'height': '40vh'})

#--------------------------------------------- SH_DYN_MORT_neonatal Graph ---------------------------------------------#

def get_SH_DYN_MORT_neo_data(selected_countries_list, selected_year):
    """
    Retrieve the SH_DYN_MORT_neo data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the SH_DYN_MORT_neo data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator.in_(['SH.DYN.NMRT']),
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_SH_DYN_MORT_neo_graph(selected_countries_list, selected_year):
    """
    Update the SH_DYN_MORT_neo graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated SH_DYN_MORT_neo data.
    :rtype: dash.development.base_component.Component
    """
    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        # Récupérer les données de mortalité néonatale
        df = get_SH_DYN_MORT_neo_data(selected_countries_list, selected_year)

        # Filtrer les données pour la mortalité néonatale (identifiant 'SH.DYN.NMRT')
        df_neonatal = df[df['id_indicator'] == 'SH.DYN.NMRT']

        # Création du graphique en ligne avec Plotly
        fig = px.line(
            data_frame=df_neonatal,
            x="year_recorded",  # Année sur l'axe des X
            y="value",  # Taux de mortalité néonatale sur l'axe des Y
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les lignes par pays
            markers=True,  # Ajouter des marqueurs pour chaque point de donnée
            custom_data=["id_country"],  # Données supplémentaires pour le survol
            color_discrete_sequence=px.colors.qualitative.G10,
        )

        fig.update_layout(
            title={
                'text': "<b>Neonatal mortality rate</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (per 1,000 live births)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',  # Centre le titre sur la zone de tracé
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<extra></extra>",
            hovertext=None,
            showlegend=True,
        )

        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )

    else:
        fig = {}

    return dcc.Graph(id='mortality-neo-graph', figure=fig, style={'width': '100%', 'height': '40vh'})


########################################################################################################################

















def generate_coverage_status_page(selected_countries_list):
    map = html.Div([
        dcc.Loading(
            id="loading-indicator",  # ID pour l'indicateur de chargement
            type="circle",  # Type de l'indicateur : 'circle', 'dot', 'default'
            children=[
                dcc.Graph(
                    id="world-map",
                    config={'scrollZoom': True, 'displayModeBar': False},
                    figure={},  # This initializes the map when the app loads
                    selectedData=None  # We use this property to capture selected country data
                )
            ]
        )
    ], style={'width': '60%', 'height': '40vh'})

    something = html.Div([html.H4("Risk Factor : Under Construction")], style={'width': '40%', 'height': '80vh'})

    row_1 = html.Div([
        map,
        something,
    ], style={'display': 'flex', 'flexDirection': 'row', 'padding': '5px','width': '100%'}),


    return row_1







################################################### Health Systems Page ################################################
def generate_health_systems_page(selected_countries_list, selected_year):

    map = html.Div([
        dcc.Loading(
            id="loading-indicator",  # ID pour l'indicateur de chargement
            type="circle",  # Type de l'indicateur : 'circle', 'dot', 'default'
            children=[
                dcc.Graph(
                    id="world-map",
                    config={'scrollZoom': True, 'displayModeBar': False},
                    selectedData=None  # We use this property to capture selected country data
                )
            ]
        )
    ], style={'width': '60%', 'height': '50vh'})

    birth_graph = update_health_systems_graph_birth(selected_countries_list, selected_year)
    death_graph = update_health_systems_graph_death(selected_countries_list, selected_year)

    graphs = html.Div([
        birth_graph,
        death_graph
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'alignItems': 'center',
        'justifyContent': 'center',
        'padding': '10px',
        'width': '100%'
    })

    row_health_systems = html.Div([
        map,
        graphs,
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'padding': '10px',
        'width': '100%'
    })

    return row_health_systems



def get_health_systems_data_birth(selected_countries_list, selected_year) :

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]


    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection :
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query= select(indicator_table).where(
            indicator_table.columns.id_indicator == "SP.REG.BRTH.ZS",
            indicator_table.columns.id_country.in_(country_codes),
            indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1])
        )

        result = connection.execute(query).fetchall()
        df_birth = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])

        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        df_birth["id_country"] = df_birth["id_country"].str.lower().map(country_mapping)

    return df_birth

def get_health_systems_data_death(selected_countries_list, selected_year) :

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]

    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection :
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query= select(indicator_table).where(
            indicator_table.columns.id_indicator == "SP.REG.DTHS.ZS",
            indicator_table.columns.id_country.in_(country_codes),
            indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1])
        )

        result = connection.execute(query).fetchall()
        df_death = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])

        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        df_death["id_country"] = df_death["id_country"].str.lower().map(country_mapping)

    return df_death

def get_health_systems_data_uhc(selected_countries_list, selected_year) :

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]

    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection :
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query= select(indicator_table).where(
            indicator_table.columns.id_indicator == "SH.UHC.SRVS.CV.XD",
            indicator_table.columns.id_country.in_(country_codes),
            indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1])
        )

        result = connection.execute(query).fetchall()
        print(result)
        df_uhc = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])

        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        df_uhc["id_country"] = df_uhc["id_country"].str.lower().map(country_mapping)

    return df_uhc





def update_health_systems_graph_birth(selected_countries_list, selected_year) :
    if selected_countries_list :
        df_birth = get_health_systems_data_birth(selected_countries_list, selected_year)

        df_birth = df_birth.dropna(subset=["year_recorded", "value", "id_country"])

        # Création du graphique
        fig = px.line(
            data_frame = df_birth,
            x = "year_recorded",
            y = "value",
            color = "id_country",
            title = f"Completeness of birth registration from {selected_year[0]} to {selected_year[1]}",
            markers=True,
            #hover_name = {"year_recorded": True, "value": True}
        )
    else :
        fig = {}

    return dcc.Graph(id = 'update_health_systems_graph', figure=fig, style={'width': '60%', 'height': '40vh'})

def update_health_systems_graph_death(selected_countries_list, selected_year) :
    if selected_countries_list :
        df_death = get_health_systems_data_death(selected_countries_list, selected_year)

        df_death = df_death.dropna(subset=["year_recorded", "value", "id_country"])

        fig = px.line(
            data_frame = df_death,
            x = "year_recorded",
            y = "value",
            color = "id_country",
            title = f"Completeness of death registration from {selected_year[0]} to {selected_year[1]}",
            markers=True,
            #hover_data={"year_recorded": True, "value": True}
        )
    else :
        fig = {}

    return dcc.Graph(id='update_health_systems_graph_death', figure=fig, style={'width': '50%', 'height': '40vh'})















