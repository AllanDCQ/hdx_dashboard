import os
import pandas as pd
import plotly.express as px
from sqlalchemy import select, create_engine, MetaData, Table
from dash import dcc, html


################################################### Health Systems Page ################################################
def generate_health_systems_page(selected_countries_list, selected_year):

    map = html.Div([
        dcc.Graph(
            id="world-map",
            config={'scrollZoom': True, 'displayModeBar': True},
            selectedData=None,  # We use this property to capture selected country data
            style={"width": "100%"}
        )
    ], className="responsive-items_systems")

    uhc_graph = update_health_systems_graph_uhc(selected_countries_list, selected_year)

    birth_graph = update_health_systems_graph_birth(selected_countries_list, selected_year)
    death_graph = update_health_systems_graph_death(selected_countries_list, selected_year)


    row_1 = html.Div([
        map,
        dcc.Graph(id='update_health_systems_graph_uhc', figure=uhc_graph, className="responsive-items_systems")
    ], className="responsive-row-1_systems")

    row_2 = html.Div([
        dcc.Graph(id = 'update_health_systems_graph', figure=birth_graph),
        dcc.Graph(id='update_health_systems_graph_death', figure=death_graph)
    ], className="responsive-row-2_systems")


    layout = html.Div([
        row_1,
        row_2,
    ], className="responsive-container_systems")

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

    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection :
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query= select(indicator_table).where(
            indicator_table.columns.id_indicator == "SH.UHC.SRVS.CV.XD",
            indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1])
        )

        result = connection.execute(query).fetchall()
        df_uhc = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])

    return df_uhc


def get_health_systems_data_uhc2(selected_countries_list, selected_year) :

    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    with engine.connect() as connection :
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query= select(indicator_table).where(
            indicator_table.columns.id_indicator == "SH.UHC.SRVS.CV.XD",
            indicator_table.columns.id_country.in_([c["alpha3"].lower() for c in selected_countries_list]),
            indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1])
        )

        result = connection.execute(query).fetchall()
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
        )
        fig.update_layout(
            xaxis_title="Years",
            yaxis_title="Completeness of birth registration",
            legend_title="Countries",
        )
    else :
        fig = {}

    return fig

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
        )
        fig.update_layout(
            xaxis_title="Years",
            yaxis_title="Completeness of death registration",
            legend_title="Countries",
        )
    else :
        fig = {}

    return fig


def update_health_systems_graph_uhc(selected_countries_list, selected_year) :
    if selected_countries_list :
        df_uhc = get_health_systems_data_uhc2(selected_countries_list, selected_year)

        df_uhc = df_uhc.dropna(subset=["year_recorded", "value", "id_country"])

        fig = px.line(
            data_frame = df_uhc,
            x = "year_recorded",
            y = "value",
            color = "id_country",
            title = f"Service coverage index from {selected_year[0]} to {selected_year[1]}",
            markers=True,
        )

        fig.update_layout(
            xaxis_title="Years",
            yaxis_title="Service coverage index",
            legend_title="Countries",
        )

    else :
        fig = {}

    return fig