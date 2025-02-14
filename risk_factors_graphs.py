import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
from risk_factors_queries import get_risk_factors_data, INDICATORS_MAPPING

def generate_risk_factors_page(selected_year, country_codes):
    """
    Génère la page des facteurs de risque avec les graphiques, en conservant la carte
    """
    # Récupération des données filtrées par pays si spécifiés
    df = get_risk_factors_data(country_codes) if country_codes else get_risk_factors_data()

    if df.empty:
        return html.Div("No data available for selected countries")
    
    # Création des graphiques
    # 1. Graphique en haut à droite - Line plot pour Weight-for-height
    weight_height_df = df[df['id_indicator'] == 'NT_ANT_WHZ_PO2']
    fig1 = px.line(weight_height_df, 
                   x='year_recorded', 
                   y='value',
                   color='id_country',
                   title=INDICATORS_MAPPING['NT_ANT_WHZ_PO2'])

    # 2-4. Les trois graphiques en bas
    figures_bottom = [
        px.bar(df[df['id_indicator'] == 'NT_BW_LBW'],
               x='id_country',
               y='value',
               color='year_recorded',
               title=INDICATORS_MAPPING['NT_BW_LBW']),
        
        px.scatter(df[df['id_indicator'] == 'WS_PPL_W-PRE'],
                  x='Year',
                  y='value',
                  size='value',
                  color='id_country',
                  title=INDICATORS_MAPPING['WS_PPL_W-PRE']),
        
        px.box(df[df['id_indicator'] == 'WS_PPL_W-B'],
               x='id_country',
               y='value',
               color='year_recorded',
               title=INDICATORS_MAPPING['WS_PPL_W-B'])
    ]

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
    ], style={'width': '50%', 'height': '40vh', 'marginRight': '20px'})

    # Layout complet
    return [
        # Première rangée avec la carte et le premier graphique
        html.Div([
            map_div,
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=fig1)
            )), width=6, style={'marginLeft': '20px'})
        ], style={'display': 'flex', 'flexDirection': 'row', 'marginBottom': '20px'}),
        
        # Deuxième rangée avec les trois graphiques
        html.Div([
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=fig)
            )), width=4, style={'marginLeft': '20px', 'marginRight': '20px'}) for fig in figures_bottom
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ]