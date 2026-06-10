import pandas as pd


def filter_cyt(actividades, conteos):
    act_cyt = actividades[actividades["Area__c"] == "CYT"]
    df = act_cyt.merge(conteos, left_on="Id", right_on="Activity__c", how="inner")
    df = df[["Name", "cnt"]].rename(columns={"Name": "Actividad", "cnt": "N_Postulantes"})
    return df.sort_values("N_Postulantes", ascending=False).reset_index(drop=True)
