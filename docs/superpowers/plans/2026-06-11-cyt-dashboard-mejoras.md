# Mejoras al dashboard CYT (ícono, gráficos por comuna, torta por género) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cambiar el ícono de la app CYT, y agregar al dashboard dos gráficos de barras (postulantes por comuna, y por comuna+tipo de taller) y una torta de distribución por género filtrable por actividad.

**Architecture:** `pipeline.py` gana funciones puras de transformación (parseo de Comuna/Tipo desde el nombre de actividad) y un nuevo fetch+filtro agregado por género que se persiste en `data/postulaciones_cyt_genero.parquet`. `app.py` consume ambos parquets y renderiza los gráficos con Plotly Express vía `st.plotly_chart`.

**Tech Stack:** Python, pandas, Streamlit, Plotly Express, pytest.

Spec de referencia: `docs/superpowers/specs/2026-06-11-cyt-dashboard-mejoras-design.md`

---

### Task 1: Cambiar ícono de 🤖 a 🦾

**Files:**
- Modify: `app.py:6` y `app.py:16`

- [ ] **Step 1: Editar `page_icon` y título**

En `app.py`, reemplazar:

```python
st.set_page_config(page_title="CYT — Postulaciones", page_icon="🤖", layout="centered")
```

por:

```python
st.set_page_config(page_title="CYT — Postulaciones", page_icon="🦾", layout="centered")
```

Y reemplazar:

```python
st.title("🤖 CYT — Postulaciones")
```

por:

```python
st.title("🦾 CYT — Postulaciones")
```

- [ ] **Step 2: Commit**

```bash
git add app.py
git commit -m "feat: cambiar icono de la app a brazo robotico"
```

---

### Task 2: `parse_comuna_tipo` y `agregar_comuna_tipo`

**Files:**
- Modify: `pipeline.py` (agregar funciones después de `filter_cyt`, antes de `actualizar_datos`)
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_pipeline.py`, reemplazar la línea de import:

```python
from pipeline import filter_cyt
```

por:

```python
from pipeline import filter_cyt, parse_comuna_tipo, agregar_comuna_tipo
```

Y agregar al final del archivo (antes de las funciones `test_get_last_updated_*` o después, da igual mientras quede dentro del archivo):

```python
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
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_pipeline.py -v -k "comuna_tipo"`
Expected: FAIL con `ImportError: cannot import name 'parse_comuna_tipo' from 'pipeline'`

- [ ] **Step 3: Implementar las funciones**

En `pipeline.py`, agregar después de `filter_cyt` (después de la línea que termina con `return df.sort_values("N_Postulantes", ascending=False).reset_index(drop=True)`) y antes de `def actualizar_datos():`:

```python
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
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_pipeline.py -v -k "comuna_tipo"`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline.py tests/test_pipeline.py
git commit -m "feat: parsear comuna y tipo de taller desde el nombre de la actividad"
```

---

### Task 3: `fetch_conteo_postulaciones_genero` y `filter_cyt_genero`

**Files:**
- Modify: `pipeline.py` (agregar funciones después de `agregar_comuna_tipo`, antes de `actualizar_datos`)
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_pipeline.py`, ampliar el import de la línea modificada en la Task 2:

```python
from pipeline import filter_cyt, parse_comuna_tipo, agregar_comuna_tipo, filter_cyt_genero
```

Y agregar al final del archivo:

```python
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
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_pipeline.py -v -k "genero"`
Expected: FAIL con `ImportError: cannot import name 'filter_cyt_genero' from 'pipeline'`

- [ ] **Step 3: Implementar las funciones**

En `pipeline.py`, agregar después de `agregar_comuna_tipo` y antes de `def actualizar_datos():`:

```python
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
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_pipeline.py -v -k "genero"`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline.py tests/test_pipeline.py
git commit -m "feat: agregar fetch y filtro de conteo de postulaciones CYT por genero"
```

---

### Task 4: Persistir `postulaciones_cyt_genero.parquet` en `actualizar_datos`

**Files:**
- Modify: `pipeline.py` (constante `OUT_FILE_GENERO` y función `actualizar_datos`)

- [ ] **Step 1: Agregar la constante `OUT_FILE_GENERO`**

En `pipeline.py`, reemplazar:

```python
DATA_DIR = Path(__file__).parent / "data"
OUT_FILE = DATA_DIR / "postulaciones_cyt.parquet"
```

por:

```python
DATA_DIR = Path(__file__).parent / "data"
OUT_FILE = DATA_DIR / "postulaciones_cyt.parquet"
OUT_FILE_GENERO = DATA_DIR / "postulaciones_cyt_genero.parquet"
```

- [ ] **Step 2: Refactorizar `actualizar_datos`**

Reemplazar:

```python
def actualizar_datos():
    sf = get_connection()
    df = filter_cyt(fetch_actividades(sf), fetch_conteo_postulaciones(sf))
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(OUT_FILE, index=False)
    return df
```

por:

```python
def actualizar_datos():
    sf = get_connection()
    actividades = fetch_actividades(sf)
    df = filter_cyt(actividades, fetch_conteo_postulaciones(sf))
    df_genero = filter_cyt_genero(actividades, fetch_conteo_postulaciones_genero(sf))
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(OUT_FILE, index=False)
    df_genero.to_parquet(OUT_FILE_GENERO, index=False)
    return df
```

- [ ] **Step 3: Correr toda la suite de tests para verificar que nada se rompió**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: todos los tests existentes + los nuevos de las Tasks 2 y 3 en PASS (15 passed)

- [ ] **Step 4: Commit**

```bash
git add pipeline.py
git commit -m "feat: guardar postulaciones_cyt_genero.parquet al actualizar datos"
```

---

### Task 5: Agregar Plotly como dependencia

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Instalar plotly**

Run: `pip install plotly`

- [ ] **Step 2: Obtener la versión instalada**

Run: `python -c "import plotly; print(plotly.__version__)"`

Anotar la versión impresa (ej. `5.24.1`) para el siguiente paso.

- [ ] **Step 3: Agregar a `requirements.txt`**

En `requirements.txt`, agregar una línea al final con el formato `plotly==<version impresa en el Step 2>`, por ejemplo:

```
streamlit==1.58.0
pandas==3.0.3
pyarrow==24.0.0
simple-salesforce==1.12.9
plotly==5.24.1
```

(Usar el número real de versión obtenido en el Step 2, no necesariamente `5.24.1`.)

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: agregar plotly como dependencia"
```

---

### Task 6: Sección "📍 Postulantes por comuna" en `app.py`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Agregar el import de Plotly**

Reemplazar:

```python
import pandas as pd
import streamlit as st

import pipeline
```

por:

```python
import pandas as pd
import plotly.express as px
import streamlit as st

import pipeline
```

- [ ] **Step 2: Agregar la sección de gráficos por comuna**

Reemplazar:

```python
    tabla = data.rename(columns={"N_Postulantes": "N° Postulantes"})
    altura = (len(tabla) + 1) * 35 + 3
    st.dataframe(tabla, hide_index=True, use_container_width=True, height=altura)

    st.caption(f"Última actualización: {pipeline.get_last_updated()}")
```

por:

```python
    tabla = data.rename(columns={"N_Postulantes": "N° Postulantes"})
    altura = (len(tabla) + 1) * 35 + 3
    st.dataframe(tabla, hide_index=True, use_container_width=True, height=altura)

    st.caption(f"Última actualización: {pipeline.get_last_updated()}")

    st.subheader("📍 Postulantes por comuna")

    df_comuna = pipeline.agregar_comuna_tipo(data)
    totales_comuna = (
        df_comuna.groupby("Comuna")["N_Postulantes"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    orden_comunas = totales_comuna["Comuna"].tolist()

    fig_total = px.bar(
        totales_comuna,
        x="N_Postulantes",
        y="Comuna",
        orientation="h",
        color="Comuna",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        text="N_Postulantes",
        category_orders={"Comuna": orden_comunas},
    )
    fig_total.update_yaxes(autorange="reversed")
    fig_total.update_layout(showlegend=False)
    st.plotly_chart(fig_total, use_container_width=True)

    fig_tipo = px.bar(
        df_comuna,
        x="N_Postulantes",
        y="Comuna",
        color="Tipo",
        orientation="h",
        barmode="stack",
        text="N_Postulantes",
        color_discrete_map={
            "Robótica Educativa": "orange",
            "Creación de Videojuegos": "red",
        },
        category_orders={"Comuna": orden_comunas},
    )
    fig_tipo.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tipo, use_container_width=True)
```

- [ ] **Step 3: Verificar que la app levanta sin errores**

Run: `python -m streamlit run app.py --server.headless true`

Expected: la app arranca sin tracebacks en la consola (puede mostrar "Aún no hay datos" si `data/postulaciones_cyt.parquet` no existe — eso es esperado y no es un error).

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: agregar graficos de postulantes por comuna y tipo de taller"
```

---

### Task 7: Sección "👥 Postulantes por género" en `app.py`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Agregar `load_data_genero`**

Reemplazar:

```python
@st.cache_data
def load_data():
    if not pipeline.OUT_FILE.exists():
        return None
    return pd.read_parquet(pipeline.OUT_FILE)
```

por:

```python
@st.cache_data
def load_data():
    if not pipeline.OUT_FILE.exists():
        return None
    return pd.read_parquet(pipeline.OUT_FILE)


@st.cache_data
def load_data_genero():
    if not pipeline.OUT_FILE_GENERO.exists():
        return None
    return pd.read_parquet(pipeline.OUT_FILE_GENERO)
```

- [ ] **Step 2: Agregar la sección de torta por género**

Reemplazar el bloque agregado en la Task 6 (el final de la sección de comuna):

```python
    fig_tipo.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tipo, use_container_width=True)
```

por:

```python
    fig_tipo.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tipo, use_container_width=True)

    st.subheader("👥 Postulantes por género")

    data_genero = load_data_genero()

    if data_genero is None or data_genero.empty:
        st.info("Aún no hay datos de género. Presiona 'Actualizar datos'.")
    else:
        col_filtro, col_torta = st.columns([1, 2])

        with col_filtro:
            actividades_cyt = sorted(data_genero["Actividad"].unique())
            actividad_seleccionada = st.selectbox("Actividad", ["Todas"] + actividades_cyt)

        if actividad_seleccionada == "Todas":
            datos_torta = data_genero.groupby("Genre__c")["N_Postulantes"].sum().reset_index()
        else:
            datos_torta = data_genero[data_genero["Actividad"] == actividad_seleccionada]

        with col_torta:
            fig_genero = px.pie(datos_torta, values="N_Postulantes", names="Genre__c")
            st.plotly_chart(fig_genero, use_container_width=True)
```

- [ ] **Step 3: Verificar que la app levanta sin errores**

Run: `python -m streamlit run app.py --server.headless true`

Expected: la app arranca sin tracebacks. Si `data/postulaciones_cyt_genero.parquet` no existe todavía, debe mostrarse el mensaje "Aún no hay datos de género..." sin error.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: agregar torta de postulantes por genero filtrable por actividad"
```

---

### Task 8: Verificación visual end-to-end en local

**Files:** ninguno (verificación manual)

- [ ] **Step 1: Levantar la app**

Run: `python -m streamlit run app.py`

- [ ] **Step 2: Regenerar datos**

En el navegador, presionar "🔄 Actualizar datos". Esto ejecuta `actualizar_datos()`, que ahora también genera `data/postulaciones_cyt_genero.parquet`.

- [ ] **Step 3: Checklist visual**

Confirmar en el navegador:
- El ícono de la pestaña y el título muestran 🦾.
- Aparece "📍 Postulantes por comuna" con el gráfico de barras totales (un color por comuna) y el gráfico apilado por Tipo (naranja = Robótica Educativa, rojo = Creación de Videojuegos), ambos ordenados de mayor a menor.
- Aparece "👥 Postulantes por género" con un selector ("Todas" + las actividades CYT) y una torta que cambia según la actividad seleccionada.

- [ ] **Step 4: Ajustes finales**

Si algo no se ve bien (colores, orden, tamaños), ajustar directamente en `app.py` y volver a verificar en el navegador. Cuando quede conforme, hacer commit de los ajustes:

```bash
git add app.py
git commit -m "fix: ajustes visuales graficos comuna y genero"
```

(Omitir este commit si no hubo ajustes.)
