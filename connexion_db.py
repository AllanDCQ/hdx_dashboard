import os
import webscraping
import json
import concurrent.futures


"""
CODE EXEMPLE POUR ACCEDER A LA BASE DE DONNEES

# import   
import os
import pandas as pd
from sqlalchemy import select, create_engine, MetaData, Table

os.environ["BASE_URL"] = "postgresql://******************"  !!!!!!!!!!!!!!! à ne pas push sur GitHub !!!!!!!!!!!!!!!!!!!

with engine.connect() as connection:
    metadata = MetaData()

    # Exemple Chargement de la table Indicator
    indicator_table = Table('Timed_Indicators', metadata, autoload_with=engine)

    # Exemple de requête
    query = select(indicator_table).where(
        indicator_table.columns.id_indicator == "MMR_100k",
        indicator_table.columns.id_country == "GEO"
    )
    result = connection.execute(query).fetchall() # ou fetchone() si on veut un seul résultat

    # create dataframe
    df = pd.DataFrame(result, columns=[col.name for col in indicator_table.columns])
    


"""




################################################## FONCTIONS LEO-PAUL ##################################################


def update_list_health_status(country_list):
    """
    Updates the health status for a list of countries by fetching data from WHO and World Bank.

    :param country_list: List of country IDs to update.
    :type country_list: list
    :return: None
    :rtype: None

    Examples usage:
        update_list_health_status(['fra', 'dza', 'gbr'])
        update_list_health_status(['fra'])
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []

        for country_id in country_list:
            futures.append(executor.submit(_fetch_who_data, country_id))
            futures.append(executor.submit(_fetch_world_bank_data, country_id))

        concurrent.futures.wait(futures)  # Attend la fin des mises à jour des pays

    _fetch_unicef_data(country_list)


# Fonction principale pour traiter tous les pays
def update_all_health_status():
    """
    Updates the health status for all countries by fetching data from various sources.

    :return: None
    :rtype: None
    """
    with open("countries.json", "r") as f:
        countries = json.load(f)

    country_list = [
        country_info["alpha3"].lower()
        for subregions in countries["regions"].values()
        for countries in subregions.values()
        for country_info in countries
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(update_list_health_status, country_list)

def _fetch_who_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """
    try:
        dataset = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="who-data",
            dataset_index=0
        )
        dataset.add_indicator_to_db(
            indicators=["WHOSIS_000001", "WHOSIS_000002"],
            column_name="GHO (CODE)",
            column_fullname="GHO (DISPLAY)",
            column_value="Numeric",
            column_date="ENDYEAR",
            column_sexe="DIMENSION (NAME)"
        )
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_id} (WHO Data): {e}")

def _fetch_world_bank_data(country_id):
    """
    Fetches World Bank data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """
    try:
        dataset2 = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="world-bank-health-indicators",
            dataset_index=0
        )
        dataset2.add_indicator_to_db(
            indicators=["SH.DYN.MORT", "SH.DYN.MORT.FE", "SH.DYN.MORT.MA", "SH.DYN.NMRT"],
            column_name="Indicator Code",
            column_fullname="Indicator Name",
            column_value="Value",
            column_date="Year"
        )
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_id} (World Bank Data): {e}")

def _fetch_unicef_data(country_list):
    """
    Fetches UNICEF data for a list of countries and updates the database.

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
    :return: None
    :rtype: None
    """
    try:
        dataset = webscraping.FetchPageSingle(
            source_dataset="unicef-mnch-mmr",
            dataset_index = 0)
        dataset.add_indicator_to_db(
            indicator="MMR_100k",
            id_countries=[country.upper() for country in country_list], # Upper case for the csv
            column_contry_id = "REF_AREA",
            column_name = "INDICATOR",
            column_fullname="Indicator",
            column_value = "OBS_VALUE",
            column_date = "TIME_PERIOD")
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec UNICEF Data: {e}")

########################################################################################################################
