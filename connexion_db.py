import webscraping


def try_to_update_health_status(list_country):

    for country in list_country:
        try:
            dataset = webscraping.FetchPage(country=country,
                                            source_dataset="who-data",
                                            dataset_index = 0)

            dataset.add_indicator_to_db(indicators=["WHOSIS_000001", "WHOSIS_000002"],
                                        column_name = "GHO (CODE)",
                                        column_value = "Numeric",
                                        column_date = "ENDYEAR",
                                        column_sexe = "DIMENSION (NAME)")
            print(f"Country {country} updated")
        except Exception as e:
            print(f"Error with country {country}: {e}")
            pass

    return

import json
