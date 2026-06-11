import pandas as pd
import plotly.express as px
import streamlit as st

import pipeline

st.set_page_config(page_title="CYT — Postulaciones", page_icon="🦾", layout="wide")


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


def boton_actualizar():
    if st.button("🔄 Actualizar datos"):
        with st.spinner("Conectando a Salesforce..."):
            try:
                pipeline.actualizar_datos()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo actualizar: {e}")


st.title("🦾 CYT — Postulaciones")

data = load_data()

if data is None or data.empty:
    st.info("Aún no hay datos. Presiona 'Actualizar datos' para cargar desde Salesforce.")
    boton_actualizar()
else:
    col_metric, col_boton = st.columns([3, 1], vertical_alignment="bottom")
    with col_metric:
        st.metric("Total postulantes", int(data["N_Postulantes"].sum()))
    with col_boton:
        boton_actualizar()

    col_tabla, col_genero = st.columns(2)

    with col_tabla:
        tabla = data.rename(columns={"N_Postulantes": "N° Postulantes"})
        altura = (len(tabla) + 1) * 35 + 3
        st.dataframe(tabla, hide_index=True, use_container_width=True, height=altura)
        st.caption(f"Última actualización: {pipeline.get_last_updated()}")

    with col_genero:
        st.subheader("👥 Postulantes por género")

        data_genero = load_data_genero()

        if data_genero is None or data_genero.empty:
            st.info("Aún no hay datos de género. Presiona 'Actualizar datos'.")
        else:
            actividades_cyt = sorted(data_genero["Actividad"].unique())
            actividad_seleccionada = st.selectbox("Actividad", ["Todas"] + actividades_cyt)

            if actividad_seleccionada == "Todas":
                datos_torta = data_genero.groupby("Genre__c")["N_Postulantes"].sum().reset_index()
            else:
                datos_torta = data_genero[data_genero["Actividad"] == actividad_seleccionada]

            fig_genero = px.pie(datos_torta, values="N_Postulantes", names="Genre__c")
            st.plotly_chart(fig_genero, use_container_width=True)

    st.subheader("📍 Postulantes por comuna")

    df_comuna = pipeline.agregar_comuna_tipo(data)
    totales_comuna = (
        df_comuna.groupby("Comuna")["N_Postulantes"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    orden_comunas = totales_comuna["Comuna"].tolist()

    col_bar_tipo, col_bar_total = st.columns(2)

    with col_bar_tipo:
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
        fig_tipo.update_traces(textfont_size=16, textfont_color="black")
        st.plotly_chart(fig_tipo, use_container_width=True)

    with col_bar_total:
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
        fig_total.update_traces(textfont_size=16, textfont_color="black")
        st.plotly_chart(fig_total, use_container_width=True)
