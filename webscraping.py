import os

from datetime import date, datetime
import requests
import io
import pandas as pd
from bs4 import BeautifulSoup

from sqlalchemy import select, create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert

import json


DATABASE_URL = os.getenv("DATABASE_URL")


class FetchPage:
    """
    Class to fetch and download datasets from the HDX page for a specific country and a specific source of dataset.

    :param country: The country to fetch the datasets for.
    :param source_dataset: The source of dataset to fetch (e.g. "who-data").
    :param dataset_index: The index of the dataset to fetch (optional).
    """
    def __init__(self, country, source_dataset, dataset_index = None):
        self.country = country.lower()
        self.source_dataset = source_dataset
        try:
            self.id_country = self._get_country_id()
        except AttributeError:
            self.id_country = self.country[:3]
        self.dataset_index = dataset_index

        self.datasets_list = self._get_datasets_list()

    def _get_country_id(self):
        #open the json file
        with open("countries.json", "r") as f:
            countries = json.load(f)

        # Iterate through the countries to find a match
        for country_info in countries:
            if self.country in country_info["name"].lower():
                return country_info["alpha-3"].lower()


    def _get_datasets_list(self) -> pd.DataFrame:
        """
        Fetches the datasets from the World Bank Health Indicators for a specific country.

        :return: A DataFrame containing the datasets.
        """

        # Base URL for the datasets
        base_url = "https://data.humdata.org"
        if self.source_dataset == "who-data":
            datasets_url = f"{base_url}/dataset/{self.source_dataset}-for-{self.id_country}"
        else:
            datasets_url = f"{base_url}/dataset/{self.source_dataset}-for-{self.country}"

        # Fetch the URL of the page containing the datasets
        try:
            response = requests.get(datasets_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {datasets_url}: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of an error

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
            else:
                return df_list_dataset.iloc[self.dataset_index]

    def _check_update_date(self, list_indicators):


        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            metadata = MetaData()

            # Chargement de la table Indicator
            indicator_table = Table('Indicator', metadata, autoload_with=engine)

            list_indicators_to_update = []

            for indicator in list_indicators:
                query = select(indicator_table).where(
                    indicator_table.c.id_indicator == indicator,
                    indicator_table.c.id_country == self.id_country)
                result = connection.execute(query).fetchone()

                if result is None:
                    list_indicators_to_update.append(indicator)
                else:
                    if result[4] < self.datasets_list["update_date"][self.dataset_index]:
                        list_indicators_to_update.append(indicator)

        return list_indicators_to_update


    def _read_csv_from_list(self) -> pd.DataFrame:
        """
        Downloads a specific dataset and returns it as a DataFrame.

        :param dataset: the dataset to download
        :param index: the index of the dataset in the list
        :return: DataFrame containing the dataset
        """
        dataset = self.datasets_list.iloc[self.dataset_index]

        csv_url = dataset["url"]  # Get the URL of the dataset

        try:
            csv_response = requests.get(csv_url)  # Download the dataset
            csv_response.raise_for_status()
            data = pd.read_csv(io.StringIO(csv_response.text))
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()

        return data

    def add_indicator_to_db(self, column_name:str, column_date:str, column_value:str, column_sexe:str, indicators : list[str] = None, dataset_index : int = None) -> None:

        list_indicators_to_update = self._check_update_date(indicators)

        if dataset_index is not None:
            self.dataset_index = dataset_index
            self.datasets_list = self._get_datasets_list()

        if len(list_indicators_to_update) == 0:
            print("No indicators to update")
            return

        print(f"For {self.country}: Indicators to update: {list_indicators_to_update}")
        dataset = self._read_csv_from_list()

        data_to_update = {
            "country": self.country,
            "source_dataset": self.source_dataset,
            "download_date": date.today().strftime("%Y-%m-%d"),
            "update_date": self.datasets_list["update_date"][self.dataset_index].strftime("%Y-%m-%d"),
            "id_country": self.id_country,
            "column_name" : column_name,
            "column_date" : column_date,
            "column_value" : column_value,
            "column_sexe" : column_sexe
        }

        for indicator in list_indicators_to_update:
            data_to_update[str(indicator)] = dataset[[column_name,
                                                      column_date,
                                                      column_value,
                                                      column_sexe]][dataset[column_name] == indicator].to_dict(orient="records")

        indicators = Indicators(data_to_update, list_indicators_to_update)

        engine = create_engine(DATABASE_URL)
        with engine.begin() as connection:
            indicators.send_data_to_db(engine, connection)

        return


class Indicators:

    def __init__(self, dict_data, list_indicators_to_update):
        self.country = dict_data["country"]
        self.source_dataset = dict_data["source_dataset"]
        self.download_date = dict_data["download_date"]
        self.update_date = dict_data["update_date"]
        self.id_country = dict_data["id_country"]
        self.column_name = dict_data["column_name"]
        self.column_date = dict_data["column_date"]
        self.column_value = dict_data["column_value"]
        self.column_sexe = dict_data["column_sexe"]

        self.list_indicators = list_indicators_to_update

        self.data = self._get_data(dict_data)


    def _get_data(self,dict_data):

        data = {indicator: dict_data[indicator] for indicator in self.list_indicators}

        return data

    def _add_row_country(self, engine, connection):
        metadata = MetaData()

        country_table = Table("Country", metadata, autoload_with=engine)

        query = select(country_table).where(country_table.c.id_country == self.id_country)
        result = connection.execute(query).fetchone()

        if result is None:
            new_row = {"id_country": self.id_country, "country_name": self.country}
            insert_stmt = insert(country_table).values(new_row)
            connection.execute(insert_stmt)

            query_after_insert = select(country_table).where(country_table.c.id_country == self.id_country)
            result_after_insert = connection.execute(query_after_insert).fetchone()

        return

    def _add_row_indicator(self, df, indicator, engine, connection):

        metadata = MetaData()
        indicator_table = Table('Indicator', metadata, autoload_with=engine)

        new_row = {
            "id_indicator": indicator,
            "id_country": self.id_country,
            "name_indicator": df[self.column_name][0],
            "source": self.source_dataset,
            "download": self.download_date,
            "update": self.update_date
        }

        # Insert new row or update if it exists
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

        return

    def _add_indicator_values(self, df, indicator, engine, connection):

        metadata = MetaData()

        timed_indicators = Table("Timed_Indicators", metadata, autoload_with=engine)

        for index, row in df.iterrows():
            year = row[self.column_date]
            value = row[self.column_value]

            if self.column_sexe is not None:
                sexe = row[self.column_sexe]
            else:
                sexe = "all"

            new_row = {
                "id_indicator": indicator,
                "id_country": self.id_country,
                "year_recorded": year,
                "value": value,
                "sexe": sexe
            }

            insert_stmt = insert(timed_indicators).values(new_row)
            on_update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['id_indicator', 'id_country', 'year_recorded', 'sexe'],
                set_={
                    "value": new_row["value"]
                }
            )
            connection.execute(on_update_stmt)

        return

    def send_data_to_db(self, engine, connection) -> None:

        self._add_row_country(engine, connection)

        for indicator in self.list_indicators:
            df = pd.DataFrame(self.data[indicator])
            self._add_row_indicator(df, indicator, engine, connection)
            self._add_indicator_values(df, indicator, engine, connection)

        return
