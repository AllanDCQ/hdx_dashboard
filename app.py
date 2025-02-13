import json
import os
from types import NoneType

from flask import Flask
from flask_caching import Cache

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np

import app_function as af

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


# ------------------------------------------------- Initialize Dash App ------------------------------------------------

# Create a Flask server
server = Flask(__name__)

# Initialise Dash app with Bootstrap CSS and suppress callback exceptions
app = dash.Dash(__name__,
                title="HealthScope Info",
                update_title="Loading...",
                server=server,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

# Initialise list to store selected countries {"alpha3": selected_alpha3, "name": selected_country_name}
selected_countries_list = []
selected_geojson_data = {}

# Initialise delfault year selected
selected_year = [2008,2020]

# Initial default title page
title_page = "Health Status Indicators"

cache = Cache(server, config={"CACHE_TYPE": "simple"})
cache.init_app(server)

# ----------------------------------------------------------------------------------------------------------------------





# --------------------------------------------------- Design of the App ------------------------------------------------

# Class of the buttons using Bootstrap
classButton = "btn btn-primary btn-sm mx-1"

# ----------------------------------------------------------------------------------------------------------------------





# --------------------------------------------------- Initialize Data --------------------------------------------------

# Load country data from JSON file of countries
file_path = "countries.json"
with open(file_path, "r") as file:
    country_data = json.load(file)


@cache.memoize(timeout=86400)  # Cache for 1 day
def get_geo_df():
    file_path = "filtered_world.geojson"
    with open(file_path, "r") as file:
        geojson_data = json.load(file)

    geo_countries = [{"CODE": feature["properties"]["CODE"], "NAME": feature["properties"]["NAME"]}
                     for feature in geojson_data["features"]]
    return geojson_data, pd.DataFrame(geo_countries)

geojson_data, geo_df = get_geo_df()  # Load once, then reuse

# ----------------------------------------------------------------------------------------------------------------------





# --------------------------------------------------- App Layout -------------------------------------------------------
app.layout = html.Div([

    # =============================================== Top Navigation Bar ===============================================
    html.Div([
        html.Div([

            # Project Logo
            html.Img(src="/assets/logo.png", style={'height': '5vh', 'paddingRight': '1vw'}),
            # University Logo
            html.Img(src="/assets/lille.png", style={'height': '4vh', 'paddingLeft': '1vw', 'paddingRight': '5vw'}),

            # ****************************** Navigation Buttons ******************************
            html.Div([
                html.Button("Health Status", id="health-btn", n_clicks=0, className=classButton),
                html.Button("Risk Factors", id="risk-btn", n_clicks=0, className=classButton),
                html.Button("Service Coverage", id="service-btn", n_clicks=0, className=classButton),
                html.Button("Health Systems", id="healthsys-btn", n_clicks=0, className=classButton),
            ], style={'paddingRight': '5vw','width': '50%'}),
            # ********************************************************************************


            # ******************************* Date Picker ************************************
            html.Div([
                # Dynamic Date Text using the callback function update_date()
                dcc.Store(id='date-store',data=selected_year),
                html.H3(id="date-display", style={'fontSize': '1.25rem', 'fontWeight': 'bold'}),

                # Date Slider
                html.Div([
                    dcc.RangeSlider(min=2000,max=2025,step=1,
                        marks={2000: '2000', 2025: '2025'},
                        value=selected_year,
                        tooltip={"placement": "bottom", "always_visible": True},
                        id="date-slider",
                    )
                ], style={'padding': '3px', 'flex': '1'})

            ], style={'display': 'flex', 'flexDirection': 'row','width': '20%'}),

            # Alert for maximum countries using the callback function update_page_and_countries()
            html.Div(id="maximum-alert", style={'padding': '10px'}),
            # ********************************************************************************


            # ******************************** Country Picker ********************************
            html.Div([
                # Dropdown Menu for selecting countries using the callback function update_page_and_countries()
                html.Div([
                    dbc.DropdownMenu(
                        label="Select Countries",
                        # Generate the country menu using the function generate_country_menu() in app_function.py
                        children= af.generate_country_menu(country_data),
                        direction="down",
                        toggle_style={"width": "200px"},
                        id="country-dropdown"
                    ),
                ], style={'padding': '5px', 'flex': '1', 'marginRight': 'auto'}),

                # Button to remove selected countries using the callback function update_page_and_countries()
                html.Button("Remove Selected Countries",
                            id="remove-countries-btn",
                            n_clicks=0,
                            className="btn btn-danger btn-sm mx-1"),
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '20%'}),
            # ********************************************************************************


        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '10px', 'backgroundColor': '#f4f4f4', 'width': '100%'})
    ], style={'display': 'flex', 'flexDirection': 'row'}),
    # ==================================================================================================================


    # ----------------------------------------------- Section Dashboard ------------------------------------------------

    html.Div(id="page-content", style={'padding': '20px'}),

    html.Div([
        dcc.Loading(
            id="loading-indicator2",
            type="default", # choose from 'circle', 'dot', 'default'
            children=html.Div(id="status-page")
        ),
        dcc.Store(id='intermediate-value'),
    ])

])
# ----------------------------------------------------------------------------------------------------------------------






@app.callback(
    Output("date-display", "children"),
    Output("date-store", "data"),
    Input("date-slider", "value")
)
def update_date(new_selected_year):
    """
    Update the displayed date based on the selected year from the slider.

    This callback function updates the displayed date based on the selected year from the slider.
        - Output: id= **date-display** Updates the `date-display` element with the selected year as a string.
        - Input: id = **date-slider** Receives the selected year from the `date-slider`.

    :param new_selected_year: The year selected from the date slider.
    :type new_selected_year: list[int,int]

    :return: The selected year as a string.
    :rtype: str
    """
    global selected_year

    selected_year = new_selected_year

    return f"{selected_year[0]} - {selected_year[1]}", selected_year


@app.callback(
    Output("page-content", "children"),
        Output("maximum-alert", "children"),
        Output("status-page", "children"),
        Output("intermediate-value", "data"),
    [
        Input("health-btn", "n_clicks"),
        Input("risk-btn", "n_clicks"),
        Input("service-btn", "n_clicks"),
        Input("healthsys-btn", "n_clicks"),
        Input("remove-countries-btn", "n_clicks"),
        Input("date-store", "data")
    ] + [
        Input(country["alpha3"], "n_clicks")
        for region in country_data["regions"]
        for subregion in country_data["regions"][region]
        for country in country_data["regions"][region][subregion]
        if isinstance(country, dict)
    ]
    )
def update_page_and_countries(*args):
    """
    Update the page content and selected countries based on user interactions.

    This callback function updates the page content and selected countries based on various user interactions, such as button clicks and country selections.
        - Output: id= **page-content** Updates the `page-content` element with the current title and selected countries.
        - Output: id= **maximum-alert** Displays an alert if the maximum number of countries is selected.
        - Output: id= **status-page** Updates the `status-page` element with the current status page content.
        - Input: id = **health-btn**, **risk-btn**, **service-btn**, **healthsys-btn**, **remove-countries-btn** Handles button clicks for different indicators and removing selected countries.
        - Input: id = **country-dropdown** Handles country selections from the dropdown menu.

    :param args: The arguments passed from the callback inputs.
    :type args: list
    :return: The updated page content, alert message, and status page content.
    :rtype: tuple
    """

    # Get the trigger source = the button or country selected
    ctx = dash.callback_context

    # Get the global variables
    global title_page
    global selected_countries_list

    if not isinstance(selected_countries_list, list):
        selected_countries_list = []

    # Initialize alert message to an empty string
    alert = ""

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If a trigger source is detected
    if triggered_id != "date-store":

        # Check the trigger source
        match triggered_id:
            case "health-btn": # If the trigger source is the Health Status button
                title_page = "Health Status Indicators"
            case "risk-btn": # If the trigger source is the Risk Factors button
                title_page = "Risk Factors Indicators"
            case "service-btn": # If the trigger source is the Service Coverage button
                title_page = "Service Coverage Indicators"
            case "healthsys-btn": # If the trigger source is the Health Systems button
                title_page = "Health Systems"
            case "remove-countries-btn": # If the trigger source is the Remove Selected Countries button
                # Clear selected countries
                selected_countries_list.clear()
                return (
                    html.H4(f"{title_page} : No countries selected"),
                    alert,
                    display_status_page(),
                    selected_countries_list
                    )
            case _: # If the trigger source is something else (so a country selection)

                # Get the alpha3 code : The selected country id is his alpha3 code (ex: Algeria clicked = DZA)
                selected_alpha3 = triggered_id

                # Check if the selected country is already in the list
                if selected_alpha3 not in [c["alpha3"] for c in selected_countries_list]:

                    # Check if the maximum number of countries is selected
                    if len(selected_countries_list) >= 4:
                        # If the maximum number of countries is selected, display an alert message
                        alert = dbc.Alert(
                            [
                                html.I(className="bi bi-exclamation-triangle-fill me-2"),  # Bootstrap warning icon
                                "Maximum of 4 countries can be selected"
                            ],
                            color="warning",
                            dismissable=True,
                            duration=4000
                        )
                        # Return the current title and selected countries with the alert message displayed
                        return (
                            html.H4(f"{title_page} : {', '.join([c['name'] for c in selected_countries_list])}"),
                            alert,
                            display_status_page(),
                            selected_countries_list
                        )

                    else :
                        # Get the name of the selected country
                        selected_country_name = af.get_country_name_by_alpha3(selected_alpha3, country_data)

                        # Add the selected country to the list
                        selected_countries_list.append({"alpha3": selected_alpha3, "name": selected_country_name})

                # If the selected country is already in the list
                else:
                    # Remove country if already selected by filtering the list without the selected country
                    selected_countries_list[:] = [c for c in selected_countries_list if c["alpha3"] != selected_alpha3]

    # Generate country text
    if selected_countries_list == None or selected_countries_list == {NoneType}:
        countries = "No countries selected"
    else :
        countries = ", ".join([c["name"] for c in selected_countries_list])

    return (
        html.H4(f"{title_page} : {countries}"),
        alert,
        display_status_page(),
        selected_countries_list
    )


@app.callback(
    Output("world-map", "figure"),
    [
        Input("intermediate-value", "data")
    ],
)
def update_map(*args):
    """
    Update the world map based on the selected countries.

    This callback function updates the world map based on the selected countries stored in the global variable `selected_countries_list`.
        - Output: id= **world-map** Updates the `world-map` element with the updated world map.
        - Input: id = **intermediate-value** Receives the selected countries list from the global variable.

    :param args: The arguments passed from the callback inputs.
    :type args: list

    :return: The updated figure for the world map.
    :rtype: plotly.graph_objects.Figure
    """

    global selected_countries_list
    global selected_geojson_data

    fig = go.Figure()
    locations = []
    z = []
    colors = []
    hovertext = None
    colorscale = [[0, "lightgray"], [1, "lightgray"]]  # Default color scale

    if selected_countries_list:
        selected_df = pd.DataFrame(selected_countries_list)
        selected_df["alpha3"] = selected_df["alpha3"].str.upper()

        # Filter GeoJSON for selected countries
        selected_geojson_data = {
            "type": "FeatureCollection",
            "features": [
                feature
                for feature in geojson_data["features"]
                if feature["properties"]["CODE"] in selected_df["alpha3"].values
            ]
        }

        # Update geo_df for selection status
        geo_df["selected"] = np.where(geo_df["CODE"].isin(selected_df["alpha3"]), 1, 0)

        color_palette = px.colors.qualitative.Plotly
        num_colors = len(selected_countries_list)
        country_z_values = {selected_countries_list[i]["alpha3"]: i for i in range(num_colors)}

        map = selected_geojson_data
        locations = geo_df["CODE"]
        z = [country_z_values[code] if code in country_z_values else None for code in locations]
        hovertext = geo_df["NAME"]

        colorscale = [[i / max(1, num_colors - 1), color_palette[i % len(color_palette)]] for i in range(num_colors)]
        print(colorscale)
    else:
        map = geojson_data


        # Add the Choropleth layer to the map
    fig.add_trace(go.Choroplethmap(
        geojson=map,  # Use the filtered GeoJSON
        locations=locations,
        z=z,
        colorscale=colorscale,
        marker=dict(opacity=0.6, line=dict(color='red', width=2)),
        showscale=False,  # Hide the color scale
        featureidkey="properties.CODE",
        hovertext=hovertext,
        hoverinfo="text"
    ))


    # Update the layout for the map view to focus on the last selected country
    fig.update_layout(
        mapbox=dict(
            style="white-bg",  # This is a simple Plotly style, doesn't need access token
            zoom=3.5,  # Adjust zoom level to get a closer or farther view
            center=dict(lat=0, lon=0),  # Set dynamic center based on lat/lon
            accesstoken=None,
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}  # Remove margins
    )

    return fig



def display_status_page():
    """
    Display the status page based on the selected title.

    :return: The content of the status page based on the selected title.
    :rtype: dash.development.base_component.Component
    """

    global title_page
    global selected_countries_list

    match title_page:
        case "Health Status Indicators":
            return af.generate_health_status_page(selected_countries_list,selected_year)

        case "Risk Factors Indicators":
            return af.generate_factors_risk_status_page(selected_countries_list)

        case "Service Coverage Indicators":
            return af.generate_coverage_status_page(selected_countries_list)

        case "Health Systems":
            return af.generate_health_systems_page(selected_countries_list)

        case _:
            return None


##########################Health Status Page############################################










#######################################################################################

# Run the Dash app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.getenv("PORT")), debug=False)
    #app.run_server(debug=True)

