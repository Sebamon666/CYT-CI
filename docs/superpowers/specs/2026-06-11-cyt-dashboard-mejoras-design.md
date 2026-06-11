# Diseño: Mejoras al dashboard CYT (ícono, gráficos por comuna y por género)

## Contexto

El dashboard CYT (`app.py` + `pipeline.py`) hoy muestra una sola tabla con el
total de postulantes por actividad CYT (`Actividad`, `N_Postulantes`),
ordenada descendente. Esta iteración agrega:

1. Cambiar el ícono de la app de 🤖 a 🦾.
2. Dos gráficos de barras horizontales con el desglose de postulantes por
   comuna (total, y total dividido por tipo de taller).
3. Una torta de distribución por género, con un selector que filtra
   únicamente esa torta por actividad CYT específica.

Referencia visual para los gráficos de comuna: `Salesforce/CyT.png`
(estilo de barras horizontales, colores fijos para "Robótica Educativa"
naranja y "Creación de Videojuegos" rojo en el segundo gráfico).

## Datos disponibles (verificado contra el org)

- `Postulation__c.Genre__c`: Masculino / Femenino / Prefiero no decirlo.
  Para las 133 postulaciones de actividades con `Area__c == "CYT"`, el 100%
  tiene este campo cargado (Masculino 105, Femenino 27, Prefiero no decirlo 1)
  — no hay casos "sin dato" dentro de CYT.
- Las 16 actividades CYT siguen el patrón de nombre
  `"CDI Robótica Educativa <Comuna>"` / `"CDI Creación De Videojuegos <Comuna>"`.
  Comuna y Tipo de taller se derivan de este nombre — no requieren un campo
  adicional de Salesforce.

## Cambios en `pipeline.py`

### Nuevas funciones puras (parseo Comuna/Tipo)

```python
TIPOS_CYT = {
    "CDI Robótica Educativa ": "Robótica Educativa",
    "CDI Creación De Videojuegos ": "Creación de Videojuegos",
}

def parse_comuna_tipo(nombre_actividad: str) -> tuple[str, str]:
    """Devuelve (comuna, tipo) a partir del nombre de una actividad CYT.
    Si el nombre no matchea ningún prefijo conocido, tipo="Otro" y comuna
    es el nombre completo."""

def agregar_comuna_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas 'Comuna' y 'Tipo' a un DataFrame con columna 'Actividad',
    aplicando parse_comuna_tipo. No modifica el DataFrame original."""
```

### Nueva consulta y filtro para género

```python
def fetch_conteo_postulaciones_genero(sf) -> pd.DataFrame:
    """SELECT Activity__c, Genre__c, COUNT(Id) cnt FROM Postulation__c
    GROUP BY Activity__c, Genre__c"""

def filter_cyt_genero(actividades: pd.DataFrame, conteos_genero: pd.DataFrame) -> pd.DataFrame:
    """Igual que filter_cyt pero conserva Genre__c. Devuelve columnas
    ['Actividad', 'Genre__c', 'N_Postulantes'], formato largo (una fila por
    combinación actividad x género)."""
```

### `actualizar_datos()`

Se refactoriza para llamar `fetch_actividades(sf)` una sola vez y reutilizarlo
en ambos filtros (hoy se llamaría dos veces si agregamos el segundo fetch sin
tocar esto):

```python
OUT_FILE_GENERO = DATA_DIR / "postulaciones_cyt_genero.parquet"

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

`OUT_FILE_GENERO` queda cubierto por la regla existente `data/*.parquet` en
`.gitignore`.

## Cambios en `app.py`

### Ícono

`page_icon="🦾"` y `st.title("🦾 CYT — Postulaciones")` (reemplaza 🤖).

### Sección "📍 Postulantes por comuna"

Debajo de la tabla actual. Se calcula `agregar_comuna_tipo(data)` sobre el
DataFrame de `postulaciones_cyt.parquet` ya cargado.

- **Gráfico 1**: barras horizontales, una fila por comuna, valor = suma de
  `N_Postulantes` de ambos tipos. Un color distinto por comuna (paleta
  `px.colors.qualitative.Pastel`), orden descendente por total, con la
  cantidad como etiqueta sobre cada barra.
- **Gráfico 2**: barras horizontales apiladas, mismo orden de comunas que el
  gráfico 1, segmentadas por `Tipo` con colores fijos
  (`"Robótica Educativa": "orange"`, `"Creación de Videojuegos": "red"`),
  con la cantidad como etiqueta en cada segmento.

Ambos con `px.bar(..., orientation="h")`, mostrados con `st.plotly_chart`.

### Sección "👥 Postulantes por género"

Se carga `postulaciones_cyt_genero.parquet` (nuevo, con `@st.cache_data`,
mismo patrón que `load_data`).

Layout con `st.columns`: en la columna angosta, un `st.selectbox` con opciones
`["Todas"] + <16 actividades CYT>` (default "Todas"). En la columna ancha, una
torta (`px.pie`) con la distribución de `Genre__c`:
- Si "Todas": se agrupan todas las actividades (suma de `N_Postulantes` por
  `Genre__c`).
- Si una actividad específica: se filtra `data_genero` a esa actividad.

El selector solo afecta esta torta — no afecta la tabla ni los gráficos de
comuna.

## Testing

En `tests/test_pipeline.py`, siguiendo el estilo existente (DataFrames de
entrada armados a mano, `assert ... == ...` sobre `to_dict("records")` o listas):

- `parse_comuna_tipo`: casos para "CDI Robótica Educativa X", "CDI Creación De
  Videojuegos X", y un nombre que no matchea ningún prefijo (→ "Otro").
- `agregar_comuna_tipo`: agrega columnas Comuna/Tipo correctamente sobre un
  DataFrame de ejemplo, sin mutar el original.
- `filter_cyt_genero`: análogo a los tests existentes de `filter_cyt`
  (incluye actividad CYT con género, excluye otra área, formato largo
  correcto).

Los gráficos de Plotly y el layout de `app.py` no se prueban con pytest — se
validan corriendo la app en local (`streamlit run app.py`), como ya se hizo
con cambios anteriores de UI.

## Dependencias

Se agrega `plotly` a `requirements.txt`.

## Fuera de alcance

- No se modifica `filter_cyt` ni `postulaciones_cyt.parquet` existentes.
- No se valida el comportamiento si en el futuro aparecen postulaciones CYT
  sin `Genre__c` (hoy no ocurre); si pasa, esa fila simplemente no aparecerá
  como segmento en la torta de "Todas" salvo que se sume como categoría
  "Sin dato" más adelante.
