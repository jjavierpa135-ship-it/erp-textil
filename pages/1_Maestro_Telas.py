import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. CONEXIÓN A DB ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión: {e}"); st.stop()

st.set_page_config(page_title="Maestro de Telas", page_icon="🧵", layout="wide")
st.title("🧵 Maestro de Telas")

# --- 2. FORMULARIO DE INGRESO ---
with st.expander("➕ Registrar Nueva Tela", expanded=True):
    with st.form("form_telas", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            nombre = st.text_input("Nombre Interno (ID)", placeholder="Ej: FURIOSO").upper()
            tipo_tela = st.text_input("Tipo de Tela", placeholder="Ej: Denim, Gabardina")
            composicion = st.text_input("Composición")
        
        with col2:
            cod_prov = st.text_input("Código de Proveedor")
            desc_prov = st.text_area("Descripción de Proveedor", height=68)
            prov_frec = st.text_input("Proveedor Frecuente")
            
        with col3:
            peso = st.number_input("Peso (oz)", min_value=0.0, step=0.1)
            precio = st.number_input("Precio Reposición (USD)", min_value=0.0, step=0.01)
            moneda = st.selectbox("Moneda", ["USD", "ARS", "EUR"])
            st.write("") 
            enviar = st.form_submit_button("Guardar en Base de Datos", use_container_width=True)

        if enviar:
            if nombre:
                # Mapeo exacto a las columnas de tu imagen de Supabase
                payload = {
                    "nombre_interno": nombre,
                    "codigo_proveedor": cod_prov,
                    "descripcion_proveedor": desc_prov,
                    "tipo_tela": tipo_tela,
                    "peso_oz": peso,
                    "composicion": composicion,
                    "proveedor_frecuente": prov_frec,
                    "precio_reposición_usd": precio, # Nota: Verifica si lleva tilde en Supabase. Si falla, quita la tilde a 'reposición'
                    "moneda": moneda,
                    "fecha_registro": datetime.datetime.now().isoformat()
                }
                try:
                    supabase.table("maestro_telas").upsert(payload).execute()
                    st.success(f"✅ Tela '{nombre}' registrada con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("El Nombre Interno es obligatorio.")

st.divider()

# --- 3. TABLA DE CONSULTA ---
st.subheader("📋 Telas Registradas")
try:
    res = supabase.table("maestro_telas").select("*").order("nombre_interno").execute()
    if res.data:
        st.dataframe(res.data, use_container_width=True)
    else:
        st.info("No hay datos.")
except Exception as e:
    st.error(f"Error al cargar lista: {e}")
