import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sqlalchemy import select, create_engine, MetaData, Table, and_
from dash import dcc, html

from src.app_function import color_palette


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
    ], className="responsive-item-1_coverage")

    # Conteneur pour le graphique linéaire (mise à jour via callback)
    linear_graph_container = html.Div(
        id='indicator-graph-container',
        className="responsive-map_coverage"
    )

    # Première rangée : carte et graphique linéaire côte à côte
    top_row = html.Div(
        [map, linear_graph_container],
        className="responsive-row_coverage"
    )

    # Conteneur pour le diagramme Top 5
    top5_chart_container = html.Div(
        id='top5-bar-chart-container',
        className="responsive-item-2_coverage"
    )

    # Conteneur pour le diagramme vertical
    selected_country_average_container = html.Div(
        id="selected-country-average-container",
        className="responsive-item-2_coverage"
    )

    # Conteneur pour le diagramme horizontal
    global_average_container = html.Div(
        id="global-average-container",
        className="responsive-item-2_coverage"
    )

    # Deuxième rangée : les trois diagrammes côte à côte
    bottom_row = html.Div(
        [top5_chart_container, selected_country_average_container, global_average_container],
        className="responsive-row_coverage"
    )

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
            'marginBottom': '10px'
        }
    )

    dcc.Store(id="selected-countries-store", data=selected_countries_list)

    layout = html.Div([
        store_selected_countries,
        title_banner,
        subtitle,
        selection_controls,
        top_row,
        bottom_row
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})

    return layout

def get_indicator_data(selected_countries_list, selected_year, indicator_code):

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]

    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == indicator_code,
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
            country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}
            fig = px.line(
                data_frame= df,
                x="year_recorded",
                y="value",
                color="id_country",
                color_discrete_map=country_to_color,
                color_discrete_sequence=px.colors.qualitative.G10,
                title=f"{indicator_title} from {selected_year[0]} to {selected_year[1]}"
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
        config={'displayModeBar': False})

########################################################################################################################
