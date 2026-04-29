import streamlit as st
from supabase import create_client, Client

# 1. CONEXIÓN A BASE DE DATOS
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="ERP Textil", layout="wide")

# --- BARRA LATERAL (MENÚ) ---
st.sidebar.header("⚙️ PANEL DE CONTROL")

# Forzamos a que el menú siempre esté visible y con una opción marcada
opcion_menu = st.sidebar.selectbox(
    "SELECCIONE UNA PÁGINA:",
    ["🏢 PROVEEDORES", "🧶 TELAS"],
    index=0 # Esto obliga a que empiece siempre en Proveedores
)

# --- PÁGINA DE PROVEEDORES ---
if opcion_menu == "🏢 PROVEEDORES":
    st.title("🏢 Gestión de Proveedores")
    st.write("Registra aquí a tus proveedores para poder crear telas después.")

    # Formulario para registrar
    with st.expander("➕ ABRIR FORMULARIO DE REGISTRO", expanded=True):
        with st.form("nuevo_proveedor"):
            c1, c2 = st.columns(2)
            razon = c1.text_input("Razón Social (Nombre)*")
            ruc = c1.text_input("Número de RUC*")
            tipo = c2.selectbox("Categoría", ["Telas", "Avíos", "Servicios", "Otros"])
            contacto = c2.text_input("Persona de Contacto")
            
            submit = st.form_submit_button("GUARDAR EN BASE DE DATOS")
            
            if submit:
                if razon and ruc:
                    try:
                        supabase.table("proveedores").insert({
                            "razon_social": razon, 
                            "ruc": ruc, 
                            "tipo_proveedor": tipo, 
                            "contacto": contacto
                        }).execute()
                        st.success(f"✅ ¡Éxito! El proveedor {razon} ha sido guardado.")
                        st.rerun() # Esto refresca la página para mostrar los datos
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
                else:
                    st.warning("⚠️ Completa la Razón Social y el RUC.")

    # Tabla de visualización
    st.divider()
    st.subheader("📋 Proveedores en el sistema")
    datos = supabase.table("proveedores").select("*").execute()
    if datos.data:
        st.dataframe(datos.data, use_container_width=True)
    else:
        st.info("Aún no hay proveedores. Usa el formulario de arriba.")

# --- PÁGINA DE TELAS ---
elif opcion_menu == "🧶 TELAS":
    st.title("🧶 Maestro de Telas")
    
    # Consultar si hay proveedores para poder elegir uno
    try:
        prov_data = supabase.table("proveedores").select("id_proveedor, razon_social").execute()
        opciones_p = {p['razon_social']: p['id_proveedor'] for p in prov_data.data} if prov_data.data else {}
    except:
        opciones_p = {}

    if not opciones_p:
        st.error("🚨 NO PUEDES REGISTRAR TELAS TODAVÍA.")
        st.warning("Primero debes ir a la página de '🏢 PROVEEDORES' y registrar al menos uno.")
    else:
        with st.expander("➕ REGISTRAR NUEVA TELA"):
            with st.form("nueva_tela"):
                nombre_t = st.text_input("Nombre de la Tela*")
                prov_t = st.selectbox("¿Quién provee esta tela?", options=list(opciones_p.keys()))
                
                if st.form_submit_button("GUARDAR TELA"):
                    if nombre_t:
                        supabase.table("telas").insert({
                            "nombre_interno": nombre_t,
                            "id_proveedor": opciones_p[prov_t]
                        }).execute()
                        st.success("✅ Tela guardada correctamente.")
                        st.rerun()

        # Listado de Telas
        st.subheader("📋 Catálogo")
        res_telas = supabase.table("telas").select("*, proveedores(razon_social)").execute()
        if res_telas.data:
            st.dataframe(res_telas.data, use_container_width=True)
