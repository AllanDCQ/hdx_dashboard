"""
This module contains classes and methods for fetching and processing datasets from various sources,
such as the World Bank Health Indicators and HDX. It includes functionality for downloading datasets,
checking for updates, and adding indicators to a PostgreSQL database.

Classes:
- Fetch: Abstract base class for fetching datasets.
    - FetchPageSingle: Class for fetching a single dataset.
    - FetchPage: Class for fetching and downloading datasets for a specific country.

- IndicatorBase: Abstract base class for handling indicators.
    - Indicator: Class for handling a single indicator.
    - Indicators: Class for handling multiple indicators.

"""
import os
import requests
import io
import pandas as pd
import json

from bs4 import BeautifulSoup
from sqlalchemy import select, create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from abc import ABC, abstractmethod
from datetime import date, datetime


################################################### FETCH PAGES ########################################################


class Fetch(ABC):
    """
    Abstract base class for fetching datasets from HDX.

    Attributes:
        source_dataset (str): The source of the dataset.
        dataset_index (int, optional): The index of the dataset to fetch. Defaults to None.
        datasets_list (pd.DataFrame): The list of datasets fetched from HDX.
    """
    def __init__(self, source_dataset, dataset_index = None):
        self.source_dataset = source_dataset
        self.dataset_index = dataset_index
        self.datasets_list = self._get_datasets_list()

    @abstractmethod
    def _get_datasets_list(self) -> pd.DataFrame:
        """
        Fetches the datasets from HDX.
        """
        pass


    @abstractmethod
    def _check_update_date(self, indicator, id_countries):
        """
        Check if the data is up to date.
        """
        pass

    @abstractmethod
    def add_indicator_to_db(self, *args, **kwargs):
        """
        Abstract method to add indicators to the database.
        """
        pass

    def _read_csv_from_list(self) -> pd.DataFrame:
        """
        Downloads a specific dataset and returns it as a DataFrame.

        :return: A DataFrame containing the dataset.
        :rtype: pd.DataFrame
        """
        dataset = self.datasets_list.iloc[self.dataset_index]
        csv_url = dataset["url"]

        try:
            csv_response = requests.get(csv_url)
            csv_response.raise_for_status()
            data = pd.read_csv(io.StringIO(csv_response.text))
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()

        return data





class FetchPageSingle(Fetch):
    """
    Class to fetch a single dataset from the World Bank Health Indicators and process it.

    Attributes:
        source_dataset (str): The source of the dataset.
        dataset_index (int, optional): The index of the dataset to fetch. Defaults to None.
    """
    def __init__(self, source_dataset, dataset_index=None):
        super().__init__(source_dataset, dataset_index)

    def _get_datasets_list(self) -> pd.DataFrame:
        """
        Fetches the datasets from the World Bank Health Indicators for a specific country.

        :return: A DataFrame containing the datasets.
        """

        # Base URL for the datasets
        base_url = "https://data.humdata.org"
        datasets_url = f"{base_url}/dataset/{self.source_dataset}"


        # Fetch the URL of the page containing the datasets
        try:
            response = requests.get(datasets_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {datasets_url}: {e}")
            return pd.DataFrame()

        soup = BeautifulSoup(response.content, "html.parser")
        resource_list = soup.find(class_="hdx-bs3 resource-list")

        # Create a DataFrame to store the datasets
        df_list_dataset = pd.DataFrame(columns=["title", "update_date", "download_date", "url"])

        if self.dataset_index is not None:
            for dataset in resource_list.find_all(class_="resource-item"):
                # Extract data from the dataset
                try:
                    title = dataset.find('a').get('title') # Title of the dataset
                    update_date = dataset.find(class_="update-date").get_text().strip().split('\n')[-1].strip() # Date of the last update on the website
                    url = dataset.find(class_="resource-download-button").get('href') # URL of the dataset

                    new_row = {
                        "title": title,
                        "update_date": datetime.strptime(update_date, "%d %B %Y").date(),
                        "download_date": date.today(),
                        "url": url
                    }

                    # Append the new row to the DataFrame
                    df_list_dataset = pd.concat([df_list_dataset, pd.DataFrame([new_row])], ignore_index=True)

                except (AttributeError, ValueError) as e:
                    print(f"Error extracting data from dataset: {e}")
                    continue
                return df_list_dataset
            else:
                return df_list_dataset.iloc[self.dataset_index]

    def _check_update_date(self, indicator,id_countries):
        """
        Check if the data is up to date for the given indicator and list of country IDs.

        :param indicator: The indicator to check.
        :type indicator: str
        :param id_countries: List of country IDs to check.
        :type id_countries: list[str]
        :return: List of country IDs that need to be updated.
        :rtype: list[str]
        """

        id_countries_to_update = []

        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.connect() as connection:
            metadata = MetaData()

            # Chargement de la table Indicator
            indicator_table = Table('Indicator', metadata, autoload_with=engine)

            for id_country in id_countries:
                query = select(indicator_table).where(
                    indicator_table.columns.id_indicator == indicator,
                    indicator_table.columns.id_country == id_country)
                result = connection.execute(query).fetchone()

                if result is None:
                    id_countries_to_update.append(id_country)
                else:
                    if result[4] < self.datasets_list["update_date"][self.dataset_index]:
                        id_countries_to_update.append(id_country)

        return id_countries_to_update

    def add_indicator_to_db(self, indicator : str, column_name:str, column_fullname:str, column_date:str, column_value:str, id_countries:list[str], column_contry_id:str) -> None:
        """
        Adds an indicator to the database.

        :param indicator: The indicator to add.
        :type indicator: str
        :param column_name: The name of the column containing the indicator.
        :type column_name: str
        :param column_fullname: The full name of the column containing the indicator.
        :type column_fullname: str
        :param column_date: The name of the column containing the date.
        :type column_date: str
        :param column_value: The name of the column containing the value.
        :type column_value: str
        :param id_countries: The list of country IDs.
        :type id_countries: list[str]
        :param column_contry_id: The column name for the country ID.
        :type column_contry_id: str
        """
        id_countries = [country.lower() for country in id_countries]

        # Check if the countries to up to date
        id_countries_to_update = self._check_update_date(indicator,id_countries)

        if not id_countries_to_update:
            return

        # Get the name of the country
        countries_names_to_update, not_countries, id_countries_to_update = self._get_name_country(id_countries_to_update)

        if not_countries:
            return

        if not countries_names_to_update:
            return


        dataset = self._read_csv_from_list()

        id_countries_to_db = []

        # check if contry id from id_countries_to_update is in the dataset
        for country in id_countries_to_update:
            if any(dataset[column_contry_id] == country):
                id_countries_to_db.append(country)

        if id_countries_to_db == []:
            return


        # Check if the column_date is a yyyy format and remove if not
        #dataset = dataset[dataset[column_date].str.match(r'^\d{4}$', na=False)]

        data_to_update = {
            "list_countries_id": id_countries_to_db,
            "list_countries_name": countries_names_to_update,
            "source_dataset": self.source_dataset,
            "download_date": date.today().strftime("%Y-%m-%d"),
            "update_date": self.datasets_list["update_date"][self.dataset_index].strftime("%Y-%m-%d"),
            "column_name" : column_name,
            "column_fullname" : column_fullname,
            "column_date" : column_date,
            "column_value" : column_value,
            "column_contry_id" : column_contry_id
        }

        columns = [column_contry_id, column_name, column_fullname, column_date, column_value]

        for country in id_countries_to_db:
            data_to_update[str(country)] = (dataset[columns][dataset[column_contry_id] == country.upper()].to_dict(orient="records"))

        indicator = Indicator(data_to_update, indicator)

        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.begin() as connection:
            indicator.send_data_to_db(engine, connection)

        return

    def _get_name_country(self,id_countries: list[str]):
        """
        Gets the names of countries based on their IDs.

        :param id_countries: List of country IDs.
        :type id_countries: list[str]
        :return: A tuple containing the list of country names, the list of IDs that are not countries, and the updated list of country IDs.
        :rtype: tuple[list[str], list[str], list[str]]
        """
        with open("assets/countries.json", "r") as f:
            countries = json.load(f)

        name_countries = []
        not_countries = []

        for id_country in id_countries:
            for region, subregions in countries["regions"].items():
                for subregion, subregion_countries in subregions.items():
                    for country_info in subregion_countries:
                        if id_country.lower() == country_info["alpha3"].lower():
                            name_countries.append(country_info["name"].lower())
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break
            else:
                not_countries.append(id_country)
                id_countries.remove(id_country)


        return name_countries, not_countries, id_countries





class FetchPage(Fetch):
    """
    Class to fetch and download datasets from the HDX page for a specific country and a specific source of dataset.

    :param country_id: The ID of the country.
    :type country_id: str
    :param source_dataset: The source of the dataset.
    :type source_dataset: str
    :param dataset_index: The index of the dataset to fetch (optional).
    :type dataset_index: int
    :param dataset_name: The name of the dataset to fetch (optional).
    :type dataset_name: str
    """
    def __init__(self, country_id, source_dataset, dataset_index=None, dataset_name=None):
        self.id_country = country_id.lower()
        self.country = self._get_country_name()
        self.dataset_name = dataset_name
        super().__init__(source_dataset, dataset_index)

    def _get_country_name(self):
        #open the json file
        with open("assets/countries.json", "r") as f:
            countries = json.load(f)

        # Iterate through the countries to find a match
        for region, subregions in countries["regions"].items():
            for subregion, countries in subregions.items():
                for country_info in countries:
                    if self.id_country.lower() == country_info["alpha3"].lower():
                        return country_info["name"].lower()

        return None

    def _get_datasets_list(self) -> pd.DataFrame:
        """
        Fetches the datasets from the World Bank Health Indicators for a specific country.

        :return: A DataFrame containing the datasets.
        """

        # Base URL for the datasets
        base_url = "https://data.humdata.org"
        if self.source_dataset == "who-data":
            datasets_url = f"{base_url}/dataset/{self.source_dataset}-for-{self.id_country}"
        elif self.source_dataset == "world-bank-health-indicators" :
            datasets_url = f"{base_url}/dataset/{self.source_dataset}-for-{self.country.replace(' ', '-').replace(',','')}"
        else: # world-bank-health-indicators
            datasets_url = f"{base_url}/dataset/{self.source_dataset}"

        # Fetch the URL of the page containing the datasets
        try:
            response = requests.get(datasets_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return None

        soup = BeautifulSoup(response.content, "html.parser")
        resource_list = soup.find(class_="hdx-bs3 resource-list")

        # Create a DataFrame to store the datasets
        df_list_dataset = pd.DataFrame(columns=["title", "update_date", "download_date", "url"])

        for dataset in resource_list.find_all(class_="resource-item"):
            # Extract data from the dataset
            try:
                title = dataset.find('a').get('title') # Title of the dataset
                update_date = dataset.find(class_="update-date").get_text().strip().split('\n')[-1].strip() # Date of the last update on the website
                url = base_url + dataset.find(class_="resource-download-button").get('href') # URL of the dataset

                new_row = {
                    "title": title,
                    "update_date": datetime.strptime(update_date, "%d %B %Y").date(),
                    "download_date": date.today(),
                    "url": url
                }

                # Append the new row to the DataFrame
                df_list_dataset = pd.concat([df_list_dataset, pd.DataFrame([new_row])], ignore_index=True)

            except (AttributeError, ValueError) as e:
                print(f"Error extracting data from dataset: {e}")
                continue
        return df_list_dataset

    def _check_update_date(self, list_indicators):

        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.connect() as connection:
            metadata = MetaData()

            # Chargement de la table Indicator
            indicator_table = Table('Indicator', metadata, autoload_with=engine)

            list_indicators_to_update = []

            for indicator in list_indicators:
                query = select(indicator_table).where(
                    indicator_table.columns.id_indicator == indicator,
                    indicator_table.columns.id_country == self.id_country)
                result = connection.execute(query).fetchone()

                if result is None:
                    list_indicators_to_update.append(indicator)
                else:
                    if result[4] < self.datasets_list["update_date"][self.dataset_index]:
                        list_indicators_to_update.append(indicator)

        return list_indicators_to_update

    def add_indicator_to_db(self, column_name:str, column_fullname:str, column_date:str, column_value:str, column_sexe:str = None, indicators : list[str] = None, dataset_index : int = None) -> None:
        """
        Adds indicators to the database.

        :param column_name: The name of the column containing the indicator.
        :param column_fullname: The full name of the column containing the indicator.
        :param column_date: The name of the column containing the date.
        :param column_value: The name of the column containing the value.
        :param column_sexe: The column name for gender/sex, if applicable.
        :param indicators: The list of indicators to update.
        :param dataset_index: The index of the dataset to fetch (optional).
        """
        list_indicators_to_update = self._check_update_date(indicators)

        if dataset_index is not None:
            self.dataset_index = dataset_index

        if self.dataset_name is not None:
            for index, row in self.datasets_list.iterrows():
                if self.dataset_name.lower() in row["title"].lower():
                    self.dataset_index = index
                    break


        if len(list_indicators_to_update) == 0:
            return

        dataset = self._read_csv_from_list()

        # check if indicator is in the dataset
        for indicator in list_indicators_to_update[:]:
            if not any(dataset[column_name] == indicator):
                list_indicators_to_update.remove(indicator)
            else:
                continue

        data_to_update = {
            "country": self.country,
            "source_dataset": self.source_dataset,
            "download_date": date.today().strftime("%Y-%m-%d"),
            "update_date": self.datasets_list["update_date"][self.dataset_index].strftime("%Y-%m-%d"),
            "id_country": self.id_country,
            "column_name" : column_name,
            "column_fullname" : column_fullname,
            "column_date" : column_date,
            "column_value" : column_value,
            "column_sexe" : column_sexe
        }

        # Get the data for each indicator
        for indicator in list_indicators_to_update:
            columns = [column_name, column_fullname, column_date, column_value]
            # Add the column sexe if it exists
            if column_sexe is not None:
                columns.append(column_sexe)

            data_to_update[str(indicator)] = dataset[columns][dataset[column_name] == indicator].to_dict(orient="records")


        indicators = Indicators(data_to_update, list_indicators_to_update)
        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.begin() as connection:
            indicators.send_data_to_db(engine, connection)


########################################################################################################################







#################################################### INDICATORS ########################################################

class IndicatorBase(ABC):
    """
    Abstract base class for handling indicators.

    Attributes:
        source_dataset (str): The source of the dataset.
        download_date (str): The date when the dataset was downloaded.
        update_date (str): The date when the dataset was last updated.
        column_name (str): The name of the column containing the indicator.
        column_fullname (str): The full name of the column containing the indicator.
        column_date (str): The name of the column containing the date.
        column_value (str): The name of the column containing the value.
    """
    def __init__(self, dict_data):
        self.source_dataset = dict_data["source_dataset"]
        self.download_date = dict_data["download_date"]
        self.update_date = dict_data["update_date"]
        self.column_name = dict_data["column_name"]
        self.column_fullname = dict_data["column_fullname"]
        self.column_date = dict_data["column_date"]
        self.column_value = dict_data["column_value"]

    def _add_row_country(self, country_id, country_name, engine, connection):
        """
        Adds a new row to the Country table in the database.

        :param country_id: The ID of the country.
        :type country_id: str
        :param country_name: The name of the country.
        :type country_name: str
        :param engine: The SQLAlchemy engine to use for the database connection.
        :type engine: sqlalchemy.engine.base.Engine
        :param connection: The SQLAlchemy connection to use for executing the queries.
        :type connection: sqlalchemy.engine.base.Connection
        """
        metadata = MetaData()
        country_table = Table("Country", metadata, autoload_with=engine)

        query = select(country_table).where(country_table.columns.id_country == country_id)
        result = connection.execute(query).fetchone()

        if result is None:
            new_row = {"id_country": country_id, "country_name": country_name}
            insert_stmt = insert(country_table).values(new_row)
            connection.execute(insert_stmt)

    def _add_row_indicator(self, df, indicator, country_id, engine, connection):
        """
        Adds a new row to the Indicator table in the database.

        This method inserts a new row into the Indicator table with the provided indicator data.
        If a row with the same id_indicator and id_country already exists, it updates the existing row.

        :param df: The DataFrame containing the indicator data.
        :type df: pandas.DataFrame
        :param indicator: The indicator to add.
        :type indicator: str
        :param country_id: The ID of the country.
        :type country_id: str
        :param engine: The SQLAlchemy engine to use for the database connection.
        :type engine: sqlalchemy.engine.base.Engine
        :param connection: The SQLAlchemy connection to use for executing the queries.
        :type connection: sqlalchemy.engine.base.Connection
        """
        metadata = MetaData()
        indicator_table = Table('Indicator', metadata, autoload_with=engine)

        new_row = {
            "id_indicator": indicator,
            "id_country": country_id,
            "name_indicator": df[self.column_fullname].iloc[0],
            "source": self.source_dataset,
            "download": self.download_date,
            "update": self.update_date
        }

        insert_stmt = insert(indicator_table).values(new_row)
        on_update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['id_indicator', 'id_country'],
            set_={
                "name_indicator": new_row["name_indicator"],
                "source": new_row["source"],
                "download": new_row["download"],
                "update": new_row["update"]
            }
        )
        connection.execute(on_update_stmt)

    def _add_indicator_values(self, df, indicator, country_id, column_sexe, engine, connection):
        """
        Adds the indicator values to the database.

        This method iterates over the rows of the DataFrame and inserts the indicator values into the database.
        If the indicator value already exists, it updates the existing value.

        :param df: The DataFrame containing the indicator values.
        :type df: pandas.DataFrame
        :param indicator: The indicator to update.
        :type indicator: str
        :param country_id: The ID of the country.
        :type country_id: str
        :param column_sexe: The column name for gender/sex, if applicable.
        :type column_sexe: str or None
        :param engine: The SQLAlchemy engine to use for the database connection.
        :type engine: sqlalchemy.engine.base.Engine
        :param connection: The SQLAlchemy connection to use for executing the queries.
        :type connection: sqlalchemy.engine.base.Connection
        """
        metadata = MetaData()
        timed_indicators = Table("Timed_Indicators", metadata, autoload_with=engine)

        for _, row in df.iterrows():
            sexe = row[column_sexe] if column_sexe else "all"
            new_row = {
                "id_indicator": indicator,
                "id_country": country_id,
                "year_recorded": row[self.column_date],
                "value": row[self.column_value],
                "sexe": sexe
            }

            insert_stmt = insert(timed_indicators).values(new_row)
            on_update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['id_indicator', 'id_country', 'year_recorded', 'sexe'],
                set_={"value": new_row["value"]}
            )
            connection.execute(on_update_stmt)

    @abstractmethod
    def send_data_to_db(self, engine, connection):
        """
        Abstract method to send data to the database.

        :param engine: The SQLAlchemy engine to use for the database connection.
        :type engine: sqlalchemy.engine.base.Engine
        :param connection: The SQLAlchemy connection to use for executing the queries.
        :type connection: sqlalchemy.engine.base.Connection
        """
        pass





class Indicator(IndicatorBase):
    """
    Class to handle a single indicator for a specific country.

    This class is responsible for managing and sending a single indicator's data to the database.

    Attributes:
        list_countries_id (list): The list of country IDs.
        list_countries_name (list): The list of country names.
        indicator (str): The indicator to update.
        data (dict): The data for the indicator.
    """
    def __init__(self, dict_data, indicator):
        super().__init__(dict_data)
        self.list_countries_id = dict_data["list_countries_id"]
        self.list_countries_name = dict_data["list_countries_name"]
        self.indicator = indicator
        self.data = {country: dict_data[country] for country in self.list_countries_id}


    def send_data_to_db(self, engine, connection):
        """
        Sends the data to the database.

        This method iterates over the list of countries and sends the data to the database.
        It first adds the country information to the database, then adds the indicator information,
        and finally adds the indicator values.

        :param engine: The SQLAlchemy engine to use for the database connection.
        :type engine: sqlalchemy.engine.base.Engine
        :param connection: The SQLAlchemy connection to use for executing the queries.
        :type connection: sqlalchemy.engine.base.Connection
        """
        for index, country_id in enumerate(self.list_countries_id):
            country_id = country_id.lower()
            df = pd.DataFrame(self.data[country_id])
            try:
                self._add_row_country(country_id, self.list_countries_name[index], engine, connection)
                self._add_row_indicator(df, self.indicator, country_id, engine, connection)
                self._add_indicator_values(df, self.indicator, country_id, None, engine, connection)
            except KeyError as e:
                print(f"Error extracting data for country {country_id}: {e}")





class Indicators(IndicatorBase):
    """
    Class to handle multiple indicators for a specific country.

    This class is responsible for managing and sending multiple indicators' data to the database.

    Attributes:
        country (str): The name of the country.
        id_country (str): The ID of the country.
        column_sexe (str, optional): The column name for gender/sex, if applicable.
        list_indicators (list): The list of indicators to update.
        data (dict): The data for each indicator.
    """
    def __init__(self, dict_data, list_indicators_to_update):
        super().__init__(dict_data)
        self.country = dict_data["country"]
        self.id_country = dict_data["id_country"]
        self.column_sexe = dict_data.get("column_sexe", None)
        self.list_indicators = list_indicators_to_update
        self.data = {indicator: dict_data[indicator] for indicator in self.list_indicators}

    def send_data_to_db(self, engine, connection):
        """
        Sends the data to the database.

        This method iterates over the list of indicators and sends the data to the database.
        It first adds the country information to the database, then adds the indicator information,
        and finally adds the indicator values.

        :param engine: The SQLAlchemy engine to use for the database connection.
        :type engine: sqlalchemy.engine.base.Engine
        :param connection: The SQLAlchemy connection to use for executing the queries.
        :type connection: sqlalchemy.engine.base.Connection
        """
        self._add_row_country(self.id_country, self.country, engine, connection)

        for indicator in self.list_indicators:
            df = pd.DataFrame(self.data[indicator])
            self._add_row_indicator(df, indicator, self.id_country, engine, connection)
            self._add_indicator_values(df, indicator, self.id_country, self.column_sexe, engine, connection)


########################################################################################################################