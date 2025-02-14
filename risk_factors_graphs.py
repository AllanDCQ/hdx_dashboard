import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
from risk_factors_queries import get_risk_factors_data, INDICATORS_MAPPING, get_country_names

def generate_risk_factors_page(selected_year, country_codes):
    """
    Génère la page des facteurs de risque avec les graphiques, en conservant la carte
    """
    # Récupération des données filtrées par pays si spécifiés
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