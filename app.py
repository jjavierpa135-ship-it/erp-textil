import streamlit as st
from supabase import create_client, Client

# 1. Conexión (Asegúrate de que esto esté correcto)
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="ERP Textil", layout="wide")

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("Navegación")
# Aquí definimos las opciones del menú
menu = st.sidebar.radio("Ir a:", ["🏢 Proveedores", "🧶 Telas"])

# --- LÓGICA DE PÁGINAS ---

if menu == "🏢 Proveedores":
    st.title("Gestión de Proveedores")
    
    # Formulario de Registro
    with st.expander("➕ Registrar Nuevo Proveedor", expanded=True):
        with st.form("form_registro_prov", clear_on_submit=True):
            c1, c2 = st.columns(2)
            razon = c1.text_input("Razón Social*")
            ruc = c1.text_input("RUC*")
            tipo = c2.selectbox("Tipo", ["Telas", "Avíos", "Lavandería", "Taller"])
            cont = c2.text_input("Contacto")
            
            if st.form_submit_button("Guardar Proveedor"):
                if razon and ruc:
                    supabase.table("proveedores").insert({
                        "razon_social": razon, 
                        "ruc": ruc, 
                        "tipo_proveedor": tipo, 
                        "contacto": cont
                    }).execute()
                    st.success("✅ Guardado con éxito")
                    st.rerun()

    # Mostrar Tabla de Proveedores
    st.subheader("Lista de Proveedores")
    res = supabase.table("proveedores").select("*").execute()
    if res.data:
        st.dataframe(res.data, use_container_width=True)

elif menu == "🧶 Telas":
    st.title("Maestro de Telas")
    
    # Primero verificamos si hay proveedores
    res_prov = supabase.table("proveedores").select("id_proveedor, razon_social").execute()
    
    if not res_prov.data:
        st.error("🚨 ERROR: No hay proveedores registrados.")
        st.info("Por favor, selecciona '🏢 Proveedores' en el menú de la izquierda y registra uno primero.")
    else:
        # Si hay proveedores, mostramos el formulario de telas
        dict_prov = {p['razon_social']: p['id_proveedor'] for p in res_prov.data}
        
        with st.expander("➕ Registrar Nueva Tela"):
            with st.form("form_telas"):
                nombre_t = st.text_input("Nombre de Tela*")
                p_elegido = st.selectbox("Seleccionar Proveedor", options=list(dict_prov.keys()))
                
                if st.form_submit_button("Guardar Tela"):
                    supabase.table("telas").insert({
                        "nombre_interno": nombre_t, 
                        "id_proveedor": dict_prov[p_elegido]
                    }).execute()
                    st.success("✅ Tela guardada")
                    st.rerun()

        # Mostrar Tabla de Telas
        res_t = supabase.table("telas").select("*, proveedores(razon_social)").execute()
        if res_t.data:
            st.dataframe(res_t.data, use_container_width=True)
