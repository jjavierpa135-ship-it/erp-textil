import streamlit as st
from supabase import create_client, Client

# 1. Conexión (Asegúrate de que tus secrets en Streamlit Cloud estén bien configurados)
try:
    url: str = st.secrets["supabase_url"]
    key: str = st.secrets["supabase_key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error en las credenciales de Supabase. Revisa tus secrets.")
    st.stop()

st.set_page_config(page_title="ERP Textil", layout="wide")

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("🧵 ERP TEXTIL")
menu = st.sidebar.radio("MENÚ PRINCIPAL:", ["🏢 Proveedores", "🧶 Telas"])

# --- PÁGINA: PROVEEDORES ---
if menu == "🏢 Proveedores":
    st.title("Gestión de Proveedores")
    
    # Formulario de Registro
    with st.expander("➕ REGISTRAR NUEVO PROVEEDOR", expanded=True):
        with st.form("form_registro_prov", clear_on_submit=True):
            c1, c2 = st.columns(2)
            razon = c1.text_input("Razón Social*")
            ruc = c1.text_input("RUC*")
            tipo = c2.selectbox("Tipo de Proveedor", ["Telas", "Avíos", "Lavandería", "Taller"])
            cont = c2.text_input("Contacto")
            
            if st.form_submit_button("Guardar Proveedor"):
                if razon and ruc:
                    try:
                        supabase.table("proveedores").insert({
                            "razon_social": razon, 
                            "ruc": ruc, 
                            "tipo_proveedor": tipo, 
                            "contacto": cont
                        }).execute()
                        st.success(f"✅ {razon} guardado con éxito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("⚠️ Razón Social y RUC son obligatorios.")

    # Mostrar Lista
    st.divider()
    st.subheader("📋 Lista de Proveedores Registrados")
    try:
        res = supabase.table("proveedores").select("*").execute()
        if res.data:
            st.dataframe(res.data, use_container_width=True)
        else:
            st.info("No hay proveedores registrados aún.")
    except Exception as e:
        st.error(f"Error al leer proveedores: {e}")

# --- PÁGINA: TELAS ---
elif menu == "🧶 Telas":
    st.title("Maestro de Telas")
    
    # Intentar obtener proveedores para el selector
    try:
        res_prov = supabase.table("proveedores").select("id_proveedor, razon_social").execute()
        lista_prov = res_prov.data if res_prov.data else []
    except:
        lista_prov = []

    if not lista_prov:
        st.error("🚨 NO HAY PROVEEDORES")
        st.info("Para crear una tela, primero ve al menú '🏢 Proveedores' y registra uno.")
    else:
        # Creamos el diccionario de opciones sin errores de nombres
        opciones_prov = {}
        for prov in lista_prov:
            opciones_prov[prov['razon_social']] = prov['id_proveedor']
        
        with st.expander("➕ REGISTRAR NUEVA TELA", expanded=True):
            with st.form("form_telas", clear_on_submit=True):
                nombre_t = st.text_input("Nombre de la Tela*")
                # Aquí usamos el diccionario que acabamos de crear
                prov_nombre = st.selectbox("Seleccionar Proveedor", options=list(opciones_prov.keys()))
                
                if st.form_submit_button("Guardar Tela"):
                    if nombre_t:
                        try:
                            supabase.table("telas").insert({
                                "nombre_interno": nombre_t, 
                                "id_proveedor": opciones_prov[prov_nombre]
                            }).execute()
                            st.success(f"✅ Tela '{nombre_t}' guardada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("El nombre es obligatorio.")

        # Mostrar Lista de Telas
        st.divider()
        st.subheader("📋 Catálogo de Telas")
        try:
            res_t = supabase.table("telas").select("*, proveedores(razon_social)").execute()
            if res_t.data:
                st.dataframe(res_t.data, use_container_width=True)
        except:
            st.info("No hay telas registradas.")
