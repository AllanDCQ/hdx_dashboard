import os
import pandas as pd
import plotly.express as px
from sqlalchemy import select, create_engine, MetaData, Table, and_
from dash import dcc, html

from app_function import color_palette



#################################################### Health Status Page ################################################


def generate_health_status_page(selected_countries_list, selected_year):
    """
    Generate the health status page layout.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: The layout of the health status page.
    :rtype: dash.development.base_component.Component
    """

    graph4=update_SH_DYN_MORT_graph(selected_countries_list, selected_year)
    # Colonne de gauche contenant la carte
    column_1 = html.Div([
        dcc.Graph(
            id="world-map",
            config={'scrollZoom': True, 'displayModeBar': False},
            figure={},
            selectedData=None,
            style={'height': '40%', 'width': '100%'}
        ),
        graph4
    ], className="responsive-column_1")


    graph3=update_MMR100k_graph(selected_countries_list, selected_year)
    graph5=update_SH_DYN_MORT_neo_graph(selected_countries_list, selected_year)

    column_2 = html.Div(children=[graph3,graph5],
                        className="responsive-column_2")

    # Génération des graphiques
    graph1 = update_WHOSIS_000001_graph(selected_countries_list, selected_year)
    graph2 = update_WHOSIS_000002_graph(selected_countries_list, selected_year)

    # Colonne de droite contenant les graphiques
    column_3 = html.Div(children=[graph1,graph2,],
                        className="responsive-column_2")

    # Conteneur principal en ligne (deux colonnes)
    layout = html.Div([
        column_1,column_2,column_3]
        ,className="responsive-container")

    return layout


#---------------------------------------------------- MMR100k Graph ---------------------------------------------------#

def get_MMR100k_data(selected_countries_list, selected_year):
    """
    Retrieve the MMR100k data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the MMR100k data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "MMR_100k",
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

def update_MMR100k_graph(selected_countries_list, selected_year):
    """
    Update the MMR100k graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated MMR100k data.
    :rtype: dash.development.base_component.Component
    """
    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        df = get_MMR100k_data(selected_countries_list, selected_year)
        # Création du graphique avec Plotly
        fig = px.line(
            data_frame=df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les courbes par pays
            custom_data=["id_country"],
            color_discrete_sequence=px.colors.qualitative.G10,
        )

        fig.update_layout(
            title={
                'text': "<b>Maternal mortality ratio</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (per 100k live births)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',  # Centre le titre sur la zone de tracé
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<extra></extra>",
            mode="lines+markers",
            hovertext=None,
            showlegend=True,
        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='health-status-graph', figure=fig, style={'width': '100%', 'height': '40%%'})

#------------------------------------------------- WHOSIS_000001 Graph ------------------------------------------------#

def get_WHOSIS_000001_data(selected_countries_list, selected_year):
    """
    Retrieve the WHOSIS_000001 data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the WHOSIS_000001 data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "WHOSIS_000001",
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
                indicator_table.columns.sexe=="Both sexes"
            )
        )
        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_WHOSIS_000001_graph(selected_countries_list, selected_year):
    """
    Update the WHOSIS_000001 graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated WHOSIS_000001 data.
    :rtype: dash.development.base_component.Component
    """
    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        df = get_WHOSIS_000001_data(selected_countries_list, selected_year)
        # Création du graphique avec Plotly
        fig = px.line(
            data_frame=df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les courbes par pays
            custom_data=["id_country"],
            color_discrete_sequence=px.colors.qualitative.G10,
        )

        fig.update_layout(
            title={
                'text': "<b>Life expectancy at birth</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (years)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<extra></extra>",
            mode="lines+markers",
            showlegend=True,

        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='health-status-graph', figure=fig, style={'width': '100%', 'height': '40%%'})

#------------------------------------------------- WHOSIS_000002 Graph ------------------------------------------------#

def get_WHOSIS_000002_data(selected_countries_list, selected_year):
    """
    Retrieve the WHOSIS_000002 data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the WHOSIS_000002 data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator == "WHOSIS_000002",
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
                indicator_table.columns.sexe=="Both sexes"
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_WHOSIS_000002_graph(selected_countries_list, selected_year):
    """
    Update the WHOSIS_000002 graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated WHOSIS_000002 data.
    :rtype: dash.development.base_component.Component
    """

    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        df = get_WHOSIS_000002_data(selected_countries_list, selected_year)
        # Création du graphique avec Plotly
        fig = px.line(
            data_frame= df,
            x="year_recorded",  # Modifier selon ta colonne contenant les années
            y="value",  # Modifier selon ta colonne contenant les valeurs
            color_discrete_map=country_to_color,
            color="id_country",
            custom_data=["id_country"],
            color_discrete_sequence=px.colors.qualitative.G10,
        )
        fig.update_layout(
            title={
                'text': "<b>Healthy life expectancy at birth</b>",
                'y': 0.97,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (years)",
            legend_title="Country",
            margin={'t': 30},
            title_xref='paper'
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country:%{customdata[0]}<extra></extra>",
            mode="lines+markers",
            hovertext=None,
            showlegend=True,
        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='health-status-graph', figure=fig,style={'width': '100%', 'height': '40%%'})

#-------------------------------------------------- SH_DYN_MORT Graph -------------------------------------------------#

def get_SH_DYN_MORT_data(selected_countries_list, selected_year):
    """
    Retrieve the SH_DYN_MORT data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the SH_DYN_MORT data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator.in_(["SH.DYN.MORT", "SH.DYN.MORT.FE", "SH.DYN.MORT.MA"]),
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_SH_DYN_MORT_graph(selected_countries_list, selected_year):
    """
    Update the SH_DYN_MORT graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated SH_DYN_MORT data.
    :rtype: dash.development.base_component.Component
    """

    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        # Récupérer les données pour les filles et les garçons
        df = get_SH_DYN_MORT_data(selected_countries_list, selected_year)

        # Filtrer les données pour les filles et les garçons
        df_female = df[df['id_indicator'] == 'SH.DYN.MORT.FE']
        df_male = df[df['id_indicator'] == 'SH.DYN.MORT.MA']

        # Ajouter une colonne 'gender' pour indiquer si c'est pour les filles ou les garçons
        df_female = df_female.assign(gender='Female')
        df_male = df_male.assign(gender='Male')

        # Combiner les DataFrames des filles et des garçons
        df_combined = pd.concat([df_female, df_male])
        df_combined = df_combined.sort_values("id_country")

        # Création du graphique à barres avec Plotly
        fig = px.bar(
            data_frame=df_combined,
            x="year_recorded",  # Année sur l'axe des X
            y="value",  # Taux de mortalité sur l'axe des Y
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les barres par pays
            barmode="group",  # Afficher les barres côte à côte
            custom_data=["id_country", "gender"],
            facet_col=None,  # Pas de facettage, un seul graphique
            color_discrete_sequence=px.colors.qualitative.G10
        )

        fig.update_layout(
            title={
                'text': "<b>Mortality Rate under 5 years</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (per 1,000 live births)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',  # Centre le titre sur la zone de tracé
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<br>Gender: %{customdata[1]}<extra></extra>",
            hovertext=None,
            showlegend=True,
        )
        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )
    else:
        fig = {}

    return dcc.Graph(id='mortality-graph', figure=fig, style={'width': '100%', 'height': '40%%'})

#--------------------------------------------- SH_DYN_MORT_neonatal Graph ---------------------------------------------#

def get_SH_DYN_MORT_neo_data(selected_countries_list, selected_year):
    """
    Retrieve the SH_DYN_MORT_neo data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: DataFrame containing the SH_DYN_MORT_neo data.
    :rtype: pandas.DataFrame
    """

    country_codes = [c["alpha3"].lower() for c in selected_countries_list]
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as connection:
        metadata = MetaData()
        indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

        query = select(indicator_table).where(
            and_(
                indicator_table.columns.id_indicator.in_(['SH.DYN.NMRT']),
                indicator_table.columns.id_country.in_(country_codes),
                indicator_table.columns.year_recorded.between(selected_year[0], selected_year[1]),
            )
        )

        result = connection.execute(query).fetchall()
        df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
        country_mapping = {c["alpha3"].lower(): c["name"] for c in selected_countries_list}
        # Remplacement des codes alpha3 par les noms de pays dans le DataFrame
        df["id_country"] = df["id_country"].str.lower().map(country_mapping)

    return df

def update_SH_DYN_MORT_neo_graph(selected_countries_list, selected_year):
    """
    Update the SH_DYN_MORT_neo graph with the data for the selected countries and year.

    :param selected_countries_list: List of selected countries.
    :type selected_countries_list: list
    :param selected_year: The selected year for the data.
    :type selected_year: list[int]
    :return: A Dash Graph component with the updated SH_DYN_MORT_neo data.
    :rtype: dash.development.base_component.Component
    """
    country_to_color = {country["name"]: color_palette[i] for i, country in enumerate(selected_countries_list)}

    if selected_countries_list:
        # Récupérer les données de mortalité néonatale
        df = get_SH_DYN_MORT_neo_data(selected_countries_list, selected_year)

        # Filtrer les données pour la mortalité néonatale (identifiant 'SH.DYN.NMRT')
        df_neonatal = df[df['id_indicator'] == 'SH.DYN.NMRT']

        # Création du graphique en ligne avec Plotly
        fig = px.line(
            data_frame=df_neonatal,
            x="year_recorded",  # Année sur l'axe des X
            y="value",  # Taux de mortalité néonatale sur l'axe des Y
            color_discrete_map=country_to_color,
            color="id_country",  # Différencier les lignes par pays
            markers=True,  # Ajouter des marqueurs pour chaque point de donnée
            custom_data=["id_country"],  # Données supplémentaires pour le survol
            color_discrete_sequence=px.colors.qualitative.G10,
        )

        fig.update_layout(
            title={
                'text': "<b>Neonatal mortality rate</b>",
                'y': 0.95,  # Ajuste la hauteur du titre
                'x': 0.5,  # Centre le texte par rapport à la zone du graphique
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Years",
            yaxis_title="Value (per 1,000 live births)",
            legend_title="Country",
            margin={'t': 30},  # Augmente la marge supérieure pour éviter le chevauchement
            title_xref='paper',  # Centre le titre sur la zone de tracé
        )

        fig.update_traces(
            hoverinfo='skip',
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}<br>Country: %{customdata[0]}<extra></extra>",
            hovertext=None,
            showlegend=True,
        )

        fig.update_layout(
            hovermode="closest",  # Affiche l'infobulle uniquement pour la courbe la plus proche
            hoverlabel=dict(namelength=0),  # Empêche l'affichage du nom du pays à côté de l'infobulle
        )

    else:
        fig = {}

    return dcc.Graph(id='mortality-neo-graph', figure=fig, style={'width': '100%', 'height': '40%%'})


########################################################################################################################