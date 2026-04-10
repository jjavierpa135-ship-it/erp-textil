import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- 2. CONEXIÓN A BASE DE DATOS ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Error de conexión"); st.stop()

# --- 3. MEMORIA DE ESTADO (Session State) ---
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True # Inicia bloqueado por defecto
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    return f"{prefijo}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"

def nueva_ficha():
    # Limpia todo para un registro nuevo
    st.session_state.bloquear = False
    st.session_state.codigo_actual = "S/C"
    st.session_state.cambios_sin_guardar = False
    st.rerun()

def cargar_ultima_muestra():
    # Busca el último registro insertado en Supabase
    res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
    if res.data:
        ficha = res.data[0]
        st.session_state.codigo_actual = ficha['codigo_muestra']
        return ficha
    return None

# --- 5. LÓGICA DE INICIO (Solo corre la primera vez) ---
if st.session_state.codigo_actual == "Cargando...":
    ultima = cargar_ultima_muestra()
    if not ultima: st.session_state.codigo_actual = "S/C"

# --- 6. INTERFAZ SUPERIOR ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Menú Principal", ["👗 Diseño y Patronaje", "👥 Proveedores"])

if modulo == "👗 Diseño y Patronaje":
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Gestión de Muestras")
    with col_c: st.metric("Código en Pantalla", st.session_state.codigo_actual)
    with col_b: 
        if st.button("➕ Nueva Ficha (Limpiar)"): nueva_ficha()

    tab_diseno, tab_patronaje = st.tabs(["🎨 Área de Diseño", "📐 Área de Patronaje"])

    with tab_diseno:
        # Recuperamos datos para mostrar (si existen)
        res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
        datos_f = res_ficha.data[0] if res_ficha.data else {}

        # --- FORMULARIO ---
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                # Si cambias cualquier campo, activamos 'cambios_sin_guardar'
                cat = st.selectbox("Categoría", ["Pantalón", "Falda", "Blusa"], 
                                   index=["Pantalón", "Falda", "Blusa"].index(datos_f.get('categoria', "Pantalón")),
                                   disabled=st.session_state.bloquear, on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
                
                estilo = st.selectbox("Estilo", ["Skinny", "Mom Fit", "Slim"], 
                                      index=["Skinny", "Mom Fit", "Slim"].index(datos_f.get('estilo', "Skinny")),
                                      disabled=st.session_state.bloquear, on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
            
            with c2:
                patronista = st.selectbox("Asignar a", ["Patronista 1", "Patronista 2"], 
                                          index=["Patronista 1", "Patronista 2"].index(datos_f.get('patronista_responsable', "Patronista 1")),
                                          disabled=st.session_state.bloquear, on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
                
                obs = st.text_area("Notas Técnicas", value=datos_f.get('observaciones_contra', ""), 
                                   disabled=st.session_state.bloquear, on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))

            st.markdown("---")
            
            # --- BOTONES DE ACCIÓN ---
            b1, b2, b3 = st.columns(3)
            
            with b1:
                if st.button("💾 Guardar Cambios", use_container_width=True):
                    if st.session_state.codigo_actual == "S/C":
                        st.session_state.codigo_actual = generar_codigo(cat, estilo)
                    
                    datos_up = {
                        "codigo_muestra": st.session_state.codigo_actual,
                        "categoria": cat, "estilo": estilo,
                        "patronista_responsable": patronista,
                        "observaciones_contra": obs,
                        "estado": "Borrador"
                    }
                    supabase.table("fichas_muestras").upsert(datos_up, on_conflict="codigo_muestra").execute()
                    st.session_state.bloquear = True
                    st.session_state.cambios_sin_guardar = False # Ya está guardado
                    st.success("Información asegurada.")
                    st.rerun()

            with b2:
                # El botón de enviar se desactiva si hay cambios sin guardar
                bloquear_envio = st.session_state.cambios_sin_guardar or st.session_state.codigo_actual == "S/C"
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=bloquear_envio):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Enviado a patronaje.")
                if st.session_state.cambios_sin_guardar:
                    st.caption("⚠️ Debes guardar los cambios antes de enviar.")

            with b3:
                if st.button("✏️ Habilitar Edición", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab_patronaje:
        st.subheader("Tareas para Patronistas")
        # (Lógica de patronista...)
