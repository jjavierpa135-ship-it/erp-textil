import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- 2. CONEXIÓN A SUPABASE ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Error de conexión"); st.stop()

# --- 3. MEMORIA DE ESTADO (Session State) ---
# Mantiene la persistencia de datos y bloqueos
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    # Genera código técnico automático
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    return f"{prefijo}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"

def nueva_ficha():
    # Resetea todo para un nuevo registro
    st.session_state.bloquear = False
    st.session_state.codigo_actual = "S/C"
    st.session_state.cambios_sin_guardar = False
    st.rerun()

def cargar_ultima_muestra():
    # Obtiene el registro más reciente de la base de datos
    res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
    if res.data:
        ficha = res.data[0]
        st.session_state.codigo_actual = ficha['codigo_muestra']
        return ficha
    return None

# --- 5. LÓGICA DE CARGA INICIAL ---
if st.session_state.codigo_actual == "Cargando...":
    ultima = cargar_ultima_muestra()
    if not ultima: st.session_state.codigo_actual = "S/C"

# --- 6. BARRA LATERAL (EL COSTADO) ---
st.sidebar.title("🏢 ERP Pilar Jeans")
st.sidebar.subheader("Menú de Navegación")
modulo = st.sidebar.radio("Ir a:", ["👗 Diseño y Patronaje", "📦 Almacén", "👥 Proveedores"])

# --- 7. MÓDULO PRINCIPAL ---
if modulo == "👗 Diseño y Patronaje":
    
    # Cabecera con Título, Código y Botón Limpiar
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Gestión de Muestras")
    with col_c: st.metric("Código en Pantalla", st.session_state.codigo_actual)
    with col_b: 
        if st.button("➕ Nueva Ficha (Limpiar)"): nueva_ficha()

    # Pestañas (Área de Diseño y Área de Patronaje)
    tab_diseno, tab_patronaje = st.tabs(["🎨 Área de Diseño", "📐 Área de Patronaje"])

    with tab_diseno:
        # Recuperamos datos de la base de datos para el código que está en pantalla
        res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
        datos_f = res_ficha.data[0] if res_ficha.data else {}

        # Función para detectar que algo cambió en el formulario
        def detectar_cambio():
            st.session_state.cambios_sin_guardar = True

        # Formulario de Diseño
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                cat_lista = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
                # index calcula la posición del dato guardado para mostrarlo en el selector
