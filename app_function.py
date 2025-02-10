import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import os

from sqlalchemy import select, create_engine, MetaData, Table, and_

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


def generate_health_status_page(selected_countries_list, selected_year):

    

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
    
    graph= update_health_graph(selected_countries_list,selected_year)

    row_1 = html.Div([
        map,graph
    ], style={'display': 'flex', 'flexDirection': 'row', 'padding': '5px','width': '100%'}),


    return row_1

def get_health_data(country_codes, selected_year):
    
    os.environ["BASE_URL"] = "postgresql://webscraping_db_user:35RuggWvxnsRNbARA2QmiBqOpo0rVo83@dpg-cughkud6l47c73be2j10-a.frankfurt-postgres.render.com:5432/webscraping_db" 

    database_url = os.getenv("BASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "MMR_100k",
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(2000, selected_year)
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])

    return df



def update_health_graph(selected_countries_list, selected_year):

    # Liste des alpha3 des pays sélectionnés
    country_codes = [c["alpha3"].lower() for c in selected_countries_list]

    # Récupérer les données filtrées
    #if country_codes:
    if country_codes:
        df = get_health_data(country_codes, selected_year)
        #else:
        #    print("No data found")
        #    return go.Figure()  # Retourne un graphique vide si aucune donnée trouvée

        # Création du graphique avec Plotly
        fig = px.line(
            data_frame= df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color="id_country",  # Différencier les courbes par pays
            title=f"Taux de mortalité maternelle en {selected_year}"
        )
    else:
        fig = {}
    
    return dcc.Graph(id='health-status-graph', figure=fig,style={'width': '60%', 'height': '40vh'})
    


def generate_factors_risk_status_page(selected_countries_list):

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

    something = html.Div([html.H4("Health status : Under Construction")], style={'width': '40%', 'height': '80vh'})

    row_1 = html.Div([
        map,
        something,
    ], style={'display': 'flex', 'flexDirection': 'row', 'padding': '5px','width': '100%'}),


    return row_1

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

def generate_health_systems_page(selected_countries_list):
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

    something = html.Div([html.H4("Health systems : Under Construction")], style={'width': '40%', 'height': '80vh'})

    row_1 = html.Div([
        map,
        something,
    ], style={'display': 'flex', 'flexDirection': 'row', 'padding': '5px','width': '100%'}),


    return row_1
