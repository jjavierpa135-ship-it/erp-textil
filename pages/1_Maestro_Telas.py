import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. CONEXIÓN A DB ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión: {e}"); st.stop()

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maestro de Telas", page_icon="🧵", layout="wide")

st.title("🧵 Maestro de Telas")
st.markdown("Registra y gestiona las telas disponibles para producción.")

# --- 3. FORMULARIO DE INGRESO ---
with st.expander("➕ Registrar Nueva Tela", expanded=True):
    with st.form("form_telas", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            nombre = st.text_input("Nombre Interno (Ej: FURIOSO, GREGOR)", placeholder="Nombre de la tela")
            proveedor = st.text_input("Proveedor")
        
        with col2:
            composicion = st.text_input("Composición (Ej: 98% Alg, 2% Elast)")
            ancho = st.number_input("Ancho Útil (metros)", min_value=0.0, value=1.50, step=0.05)
            
        with col3:
            precio = st.number_input("Precio Reposición (USD/m)", min_value=0.0, step=0.10)
            st.write("") # Espaciador
            enviar = st.form_submit_button("Guardar Tela en Maestro", use_container_width=True)

        if enviar:
            if nombre:
                payload = {
                    "nombre_interno": nombre.upper(),
                    "proveedor": proveedor,
                    "composicion": composicion,
                    "ancho_util": ancho,
                    "precio_reposicion_usd": precio,
                    "ultima_actualizacion": datetime.datetime.now().isoformat()
                }
                try:
                    supabase.table("maestro_telas").upsert(payload, on_conflict="nombre_interno").execute()
                    st.success(f"✅ Tela '{nombre.upper()}' guardada correctamente.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("El nombre de la tela es obligatorio.")

st.divider()

# --- 4. VISUALIZACIÓN DE TELAS REGISTRADAS ---
st.subheader("📋 Lista de Telas en Sistema")

try:
    res = supabase.table("maestro_telas").select("*").order("nombre_interno").execute()
    if res.data:
        # Mostramos los datos en una tabla limpia
        for t in res.data:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
                c1.write(f"**Nombre:** {t['nombre_interno']}")
                c2.write(f"**Prov:** {t.get('proveedor', 'S/D')}")
                c3.write(f"**Ancho:** {t.get('ancho_util')}m")
                c4.write(f"**Precio:** ${t.get('precio_reposicion_usd'):.2f}")
                if c5.button("Eliminar", key=f"del_{t['nombre_interno']}"):
                    supabase.table("maestro_telas").delete().eq("nombre_interno", t['nombre_interno']).execute()
                    st.rerun()
    else:
        st.info("No hay telas registradas aún.")
except Exception as e:
    st.error(f"Error al cargar la lista: {e}")
