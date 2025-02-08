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




############################################### FONCTIONS HEALTH STATUS ################################################


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
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []

        for country_id in country_list:
            futures.append(executor.submit(_fetch_who_data, country_id))
            futures.append(executor.submit(_fetch_world_bank_data, country_id))

        concurrent.futures.wait(futures, timeout=30)  # Attend la fin des mises à jour des pays

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

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(update_list_health_status, country_list)

def _fetch_who_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """

    indicators = ["WHOSIS_000001", "WHOSIS_000002"]

    try:
        dataset = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="who-data",
            dataset_index=0
        )
        if dataset.datasets_list is None:
            raise ValueError(f"Error fetching data from WHO for {country_id} for {indicators}")
        else:
            dataset.add_indicator_to_db(
                indicators=indicators,
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
    indicators = ["SH.DYN.MORT", "SH.DYN.MORT.FE", "SH.DYN.MORT.MA", "SH.DYN.NMRT"]
    try:
        dataset2 = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="world-bank-health-indicators",
            dataset_index=0
        )
        if dataset2.datasets_list is None:
            raise ValueError(f"Error fetching data from World Bank for {country_id} for {indicators}")

        else:
            dataset2.add_indicator_to_db(
                indicators=indicators,
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
        print(f"Erreur avec {country_list} (UNICEF Data): {e}")


########################################################################################################################










############################################# FONCTIONS SERVICES COVERAGES #############################################

def update_list_services_coverages(country_list):
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []

        for country_id in country_list:
            futures.append(executor.submit(_fetch_hiv_data, country_id))
            futures.append(executor.submit(_fetch_tuberculosis_data, country_id))
            futures.append(executor.submit(_fetch_malaria_data, country_id))
            futures.append(executor.submit(_fetch_immunization_data, country_id))

        concurrent.futures.wait(futures, timeout=30)


def update_all_services_coverages():
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

    update_list_services_coverages(country_list)


def _fetch_hiv_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """
    indicators = ["HIV_0000000001"]
    try:
        dataset = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="who-data",
            dataset_name="HIV Indicators",
        )
        dataset.add_indicator_to_db(
            indicators=indicators,
            column_name="GHO (CODE)",
            column_fullname="GHO (DISPLAY)",
            column_value="Numeric",
            column_date="ENDYEAR",
            column_sexe="DIMENSION (NAME)"
        )
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_id} (WHO Data): {e}")

def _fetch_tuberculosis_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """
    indicators = ["MDG_0000000020"]
    try:
        dataset = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="who-data",
            dataset_name="Tuberculosis Indicators",
        )
        dataset.add_indicator_to_db(
            indicators=indicators,
            column_name="GHO (CODE)",
            column_fullname="GHO (DISPLAY)",
            column_value="Numeric",
            column_date="ENDYEAR",
            column_sexe="DIMENSION (NAME)"
        )
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_id} (WHO Data): {e}")

def _fetch_malaria_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """
    indicators = ["MALARIA_EST_INCIDENCE"]
    try:
        dataset = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="who-data",
            dataset_name="Malaria Indicators",
        )
        dataset.add_indicator_to_db(
            indicators=indicators,
            column_name="GHO (CODE)",
            column_fullname="GHO (DISPLAY)",
            column_value="Numeric",
            column_date="ENDYEAR",
            column_sexe="DIMENSION (NAME)"
        )
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_id} (WHO Data): {e}")

def _fetch_immunization_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """
    indicators = ["WHS3_62","WHS3_41","WHS3_57"]
    try:
        dataset = webscraping.FetchPage(
            country_id=country_id,
            source_dataset="who-data",
            dataset_name="Immunization coverage and vaccine-preventable diseases Indicators",
        )
        dataset.add_indicator_to_db(
            indicators=indicators,
            column_name="GHO (CODE)",
            column_fullname="GHO (DISPLAY)",
            column_value="Numeric",
            column_date="ENDYEAR",
            column_sexe="DIMENSION (NAME)"
        )
    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_id} (WHO Data): {e}")


########################################################################################################################










################################################ FONCTIONS RISK FACTORS ################################################

def update_list_risk_factors(country_list):
    """
    Updates the risk factors for a list of countries by fetching data from WHO and World Bank.

    :param country_list: List of country IDs to update.
    :type country_list: list
    :return: None
    :rtype: None

    Examples usage:
        update_list_risk_factors(['fra', 'dza', 'gbr'])
        update_list_risk_factors(['fra'])
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(_fetch_weight_data, country_list),
                   executor.submit(_fetch_drink_safe_data, country_list),
                   executor.submit(_fetch_drink_data, country_list),
                   executor.submit(_fetch_birth_data, country_list)]

        concurrent.futures.wait(futures, timeout=30)  # Attend la fin des mises à jour des pays

    return



def update_all_risk_factors():
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

    update_list_risk_factors(country_list)

    return


def _fetch_weight_data(country_list):
    """
    Fetches UNICEF data for a list of countries and updates the database.

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
    :return: None
    :rtype: None
    """
    try:
        dataset = webscraping.FetchPageSingle(
            source_dataset="unicef-nt-ant-whz-po2",
            dataset_index = 0)
        dataset.add_indicator_to_db(
            indicator="NT_ANT_WHZ_PO2",
            id_countries=[country.upper() for country in country_list], # Upper case for the csv
            column_contry_id = "REF_AREA",
            column_name = "INDICATOR",
            column_fullname="Indicator",
            column_value = "OBS_VALUE",
            column_date = "TIME_PERIOD")

    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_list} (UNICEF Data): {e}")

    return

def _fetch_drink_safe_data(country_list):
    """
    Fetches UNICEF data for a list of countries and updates the database.

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
    :return: None
    :rtype: None
    """
    try:
        dataset = webscraping.FetchPageSingle(
            source_dataset="unicef-ws-ppl-w-sm",
            dataset_index = 0)
        dataset.add_indicator_to_db(
            indicator="WS_PPL_W-PRE",
            id_countries=[country.upper() for country in country_list], # Upper case for the csv
            column_contry_id = "REF_AREA",
            column_name = "INDICATOR",
            column_fullname="Indicator",
            column_value = "OBS_VALUE",
            column_date = "TIME_PERIOD")

    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_list} (UNICEF Data): {e}")

    return

def _fetch_drink_data(country_list):
    """
    Fetches UNICEF data for a list of countries and updates the database.

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
    :return: None
    :rtype: None
    """
    try:
        dataset = webscraping.FetchPageSingle(
            source_dataset="unicef-ws-ppl-w-b",
            dataset_index = 0)
        dataset.add_indicator_to_db(
            indicator="WS_PPL_W-B",
            id_countries=[country.upper() for country in country_list], # Upper case for the csv
            column_contry_id = "REF_AREA",
            column_name = "INDICATOR",
            column_fullname="Indicator",
            column_value = "OBS_VALUE",
            column_date = "TIME_PERIOD")

    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_list} (UNICEF Data): {e}")

    return

def _fetch_birth_data(country_list):
    """
    Fetches UNICEF data for a list of countries and updates the database.

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
    :return: None
    :rtype: None
    """
    try:
        dataset = webscraping.FetchPageSingle(
            source_dataset="unicef-nt-bw-lbw",
            dataset_index = 0)
        dataset.add_indicator_to_db(
            indicator="NT_BW_LBW",
            id_countries=[country.upper() for country in country_list], # Upper case for the csv
            column_contry_id = "REF_AREA",
            column_name = "INDICATOR",
            column_fullname="Indicator",
            column_value = "OBS_VALUE",
            column_date = "TIME_PERIOD")

    except (AttributeError, ValueError) as e:
        print(f"Erreur avec {country_list} (UNICEF Data): {e}")

    return


########################################################################################################################










############################################### FONCTIONS HEALTH SYSTEMS ###############################################


def update_list_health_systems(country_list):
    """
    Updates the risk factors for a list of countries by fetching data from WHO and World Bank.

    :param country_list: List of country IDs to update.
    :type country_list: list
    :return: None
    :rtype: None

    Examples usage:
        update_list_risk_factors(['fra', 'dza', 'gbr'])
        update_list_risk_factors(['fra'])
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(_fetch_health_systems_data, country_list)

    return

def update_all_health_systems():
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

    update_list_health_systems(country_list)

    return

def _fetch_health_systems_data(country_id):
    """
    Fetches WHO data for a given country and updates the database.

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
    :return: None
    :rtype: None
    """

    indicators = ["SH.UHC.SRVS.CV.XD", "SH.MED.BEDS.ZS","SP.REG.BRTH.ZS","SP.REG.DTHS.ZS"]


    dataset2 = webscraping.FetchPage(
        country_id=country_id,
        source_dataset="world-bank-health-indicators",
        dataset_index=0
    )
    if dataset2.datasets_list is None:
        raise ValueError(f"Error fetching data from World Bank for {country_id} for {indicators}")

    else:
        dataset2.add_indicator_to_db(
            indicators=indicators,
            column_name="Indicator Code",
            column_fullname="Indicator Name",
            column_value="Value",
            column_date="Year"
        )

    return








