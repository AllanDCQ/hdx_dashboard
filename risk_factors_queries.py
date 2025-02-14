from sqlalchemy import create_engine, MetaData, Table, select, and_
import pandas as pd
import dash_bootstrap_components as dbc

DATABASE_URL = ""

# Dictionnaire de correspondance code <-> libellé réel
INDICATORS_MAPPING = {
    "NT_ANT_WHZ_PO2": "Weight-for-height >+2 SD (overweight)",
    "NT_BW_LBW": "Prevalence of low birth weight among <br>new-borns",
    "WS_PPL_W-PRE": "Proportion of population using safely managed drinking water services",
    "WS_PPL_W-B": "Proportion of population using basic drinking water services"
}

def get_risk_factors_data(country_codes=None):
    #modification ici
    if country_codes:
        # Il faut convertir les codes en minuscules pour correspondre à la BD
        country_codes = [code.lower() for code in country_codes]  # <- Ajoutez cette ligne

    """
    Récupère les données des facteurs de risque.
    Si country_codes est fourni, ne récupère que ces pays.
    Sinon, récupère tous les enregistrements pour les indicateurs spécifiés.
    """
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    try:
        timed_indicators = metadata.tables['Timed_Indicators']
    except KeyError:
        print("La table 'Timed_Indicators' n'a pas été trouvée dans la base de données.")
        return pd.DataFrame()

    # Constitution du ou des filtres
    indicator_filter = timed_indicators.c.id_indicator.in_(INDICATORS_MAPPING.keys())
    if country_codes:
        country_filter = timed_indicators.c.id_country.in_(country_codes)
        final_filter = and_(country_filter, indicator_filter)
    else:
        final_filter = indicator_filter

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

        
def get_available_years_and_countries():
    """
    Récupère les années et les pays disponibles dans la base de données.
    """
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    try:
        timed_indicators = metadata.tables['Timed_Indicators']
    except KeyError:
        print("La table 'Timed_Indicators' n'a pas été trouvée dans la base de données.")
        return [], []

    with engine.connect() as conn:
        years = conn.execute(select(timed_indicators.c.year_recorded.distinct())).fetchall()
        countries = conn.execute(select(timed_indicators.c.id_country.distinct())).fetchall()
    
    years = [year[0] for year in years]
    countries = [country[0] for country in countries]
    return years, countries


if __name__ == "__main__":
    df = get_risk_factors_data()  # Sans paramètre country_codes
    
    if not df.empty:
        print(f"✅ {len(df)} lignes trouvées au total\n")
        
        # Compter le nombre de lignes par indicateur
        counts_by_indicator = df['id_indicator'].value_counts()
        print("Nombre de lignes par indicateur :")
        for indicator, count in counts_by_indicator.items():
            print(f"- {indicator}: {count} lignes")
        
        print("\nIndicateurs récupérés :")
        print(df[['id_indicator']].drop_duplicates().to_string(index=False))
        
        print("\nAperçu des données :")
        print(df.head().to_string(index=False))
    else:
        print("❌ Aucune donnée trouvée")

    years, countries = get_available_years_and_countries()
    print("\nAnnées disponibles :", years)
    print("Pays disponibles :", countries)