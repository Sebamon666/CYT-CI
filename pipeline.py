from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from simple_salesforce import Salesforce

DATA_DIR = Path(__file__).parent / "data"
OUT_FILE = DATA_DIR / "postulaciones_cyt.parquet"


def get_connection():
    return Salesforce(
        username=st.secrets["SF_USERNAME"],
        password=st.secrets["SF_PASSWORD"],
        security_token=st.secrets["SF_SECURITY_TOKEN"],
    )


def records_to_df(records):
    return pd.DataFrame([
        {k: v for k, v in rec.items() if k != "attributes"}
        for rec in records
    ])


def fetch_actividades(sf):
    r = sf.query_all("SELECT Id, Name, Area__c FROM Listing__c")
    return records_to_df(r["records"])


def fetch_conteo_postulaciones(sf):
    r = sf.query_all(
        "SELECT Activity__c, COUNT(Id) cnt FROM Postulation__c "
        "GROUP BY Activity__c"
    )
    return records_to_df(r["records"])


def filter_cyt(actividades, conteos):
    act_cyt = actividades[actividades["Area__c"] == "CYT"]
    df = act_cyt.merge(conteos, left_on="Id", right_on="Activity__c", how="inner")
    df = df[["Name", "cnt"]].rename(columns={"Name": "Actividad", "cnt": "N_Postulantes"})
    return df.sort_values("N_Postulantes", ascending=False).reset_index(drop=True)


TIPOS_CYT = {
    "CDI Robótica Educativa ": "Robótica Educativa",
    "CDI Creación De Videojuegos ": "Creación de Videojuegos",
}


def parse_comuna_tipo(nombre_actividad):
    for prefijo, tipo in TIPOS_CYT.items():
        if nombre_actividad.startswith(prefijo):
            return nombre_actividad[len(prefijo):], tipo
    return nombre_actividad, "Otro"


def agregar_comuna_tipo(df):
    df = df.copy()
    comuna_tipo = df["Actividad"].apply(parse_comuna_tipo)
    df["Comuna"] = comuna_tipo.apply(lambda x: x[0])
    df["Tipo"] = comuna_tipo.apply(lambda x: x[1])
    return df


def fetch_conteo_postulaciones_genero(sf):
    r = sf.query_all(
        "SELECT Activity__c, Genre__c, COUNT(Id) cnt FROM Postulation__c "
        "GROUP BY Activity__c, Genre__c"
    )
    return records_to_df(r["records"])


def filter_cyt_genero(actividades, conteos_genero):
    act_cyt = actividades[actividades["Area__c"] == "CYT"]
    df = act_cyt.merge(conteos_genero, left_on="Id", right_on="Activity__c", how="inner")
    df = df[["Name", "Genre__c", "cnt"]].rename(columns={"Name": "Actividad", "cnt": "N_Postulantes"})
    return df.reset_index(drop=True)


def actualizar_datos():
    sf = get_connection()
    df = filter_cyt(fetch_actividades(sf), fetch_conteo_postulaciones(sf))
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(OUT_FILE, index=False)
    return df


def get_last_updated():
    if OUT_FILE.exists():
        return datetime.fromtimestamp(OUT_FILE.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
    return None
