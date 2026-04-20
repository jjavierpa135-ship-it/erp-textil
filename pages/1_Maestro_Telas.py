import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. CONEXIÓN A DB ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión: {e}"); st.stop()

st.title("🧵 Maestro de Telas")

# --- 2. FORMULARIO ---
with st.expander("➕ Registrar Nueva Tela", expanded=True):
    with st.form("form_telas"):
        c1, c2, c3 = st.columns(3)
        with c1:
            nombre = st.text_input("Nombre Interno").upper()
            prov = st.text_input("Proveedor")
        with c2:
            comp = st.text_input("Composición")
            # Cambiamos 'ancho_util' por 'ancho' si prefieres nombres cortos en tu DB
            ancho_val = st.number_input("Ancho Útil (m)", min_value=0.0, value=1.50)
        with c3:
            precio_val = st.number_input("Precio USD/m", min_value=0.0)
            guardar = st.form_submit_button("Guardar en Maestro")

        if guardar:
            if nombre:
                # IMPORTANTE: Los nombres a la izquierda deben ser IGUALES a los de Supabase
                datos = {
                    "nombre_interno": nombre,
                    "proveedor": prov,
                    "composicion": comp,
                    "ancho_util": ancho_val, # Verifica que en Supabase se llame así
                    "precio_reposicion_usd": precio_val
                }
                res = supabase.table("maestro_telas").upsert(datos).execute()
                st.success("¡Tela guardada!")
                st.rerun()
            else:
                st.error("Falta el nombre de la tela.")

st.divider()

# --- 3. LISTA ---
st.subheader("📋 Inventario de Telas")
try:
    telas = supabase.table("maestro_telas").select("*").execute()
    if telas.data:
        st.table(telas.data)
    else:
        st.info("No hay telas registradas.")
except Exception as e:
    st.error(f"Error al cargar: {e}")
