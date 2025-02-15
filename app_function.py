import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

from sqlalchemy import select, create_engine, MetaData, Table, and_
from dash import dcc, html

color_palette = px.colors.qualitative.Plotly


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
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'padding': '10px',
        'width': '100%'
    })

    layout = html.Div([
        map,
        graphs,
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'alignItems': 'center',
        'justifyContent': 'center',
        'padding': '10px',
        'width': '100%'
    })

    return layout



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

    return dcc.Graph(id = 'update_health_systems_graph', figure=fig, style={'width': '40%', 'height': '40%'})

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

    return dcc.Graph(id='update_health_systems_graph_death', figure=fig, style={'width': '40%', 'height': '40%'})















