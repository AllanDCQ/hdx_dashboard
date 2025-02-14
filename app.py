import json
import os

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
                server=server,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

# Initialise list to store selected countries {"alpha3": selected_alpha3, "name": selected_country_name}
selected_countries_list = []
selected_geojson_data = {}

# Initialise delfault year selected
selected_year = 2008

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
                html.H3(id="date-display", style={'fontSize': '1.25rem', 'fontWeight': 'bold'}),

                # Date Slider
                html.Div([
                    dcc.Slider(min=2000,max=2025,step=1,
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
    Input("date-slider", "value")
)
def update_date(new_selected_year):
    """
    Update the displayed date based on the selected year from the slider.

    This callback function updates the displayed date based on the selected year from the slider.
        - Output: id= **date-display** Updates the `date-display` element with the selected year as a string.
        - Input: id = **date-slider** Receives the selected year from the `date-slider`.

    :param new_selected_year: The year selected from the date slider.
    :type new_selected_year: int

    :return: The selected year as a string.
    :rtype: str
    """
    global selected_year

    selected_year = new_selected_year

    return f"{selected_year}"


@app.callback(
    Output("page-content", "children"),  # Update the title dynamically
        Output("maximum-alert", "children"),
        Output("status-page", "children"),
        Output("intermediate-value", "data"),
    [
        Input("health-btn", "n_clicks"),
        Input("risk-btn", "n_clicks"),
        Input("service-btn", "n_clicks"),
        Input("healthsys-btn", "n_clicks"),
        Input("remove-countries-btn", "n_clicks"),
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

    # Initialize alert message to an empty string
    alert = ""

    # If a trigger source is detected
    if ctx.triggered:
        # Get the ID of the trigger source
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

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
    countries = ", ".join([c["name"] for c in selected_countries_list]) if selected_countries_list else "No countries selected"

    # Bannière bleue pour la sélection des pays (j'ai fait uniquement pour ma partie)
    if title_page == "Service Coverage Indicators":
        return (
            html.Div(),  
            alert,
            display_status_page(),
            selected_countries_list
        )
    else:
        return (
            html.H4(f"{title_page} : {countries}") if countries else html.Div(),
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
    hovertext = None

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

        map = selected_geojson_data
        locations = geo_df["CODE"]
        z = geo_df["selected"]
        hovertext = geo_df["NAME"]
    else:
        map = geojson_data


        # Add the Choropleth layer to the map
    fig.add_trace(go.Choroplethmap(
        geojson=map,  # Use the filtered GeoJSON
        locations=locations,
        z=z,
        colorscale=["lightgray", "lightgray"],  # Light gray for non-selected, red for selected
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


#################################################### Coverage Status Page ################################################


#---------------------------------------------------- Graphique linéaire ---------------------------------------------------#


@app.callback(
    Output('indicator-graph-container', 'children'),
    [
        Input('data-category', 'value'),
        Input('specific-indicator', 'value'),
        Input('date-slider', 'value'),
        Input('intermediate-value', 'data')
    ]
)
def update_indicator(selected_category, indicator_code, selected_year, selected_countries_list):
    try:
        print("Catégorie :", selected_category)
        print("Code indicateur :", indicator_code)
        print("Année sélectionnée :", selected_year)
        print("Pays sélectionnés :", selected_countries_list)
        indicator_titles = {
            'HIV_0000000001': "Estimated number of people living with HIV",
            'MALARIA_EST_INCIDENCE': "Estimated malaria incidence (per 1000 population at risk)",
            'MDG_0000000020': "Incidence of tuberculosis (per 100 000 population per year)",
            'WHS3_57': "Rubella - number of reported cases",
            'WHS3_62': "Measles - number of reported cases",
            'WHS3_41': "Diphtheria - number of reported cases"
        }
        indicator_title = indicator_titles.get(indicator_code, "Indicator")
        return af.update_indicator_graph(selected_countries_list, selected_year, indicator_code, indicator_title)
    except Exception as e:
        print("Erreur dans uptade_indicator :", e)
        # Retourner un message d'erreur dans l'interface si besoin :
        return html.Div("An error occurred when updating the graph.")

@app.callback(
    [Output('specific-indicator', 'options'),
     Output('specific-indicator', 'value')],
    Input('data-category', 'value')
)
def update_indicator_options(selected_category):
    if selected_category == 'disease':
        options = [
            {'label': 'HIV', 'value': 'HIV_0000000001'},
            {'label': 'Malaria', 'value': 'MALARIA_EST_INCIDENCE'},
            {'label': 'Tuberculosis', 'value': 'MDG_0000000020'}
        ]
        default_value = 'HIV_0000000001'
    elif selected_category == 'vaccine':
        options = [
            {'label': 'Rubella', 'value': 'WHS3_57'},
            {'label': 'Measles', 'value': 'WHS3_62'},
            {'label': 'Diphteria', 'value': 'WHS3_41'}
        ]
        default_value = 'WHS3_57'
    else:
        options = []
        default_value = None
    return options, default_value


#---------------------------------------------------- Bannière ---------------------------------------------------#


# Met à jour dynamiquement la bannière, en affichant la liste des pays sélectionnés
@app.callback(
    Output("title-banner", "children"),  
    Input("intermediate-value", "data")  # Récupère la liste des pays sélectionnés
)
def update_banner_text(selected_countries):
    print("📌 Mise à jour bannière - Pays sélectionnés :", selected_countries)
    if selected_countries:
        countries_text = ", ".join([c["name"] for c in selected_countries])  # Liste des pays sélectionnés
        return f"🩺 SERVICE COVERAGE INDICATORS : {countries_text}"  # Affiche les pays sélectionnés
    return "🩺 SERVICE COVERAGE INDICATORS : No countries selected"  # Aucun pays sélectionné


#---------------------------------------------------- Diagramme en barres horizontales ---------------------------------------------------#


@app.callback(
    Output('top5-bar-chart-container', 'children'),
    [
        Input('data-category', 'value'),
        Input('specific-indicator', 'value'),
        Input('date-slider', 'value'),
    ]
)
def update_top5_bar_chart(selected_category, indicator_code, selected_year):
    print("Dans update_top5_bar_chart:")
    print(" - Catégorie :", selected_category)
    print(" - Code indicateur :", indicator_code)
    print(" - Année :", selected_year)

    # Extraire la liste de tous les pays à partir de country_data
    all_countries = []
    for region in country_data["regions"]:
        for subregion in country_data["regions"][region]:
            for country in country_data["regions"][region][subregion]:
                if isinstance(country, dict):
                    all_countries.append(country)
    print("Tous les pays :", [c["name"] for c in all_countries])
    
    if indicator_code is not None:
        # Récupérer les données pour TOUS les pays
        df = af.get_indicator_data(all_countries, selected_year, indicator_code)
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible",
                               xref="paper", yref="paper", showarrow=False)
        else:
            # Filtrer pour l'année sélectionnée
            df_year = df[df["year_recorded"] == selected_year]
            if df_year.empty:
                fig = go.Figure()
                fig.add_annotation(text="Aucune donnée pour l'année sélectionnée",
                                   xref="paper", yref="paper", showarrow=False)
            else:
                # Trier par valeur décroissante et prendre les 5 premiers
                df_top5 = df_year.sort_values(by="value", ascending=False).head(5)
    
            # Trier par valeur décroissante et prendre les 5 premiers
            df_top5 = df_year.sort_values(by="value", ascending=False).head(5)
            # Construction du titre personnalisé 
            if indicator_code == 'HIV_0000000001':
                title_text = f"Top 5 countries with the highest estimated number of people <br>(all ages combined) living with HIV <br> from 2000 to {selected_year} overall"
            elif indicator_code == 'MALARIA_EST_INCIDENCE':
                title_text = f"Top 5 countries with the highest estimated incidence of malaria <br>(per 1000 people at risk) <br> from 2000 to {selected_year} overall"
            elif indicator_code == 'MDG_0000000020':
                title_text = f"Top 5 countries with the highest incidence of tuberculosis <br>(per 100,000 inhabitants per year) <br> from 2000 to {selected_year} overall"
            elif indicator_code == 'WHS3_62':
                title_text = f"Top 5 countries with the highest number <br>of reported cases of measles from 2000 to {selected_year} overall"
            elif indicator_code == 'WHS3_41':
                title_text = f"Top 5 countries with the highest number <br>of reported cases of diphteria from 2000 to {selected_year} overall"
            elif indicator_code == 'WHS3_57':
                title_text = f"Top 5 countries with the highest number <br>of reported cases of rubella from 2000 to {selected_year} overall"
            elif selected_category == 'disease':
                title_text = f"Top 5 countries most affected by the {indicator_code}"
            elif selected_category == 'vaccine':
                title_text = f"Top 5 countries with the most {indicator_code}"
            else:
                title_text = "Top 5 countries"

            fig = px.bar(
                df_top5,
                x="value",
                y="id_country",
                orientation="h",
                title=title_text,
                labels={"value": "Value", "id_country": "Countries"}
            )
            fig.update_layout(title_x=0.5)

        return dcc.Graph(
            figure=fig,
            config={'displayModeBar': False},
            style={'width': '100%', 'height': '600'}
    )
    else:
        return html.Div("Sélectionnez un indicateur")


#---------------------------------------------------- Diagramme en barres verticales ---------------------------------------------------#


@app.callback(
    Output('selected-country-average-container', 'children'),
    [
         Input('data-category', 'value'),
         Input('specific-indicator', 'value'),
         Input('date-slider', 'value'),
         Input('intermediate-value', 'data')
    ]
)
def update_country_average(selected_category, indicator_code, selected_year, selected_countries_list):
    print("Dans update_country_average:")
    print(" - Indicateur :", indicator_code)
    print(" - Année :", selected_year)
    print(" - Pays sélectionnés :", selected_countries_list)
    
    # Si aucun pays n'est sélectionné, afficher un message
    if not selected_countries_list:
         return html.Div("Aucun pays sélectionné", style={'textAlign': 'center'})
    
    # Pour chaque pays sélectionné, récupérer les données pour l'année sélectionnée
    averages = []
    for country in selected_countries_list:
         # On appelle get_indicator_data pour un seul pays dans une liste
         df = af.get_indicator_data([country], selected_year, indicator_code)
         # Filtrer les données pour l'année exacte
         df_year = df[df["year_recorded"] == selected_year]
         if not df_year.empty:
             avg_value = df_year["value"].mean()
         else:
             avg_value = None
         averages.append((country["name"], avg_value))
    
    # Créer un DataFrame à partir des moyennes
    df_avg = pd.DataFrame(averages, columns=["Country", "Average"])
    df_avg = df_avg[df_avg["Average"].notna()]
    
    if df_avg.empty:
         fig = go.Figure()
         fig.add_annotation(text="Aucune donnée pour les pays sélectionnés", 
                            xref="paper", yref="paper", showarrow=False)
    else:
         # Créer un diagramme en barres verticales
         fig = px.bar(df_avg, x="Country", y="Average", 
                      title=f"Average per country ({selected_year})",
                      labels={"Average": "Average value"})
         fig.update_layout(title_x=0.5)
    
    return dcc.Graph(
         figure=fig,
         config={'displayModeBar': False},
         style={'width':'80%', 'height':'600'}
    )   

#---------------------------------------------------- Graphique moyenne mondiale ---------------------------------------------------#


@app.callback(
    Output('global-average-container', 'children'),
    [
        Input('data-category', 'value'),
        Input('specific-indicator', 'value'),
        Input('date-slider', 'value')
    ]
)
def update_global_average(selected_category, indicator_code, selected_year):
    print("Dans update_global_average:")
    print(" - Catégorie :", selected_category)
    print(" - Indicateur :", indicator_code)
    print(" - Année :", selected_year)

    # Construire la liste de tous les pays à partir de country_data
    all_countries = []
    for region in country_data["regions"]:
        for subregion in country_data["regions"][region]:
            for country in country_data["regions"][region][subregion]:
                if isinstance(country, dict):
                    all_countries.append(country)
    print("Total number of countries :", len(all_countries))

    # Vérifier qu'un indicateur est sélectionné
    if indicator_code is not None:
        df = af.get_indicator_data(all_countries, selected_year, indicator_code)
        # Filtrer pour l'année sélectionnée
        df_year = df[df["year_recorded"] == selected_year]
        if df_year.empty:
            return html.Div("No data for the year selected", style={'textAlign': 'center'})
        else:
            # Calculer la moyenne
            global_avg = df_year["value"].mean()
            indicator_descriptions = {
                'HIV_0000000001': "Estimated number of people (all ages) <br>living with HIV",
                'MALARIA_EST_INCIDENCE': "Estimated malaria incidence <br>(per 1000 population at risk)",
                'MDG_0000000020': "Incidence of tuberculosis <br>(per 100 000 population per year)",
                'WHS3_57': "Rubella - number of reported cases",
                'WHS3_62': "Measles - number of reported cases",
                'WHS3_41': "Diphteria - number of reported cases"
            }
            desc = indicator_descriptions.get(indicator_code, "")
            # Afficher le titre, le chiffre et la description 
            fig = go.Figure(go.Indicator(
                mode="number",
                value=global_avg,
                title={
                    "text": f"World average ({selected_year})<br><span style='font-size:16px;color:gray; white-space: normal;'>{desc}</span>"
                }
            ))
            fig.update_layout(font=dict(size=24), margin={"l": 20, "r": 20, "t": 40, "b": 20})
            return dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                style={'width': '100%', 'height': '600px'}
            )
    else:
        return html.Div("Select an indicator", style={'textAlign': 'center'})


########################################################################################################################


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
            return af.generate_health_status_page(selected_countries_list)
        case "Risk Factors Indicators":
            return af.generate_factors_risk_status_page(selected_countries_list)

        case "Service Coverage Indicators":
            return af.generate_coverage_status_page(selected_countries_list, selected_year)

        case "Health Systems":
            return af.generate_health_systems_page(selected_countries_list)

        case _:
            return None


##########################Health Status Page############################################










#######################################################################################

port = int(os.environ.get("PORT", 8080))
# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)

