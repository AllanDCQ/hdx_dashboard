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























