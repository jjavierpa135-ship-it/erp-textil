import streamlit as st
from supabase import create_client, Client

# 1. Conexión
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="ERP Textil - Telas", layout="wide")

# Menu lateral para navegar entre maestros
menu = st.sidebar.selectbox("Seleccionar Maestro", ["Proveedores", "Telas"])

if menu == "Proveedores":
    st.title("📋 Gestión de Proveedores")
    # ... (Aquí va el código de proveedores que ya probaste)
    # Por ahora, para avanzar, pasemos al de Telas que es el nuevo
    st.info("Ya probamos que este funciona, ¡vamos a las Telas!")

elif menu == "Telas":
    st.title("🧶 Maestro de Telas")

    # Obtener la lista de proveedores para el selector
    res_prov = supabase.table("proveedores").select("id_proveedor, razon_social").execute()
    opciones_proveedores = {p['razon_social']: p['id_proveedor'] for p in res_prov.data}

    with st.expander("➕ Registrar Nueva Tela", expanded=True):
        with st.form("form_telas", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_tela = st.text_input("Nombre de la Tela (Interno)*")
                id_prov = st.selectbox("Proveedor", options=list(opciones_proveedores.keys()))
                tipo_tela = st.selectbox("Tipo de Tela", ["Confort", "Stretch", "Rígido", "Punto"])
            
            with col2:
                peso = st.number_input("Peso (Onzas)", min_value=0.0, step=0.1)
                composicion = st.text_input("Composición (ej: 98% Algodón, 2% Elastano)")
                precio = st.number_input("Precio Referencial", min_value=0.0)
                moneda = st.radio("Moneda", ["Soles", "Dólares"], horizontal=True)

            btn_tela = st.form_submit_button("Guardar Tela")

            if btn_tela:
                if nombre_tela:
                    nueva_tela = {
                        "nombre_interno": nombre_tela,
                        "id_proveedor": opciones_proveedores[id_prov],
                        "tipo_tela": tipo_tela,
                        "peso_onzas": peso,
                        "composicion": composicion,
                        "precio_referencial": precio,
                        "moneda": moneda
                    }
                    try:
                        supabase.table("telas").insert(nueva_tela).execute()
                        st.success(f"✅ Tela '{nombre_tela}' registrada.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("El nombre de la tela es obligatorio.")

    # Listado de Telas
    st.divider()
    st.subheader("📋 Inventario de Telas (Catálogo)")
    res_telas = supabase.table("telas").select("*, proveedores(razon_social)").execute()
    if res_telas.data:
        st.dataframe(res_telas.data, use_container_width=True)
