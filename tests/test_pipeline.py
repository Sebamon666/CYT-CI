import pandas as pd

from pipeline import filter_cyt


def test_incluye_actividad_cyt_con_postulaciones():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Campamento Verano", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 5},
    ])
    result = filter_cyt(actividades, conteos)
    assert result.to_dict("records") == [{"Actividad": "Campamento Verano", "N_Postulantes": 5}]


def test_excluye_actividad_cyt_sin_postulaciones():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Campamento Verano", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame(columns=["Activity__c", "cnt"])
    result = filter_cyt(actividades, conteos)
    assert len(result) == 0


def test_excluye_actividad_de_otra_area():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Campamento KAOS", "Area__c": "KAOS"},
        {"Id": "a02", "Name": "Campamento CYT", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 10},
        {"Activity__c": "a02", "cnt": 3},
    ])
    result = filter_cyt(actividades, conteos)
    assert result.to_dict("records") == [{"Actividad": "Campamento CYT", "N_Postulantes": 3}]


def test_ordena_descendente_por_cantidad():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Actividad A", "Area__c": "CYT"},
        {"Id": "a02", "Name": "Actividad B", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 2},
        {"Activity__c": "a02", "cnt": 8},
    ])
    result = filter_cyt(actividades, conteos)
    assert result["Actividad"].tolist() == ["Actividad B", "Actividad A"]


def test_inputs_vacios_retorna_dataframe_vacio():
    actividades = pd.DataFrame(columns=["Id", "Name", "Area__c"])
    conteos = pd.DataFrame(columns=["Activity__c", "cnt"])
    result = filter_cyt(actividades, conteos)
    assert len(result) == 0
    assert list(result.columns) == ["Actividad", "N_Postulantes"]
