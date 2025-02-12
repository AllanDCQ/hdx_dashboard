"""
This module contains functions to update health status, services coverages, risk factors, and health systems data for various countries.
It fetches data from WHO, World Bank, and UNICEF, and updates the database accordingly.

Functions:
    HEALTH STATUS INDICATORS:
        - update_list_health_status : Updates the health status for a list of countries.
        - update_all_health_status : Updates the health status for all countries.
        - _fetch_who_data : Fetches indicators
        - _fetch_world_bank_data : Fetches indicators
        - _fetch_unicef_data : Fetches indicators

    SERVICES COVERAGES INDICATORS:
        - update_list_services_coverages : Updates the services coverages indicators for a list of countries.
        - update_all_services_coverages : Updates the services coverages indicators for all countries.
        - _fetch_hiv_data : Fetches indicators
        - _fetch_tuberculosis_data : Fetches indicators
        - _fetch_malaria_data : Fetches indicators
        - _fetch_immunization_data : Fetches indicators

    RISK FACTORS INDICATORS:
        - update_list_risk_factors : Updates the risk factors for a list of countries.
        - update_all_risk_factors : Updates the risk factors for all countries.
        - _fetch_weight_data : Fetches indicators
        - _fetch_drink_safe_data : Fetches indicators
        - _fetch_drink_data : Fetches indicators
        - _fetch_birth_data : Fetches indicators
"""
import webscraping
import json
import concurrent.futures



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

def update_all_health_status():
    """
    Updates the health status for all countries by fetching data from various sources.
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
    Fetches the indicators WHOSIS_000001 and WHOSIS_000002 from WHO for a given country and updates the database.
        - WHOSIS_000001 : Life expectancy at birth (years)
        - WHOSIS_000002 : Healthy life expectancy (HALE) at birth (years)

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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
    Fetches the indicators SH.DYN.MORT, SH.DYN.MORT.FE, SH.DYN.MORT.MA, SH.DYN.NMRT from World Bank for a given country and updates the database.
        - SH.DYN.MORT : Mortality rate, under-5 (per 1,000 live births)
        - SH.DYN.MORT.FE : Mortality rate, under-5, female (per 1,000 live births)
        - SH.DYN.MORT.MA : Mortality rate, under-5, male (per 1,000 live births)
        - SH.DYN.NMRT : Mortality rate, neonatal (per 1,000 live births)

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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
    Fetches the indicator MMR_100k from UNICEF for a list of countries and updates the database.
        - MMR_100k : Maternal mortality ratio (modeled estimate, per 100,000 live births)

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
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
    Updates the services coverages indicators for a list of countries by fetching data from WHO and World Bank.

    :param country_list: List of country IDs to update.
    :type country_list: list

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
    Updates the services coverages indicators for all countries by fetching data from various sources.
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
    Fetches the indicator HIV_0000000001 from WHO for a given country and updates the database.
        - HIV_0000000001 : Number of new HIV infections per 1,000 uninfected population, all ages

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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
    Fetches the indicator MDG_0000000020 from WHO for a given country and updates the database.
        - MDG_0000000020 : Tuberculosis incidence per 100,000 population per year

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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
    Fetches the indicator MALARIA_EST_INCIDENCE from WHO for a given country and updates the database.
        - MALARIA_EST_INCIDENCE : Estimated incidence rate of malaria (per 1,000 population at risk)

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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
    Fetches the indicators WHS3_62, WHS3_41, WHS3_57 from WHO for a given country and updates the database.
        - WHS3_62 : Immunization coverage among 1-year-olds (%)
        - WHS3_41 : Immunization coverage among 1-year-olds (%)
        - WHS3_57 : Immunization coverage among 1-year-olds (%)

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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
    Fetches the indicator NT_ANT_WHZ_PO2 from UNICEF for a list of countries and updates the database.
        - NT_ANT_WHZ_PO2 : Prevalence of wasting, weight-for-height (% of children under 5)

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
    Fetches the indicator WS_PPL_W-PRE from UNICEF for a list of countries and updates the database.
        - WS_PPL_W-PRE : People using at least basic drinking water services (%)

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
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
    Fetches the indicator WS_PPL_W-B from UNICEF for a list of countries and updates the database.
        - WS_PPL_W-B : People using at least basic drinking water services (%)

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
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
    Fetches the indicator NT_BW_LBW from UNICEF for a list of countries and updates the database.
        - NT_BW_LBW : Prevalence of low birth weight among newborns (%)

    :param country_list: The list of country IDs to fetch data for.
    :type country_list: list
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
    Updates the health systems indicators for a list of countries by fetching data from WHO and World Bank.

    :param country_list: List of country IDs to update.
    :type country_list: list

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
    Fetches the indicators SH.UHC.SRVS.CV.XD, SH.MED.BEDS.ZS, SP.REG.BRTH.ZS, SP.REG.DTHS.ZS from World Bank for a given country and updates the database.
        - SH.UHC.SRVS.CV.XD : Service coverage index
        - SH.MED.BEDS.ZS : Hospital beds (per 1,000 people)
        - SP.REG.BRTH.ZS : Completeness of birth registration (%)
        - SP.REG.DTHS.ZS : Completeness of death registration with cause-of-death information (%)

    :param country_id: The ID of the country to fetch data for.
    :type country_id: str
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


########################################################################################################################