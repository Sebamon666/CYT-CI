import pandas as pd

from pipeline import filter_cyt, parse_comuna_tipo, agregar_comuna_tipo, filter_cyt_genero


def test_incluye_actividad_que_empieza_con_cdi_y_tiene_postulaciones():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "CDI Campamento Verano", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 5},
    ])
    result = filter_cyt(actividades, conteos)
    assert result.to_dict("records") == [{"Actividad": "CDI Campamento Verano", "N_Postulantes": 5}]


def test_excluye_actividad_cdi_sin_postulaciones():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "CDI Campamento Verano", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame(columns=["Activity__c", "cnt"])
    result = filter_cyt(actividades, conteos)
    assert len(result) == 0


def test_excluye_actividad_que_no_empieza_con_cdi():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Campamento KAOS", "Area__c": "KAOS"},
        {"Id": "a02", "Name": "CDI Campamento Verano", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 10},
        {"Activity__c": "a02", "cnt": 3},
    ])
    result = filter_cyt(actividades, conteos)
    assert result.to_dict("records") == [{"Actividad": "CDI Campamento Verano", "N_Postulantes": 3}]


def test_ordena_descendente_por_cantidad():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "CDI Actividad A", "Area__c": "CYT"},
        {"Id": "a02", "Name": "CDI Actividad B", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 2},
        {"Activity__c": "a02", "cnt": 8},
    ])
    result = filter_cyt(actividades, conteos)
    assert result["Actividad"].tolist() == ["CDI Actividad B", "CDI Actividad A"]


def test_inputs_vacios_retorna_dataframe_vacio():
    actividades = pd.DataFrame(columns=["Id", "Name", "Area__c"])
    conteos = pd.DataFrame(columns=["Activity__c", "cnt"])
    result = filter_cyt(actividades, conteos)
    assert len(result) == 0
    assert list(result.columns) == ["Actividad", "N_Postulantes"]


def test_excluye_actividad_de_area_cyt_si_nombre_no_empieza_con_cdi():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Campamento de Verano", "Area__c": "CYT"},
    ])
    conteos = pd.DataFrame([
        {"Activity__c": "a01", "cnt": 9},
    ])
    result = filter_cyt(actividades, conteos)
    assert len(result) == 0


import pipeline


def test_get_last_updated_sin_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "OUT_FILE", tmp_path / "no_existe.parquet")
    assert pipeline.get_last_updated() is None


def test_get_last_updated_con_archivo(tmp_path, monkeypatch):
    f = tmp_path / "data.parquet"
    f.write_text("x")
    monkeypatch.setattr(pipeline, "OUT_FILE", f)
    assert pipeline.get_last_updated() is not None


def test_parse_comuna_tipo_robotica():
    assert parse_comuna_tipo("CDI Robótica Educativa Recoleta") == ("Recoleta", "Robótica Educativa")


def test_parse_comuna_tipo_videojuegos():
    assert parse_comuna_tipo("CDI Creación De Videojuegos Curicó") == ("Curicó", "Creación de Videojuegos")


def test_parse_comuna_tipo_desconocido():
    assert parse_comuna_tipo("Otra Actividad Cualquiera") == ("Otra Actividad Cualquiera", "Otro")


def test_agregar_comuna_tipo():
    df = pd.DataFrame([
        {"Actividad": "CDI Robótica Educativa Recoleta", "N_Postulantes": 18},
        {"Actividad": "CDI Creación De Videojuegos Recoleta", "N_Postulantes": 19},
    ])
    result = agregar_comuna_tipo(df)
    assert result.to_dict("records") == [
        {"Actividad": "CDI Robótica Educativa Recoleta", "N_Postulantes": 18, "Comuna": "Recoleta", "Tipo": "Robótica Educativa"},
        {"Actividad": "CDI Creación De Videojuegos Recoleta", "N_Postulantes": 19, "Comuna": "Recoleta", "Tipo": "Creación de Videojuegos"},
    ]


def test_agregar_comuna_tipo_no_muta_original():
    df = pd.DataFrame([{"Actividad": "CDI Robótica Educativa Recoleta", "N_Postulantes": 18}])
    agregar_comuna_tipo(df)
    assert list(df.columns) == ["Actividad", "N_Postulantes"]


def test_filter_cyt_genero_incluye_actividad_cyt():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "CDI Robótica Educativa Recoleta", "Area__c": "CYT"},
    ])
    conteos_genero = pd.DataFrame([
        {"Activity__c": "a01", "Genre__c": "Masculino", "cnt": 12},
        {"Activity__c": "a01", "Genre__c": "Femenino", "cnt": 6},
    ])
    result = filter_cyt_genero(actividades, conteos_genero)
    assert result.to_dict("records") == [
        {"Actividad": "CDI Robótica Educativa Recoleta", "Genre__c": "Masculino", "N_Postulantes": 12},
        {"Actividad": "CDI Robótica Educativa Recoleta", "Genre__c": "Femenino", "N_Postulantes": 6},
    ]


def test_filter_cyt_genero_excluye_otra_area():
    actividades = pd.DataFrame([
        {"Id": "a01", "Name": "Campamento KAOS", "Area__c": "KAOS"},
        {"Id": "a02", "Name": "CDI Creación De Videojuegos Talca", "Area__c": "CYT"},
    ])
    conteos_genero = pd.DataFrame([
        {"Activity__c": "a01", "Genre__c": "Masculino", "cnt": 10},
        {"Activity__c": "a02", "Genre__c": "Femenino", "cnt": 4},
    ])
    result = filter_cyt_genero(actividades, conteos_genero)
    assert result.to_dict("records") == [
        {"Actividad": "CDI Creación De Videojuegos Talca", "Genre__c": "Femenino", "N_Postulantes": 4},
    ]


def test_filter_cyt_genero_inputs_vacios():
    actividades = pd.DataFrame(columns=["Id", "Name", "Area__c"])
    conteos_genero = pd.DataFrame(columns=["Activity__c", "Genre__c", "cnt"])
    result = filter_cyt_genero(actividades, conteos_genero)
    assert len(result) == 0
    assert list(result.columns) == ["Actividad", "Genre__c", "N_Postulantes"]
