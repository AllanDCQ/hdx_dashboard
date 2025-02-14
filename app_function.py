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


def generate_health_status_page(selected_countries_list):

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

#################################################### Coverage Status Page ################################################

def generate_coverage_status_page(selected_countries_list, selected_year):
    store_selected_countries = dcc.Store(id="selected-countries-store")

    # Section de sélection de catégorie et d'indicateur
    selection_controls = html.Div([
        dcc.RadioItems(
            id='data-category',
            options=[
                {'label': 'Diseases', 'value': 'disease'},
                {'label': 'Vaccination coverage', 'value': 'vaccine'}
            ],
            value='disease',
            labelStyle={'display': 'inline-block', 'marginRight': '20px'}
        ),
        dcc.Dropdown(
            id='specific-indicator',
            # Définit les options pour la catégorie "Diseases"
            options=[
                {'label': 'HIV', 'value': 'HIV_0000000001'},
                {'label': 'Malaria', 'value': 'MALARIA_EST_INCIDENCE'},          
                {'label': 'Tuberculosis', 'value': 'MDG_0000000020'}
            ],
            value=None,
            placeholder="Select...",  # Texte affiché par défaut
            clearable=False,
            style={'width': '300px', 'marginLeft': '20px'}
        )
    ], style={'display': 'flex', 'alignItems': 'center', 'padding': '10px'})

    # Div pour la carte
    map = html.Div([
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
    ], style={'width': '60%', 'height': '40vh', 'padding': '5px'})

    # Conteneur pour le graphique linéaire (mise à jour via callback)
    linear_graph_container = html.Div(
        id='indicator-graph-container',
        style={'width': '40%', 'height': '80vh', 'padding': '10px', 'alignSelf': 'flex-start'}
    )

    # Première rangée : carte et graphique linéaire côte à côte
    top_row = html.Div(
        [map, linear_graph_container],
        style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'alignItems': 'flex-start'}
    )

    # Conteneur pour le diagramme Top 5 
    top5_chart_container = html.Div(
        id='top5-bar-chart-container',
        style={
            'width': '50%', 
            'height': '60vh',
            'padding': '5px', 
            'marginTop': '0px'
        }
    )
    
    # Conteneur pour le diagramme vertical
    selected_country_average_container = html.Div(
        id="selected-country-average-container",
        style={
            'width': '50%', 
            'height': '60vh', 
            'padding': '5px', 
            'textAlign': 'center', 
            'lineHeight': '30vh',
            'marginTop': '0px'
        }
    )

    # Conteneur pour le diagramme horizontal
    global_average_container = html.Div(
        id="global-average-container",
        style={
            'width': '33.33%', 
            'height': '30vh', 
            'padding': '10px', 
            'textAlign': 'center', 
            'lineHeight': '30vh'
        }
    )
    
    # Deuxième rangée : les trois diagrammes côte à côte
    bottom_row = html.Div(
        [top5_chart_container, selected_country_average_container, global_average_container],
        style={'display': 'flex', 'flexDirection': 'row', 'width': '100%','marginTop': '0px'}
    )

    # Zone réservée au graphique de l'indicateur (sera mis à jour par un callback)
    graph = html.Div(
        id='indicator-graph-container', 
        style={
            'width': '40%', 
            'height': '10vh', 
            'padding': '10px', 
            'flexDirection': 'row',
            'alignSelf': 'flex-start',
            'margin-top': '-70px'  # Déplacer le graphique vers le haut
        })
    
    # Organisation en ligne : carte et graphique côte à côte
    row_1 = html.Div([
        graph,
    ], style={
        'display': 'flex', 
        'flexDirection': 'row', 
        'padding': '5px', 
        'width': '100%',
        'align-items': 'flex-start'  
    })

    title_banner = html.Div(
        html.H2(
            id="title-banner",
            children="Service Coverage Indicators : No countries selected",
            style={
                'textAlign': 'center', 
                'color': 'white', 
                'fontSize': '28px', 
                'fontWeight': 'bold', 
                'textTransform': 'uppercase',
                'margin': '0px'
            }
        ),
        style={
            'backgroundColor': '#3498DB',
            'padding': '15px',
            'borderRadius': '10px',
            'textAlign': 'center',
            'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.2)',
            'marginBottom': '20px',
            'width': '100%'  # S'assure que la bande bleue couvre toute la largeur
        }
    )

    subtitle = html.P(
        "Explore health and vaccination coverage by country and indicator",
        style={
            'textAlign': 'center',
            'color': '#7F8C8D',
            'fontSize': '18px',
            'fontStyle': 'italic',
            'marginBottom': '30px'
        }
    )
    
    dcc.Store(id="selected-countries-store", data=selected_countries_list)

    return html.Div([
        store_selected_countries,
        title_banner,
        subtitle,
        selection_controls,
        top_row,
        bottom_row
    ])

def get_indicator_data(selected_countries_list, selected_year, indicator_code):

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    
    os.environ["BASE_URL"] = "postgresql://webscraping_db_user:35RuggWvxnsRNbARA2QmiBqOpo0rVo83@dpg-cughkud6l47c73be2j10-a.frankfurt-postgres.render.com:5432/webscraping_db" 

    database_url = os.getenv("BASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == indicator_code,
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(2000, selected_year)
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_indicator_graph(selected_countries_list, selected_year, indicator_code, indicator_title):
    if selected_countries_list:
        df = get_indicator_data(selected_countries_list, selected_year, indicator_code)
        if df.empty:
            # Cas où aucune donnée n'est renvoyée
            fig = go.Figure()
            fig.add_annotation(text="No data available",
                               xref="paper", yref="paper", showarrow=False)

        # Création du graphique avec Plotly
        else:
            fig = px.line(
                data_frame= df,
                x="year_recorded",  
                y="value",  
                color="id_country",  
                title=f"{indicator_title} in {selected_year}"
            )
    else:
        # Message si aucun pays n'est sélectionné
        fig = go.Figure()
        fig.add_annotation(text="Please select one or more countries",
                           xref="paper", yref="paper", showarrow=False)
    
    # Personnalisation du layout pour centrer le titre et autoriser le retour à la ligne
    fig.update_layout(
        title={
            'text': fig.layout.title.text,  
            'x': 0.5,
            'xanchor': 'center'
        },
        margin={"l": 40, "r": 20, "t": 60, "b": 40},
        hovermode="x unified",
        font=dict(size=12)
    )
    
    return dcc.Graph(
        id='coverage-status-graph', 
        figure=fig,
        config={'displayModeBar': False},  # Désactive la barre d'outils
        style={'width': '100%', 'height': '80vh'})

########################################################################################################################

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















