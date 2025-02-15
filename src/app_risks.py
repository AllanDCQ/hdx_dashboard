import os
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, MetaData, select, and_
from dash import dcc, html

INDICATORS_MAPPING = {
    "NT_ANT_WHZ_PO2": "Weight-for-height >+2 SD (overweight)",
    "NT_BW_LBW": "Prevalence of low birth weight among <br> new-borns",
    "WS_PPL_W-PRE": "Proportion of population using safely managed <br> drinking water services",
    "WS_PPL_W-B": "Proportion of population using basic <br> drinking water services"
}

def generate_factors_risk_status_page(selected_countries_list, selected_year):
    """
    Generate the risk status page for the selected countries and year.
    """
    # Get data only if countries are selected
    if selected_countries_list:
        country_codes = [c["alpha3"].lower() for c in selected_countries_list]
        df = get_risk_factors_data(country_codes, selected_year)
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        if not df.empty:
            df['country_name'] = df['id_country'].map(country_mapping)
    else:
        df = pd.DataFrame()

    # Create figures (empty if no data)
    # 1. Weight-for-height
    fig1 = {}
    if not df.empty:
        weight_height_df = df[df['id_indicator'] == 'NT_ANT_WHZ_PO2'].sort_values(by=['year_recorded'])
        fig1 = px.line(
            weight_height_df,
            x='year_recorded',
            y='value',
            color='country_name',
            title=INDICATORS_MAPPING['NT_ANT_WHZ_PO2'],
            markers=True,
            line_shape='linear'
        )
        fig1.update_layout(
            title={
                'text': INDICATORS_MAPPING['NT_ANT_WHZ_PO2'],
                'yanchor': 'top',
                'y': 0.95,
                'xanchor': 'center',
                'x': 0.5,
                'pad': {'t': 20}
            },
            margin=dict(t=80),
            xaxis_title='Year',
            yaxis_title='Value',
            legend_title='Country',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

    # 2. Low birth weight
    fig_lbw = {}
    if not df.empty:
        lbw_df = df[df['id_indicator'] == 'NT_BW_LBW']
        fig_lbw = px.bar(
            lbw_df,
            x='year_recorded',
            y='value',
            color='country_name',
            barmode='group',
            title=INDICATORS_MAPPING['NT_BW_LBW']
        )
        fig_lbw.update_layout(
            title={
                'text': INDICATORS_MAPPING['NT_BW_LBW'],
                'yanchor': 'top',
                'y': 0.95,
                'xanchor': 'center',
                'x': 0.5,
                'pad': {'t': 20}
            },
            margin=dict(t=80),
            xaxis_title='Year',
            yaxis_title='Proportion (%)',
            legend_title='Country',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            bargap=0.15,
            bargroupgap=0.1
        )

    # 3. Water services (safely managed)
    fig_wpre = {}
    if not df.empty:
        wpre_df = df[df['id_indicator'] == 'WS_PPL_W-PRE']
        fig_wpre = px.scatter(
            wpre_df,
            x='year_recorded',
            y='value',
            size='value',
            color='country_name',
            title=INDICATORS_MAPPING['WS_PPL_W-PRE']
        )
        fig_wpre.update_layout(
            title={
                'text': INDICATORS_MAPPING['WS_PPL_W-PRE'],
                'yanchor': 'top',
                'y': 0.95,
                'xanchor': 'center',
                'x': 0.5,
                'pad': {'t': 20}
            },
            margin=dict(t=80),
            xaxis_title='Year',
            yaxis_title='Proportion (%)',
            legend_title='Country',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

    # 4. Water services (basic)
    fig_wb = {}
    if not df.empty:
        wb_df = df[df['id_indicator'] == 'WS_PPL_W-B']
        fig_wb = px.histogram(
            wb_df,
            x='year_recorded',
            y='value',
            color='country_name',
            barmode='group',
            title=INDICATORS_MAPPING['WS_PPL_W-B'],
            category_orders={"year_recorded": sorted(wb_df['year_recorded'].unique())}
        )
        fig_wb.update_layout(
            title={
                'text': INDICATORS_MAPPING['WS_PPL_W-B'],
                'yanchor': 'top',
                'y': 0.95,
                'xanchor': 'center',
                'x': 0.5,
                'pad': {'t': 20}
            },
            margin=dict(t=80),
            xaxis_title='Year',
            yaxis_title='Proportion (%)',
            legend_title='Country',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            bargap=0.15,
            bargroupgap=0.1
        )

    # Map component (always show empty map if no countries selected)
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
    ], className="responsive-map_risk")

    # Layout construction with separated graphs
    row_1 = html.Div([
        map_div,
        dcc.Graph(figure=fig1, className="responsive-column_risk-1"),
    ], className="responsive-row_risk")

    row_2 = html.Div([
        html.Div([
            dcc.Graph(figure=fig_wpre)
        ], className="responsive-column_risk-2"),
        html.Div([
            dcc.Graph(figure=fig_lbw)
        ], className="responsive-column_risk-2"),
        html.Div([
            dcc.Graph(figure=fig_wb)
        ], className="responsive-column_risk-2"),
    ], className="responsive-row_risk")

    layout = html.Div([
        row_1,
        row_2,
    ])

    return layout

def get_risk_factors_data(country_codes, selected_year):
    """
    Fetches risk factors data from the database.
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    metadata = MetaData()
    metadata.reflect(bind=engine)

    try:
        timed_indicators = metadata.tables['Timed_Indicators']
    except KeyError:
        print("La table 'Timed_Indicators' n'a pas été trouvée dans la base de données.")
        return pd.DataFrame()

    # Construction du filtre avec les pays en minuscules
    indicator_filter = timed_indicators.c.id_indicator.in_(INDICATORS_MAPPING.keys())
    country_filter = timed_indicators.c.id_country.in_(country_codes)
    year_filter = timed_indicators.c.year_recorded.between(selected_year[0], selected_year[1])
    final_filter = and_(country_filter, indicator_filter, year_filter)

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