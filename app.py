import pandas as pd
import streamlit as st

import pipeline

st.set_page_config(page_title="CYT — Postulaciones", page_icon="🎒", layout="centered")


@st.cache_data
def load_data():
    if not pipeline.OUT_FILE.exists():
        return None
    return pd.read_parquet(pipeline.OUT_FILE)


st.title("🎒 CYT — Postulaciones")

data = load_data()

if data is None or data.empty:
    st.info("Aún no hay datos. Presiona 'Actualizar datos' para cargar desde Salesforce.")
else:
    st.metric("Total postulantes", int(data["N_Postulantes"].sum()))

    tabla = data.rename(columns={"N_Postulantes": "N° Postulantes"})
    st.dataframe(tabla, hide_index=True, use_container_width=True)

    st.bar_chart(data.set_index("Actividad")["N_Postulantes"])

    st.caption(f"Última actualización: {pipeline.get_last_updated()}")

st.divider()

if st.button("🔄 Actualizar datos"):
    with st.spinner("Conectando a Salesforce..."):
        try:
            pipeline.actualizar_datos()
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo actualizar: {e}")
