import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="ERP Textil - Javier", page_icon="👗", layout="wide")

# --- CONEXIÓN A SUPABASE (SECRETS) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# --- BARRA LATERAL (MENÚ DE NAVEGACIÓN) ---
st.sidebar.title("🏢 ERP Textil")
st.sidebar.subheader("Menu Principal")

menu_opciones = [
    "👗 Diseño (Ficha Muestra)",
    "✂️ Producción (Corte/Taller)",
    "📦 Almacén",
    "🧾 Facturación/SUNAT",
    "🌐 Tienda Virtual",
    "💰 Finanzas/Bancos",
    "📊 Reportes/KPIs"
]

modulo_actual = st.sidebar.radio("Ir a:", menu_opciones)

# --- MÓDULO 1: DISEÑO (FICHA DE MUESTRAS) ---
if modulo_actual == "👗 Diseño (Ficha Muestra)":
    st.title("👗 Desarrollo de Muestras")
    tab1, tab2 = st.tabs(["📝 Registrar Nueva Muestra", "🔍 Consultar Fichas"])

    with tab1:
        st.subheader("Datos Generales")
        col1, col2 = st.columns(2)
        with col1:
            nombre_modelo = st.text_input("Nombre del Modelo")
            cliente = st.text_input("Cliente / Marca")
            tipo_prenda = st.selectbox("Tipo de Prenda", ["Polo", "Casaca Denim", "Pantalón", "Otros"])
        with col2:
            fecha = st.date_input("Fecha", datetime.date.today())
            tiene_lavado = st.checkbox("¿Requiere Lavado Industrial?")
            observaciones = st.text_area("Observaciones")

        st.markdown("---")
        st.subheader("📸 Fotos de Referencia")
        fotos_subidas = st.file_uploader("Sube fotos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        if fotos_subidas:
            cols = st.columns(4)
            for i, foto in enumerate(fotos_subidas):
                with cols[i % 4]:
                    st.image(foto, caption=f"Miniatura {i+1}", use_container_width=True)

        if st.button("ENVIAR FICHA A LA NUBE", type="primary"):
            st.success("¡Simulación exitosa! (Luego conectaremos todos los campos a Supabase)")
            st.balloons()

    with tab2:
        st.subheader("Buscador de Fichas")
        busqueda = st.text_input("Buscar modelo...")
        st.info("Aquí aparecerá la lista de tus modelos guardados con su galería de fotos.")

# --- OTROS MÓDULOS ---
else:
    st.title(modulo_actual)
    st.info("Módulo en construcción...")
