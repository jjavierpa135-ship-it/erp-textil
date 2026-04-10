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
    st.error("Error de conexión a Supabase"); st.stop()

# --- 3. MEMORIA DE ESTADO (Session State) ---
# Controla bloqueos, el código actual y el reinicio del formulario
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    # Genera código técnico: CAT-EST-AÑO-MES-DIA-HORA-MIN
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    return f"{prefijo}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"

def nueva_ficha():
    # Limpia memoria y cambia la llave (form_id) para resetear selectores
    st.session_state.bloquear = False
    st.session_state.codigo_actual = "S/C"
    st.session_state.cambios_sin_guardar = False
    st.session_state.form_id += 1 
    st.rerun()

def cargar_ultima_muestra():
    # Obtiene la última ficha guardada para mostrarla al iniciar
    try:
        res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
        if res.data:
            ficha = res.data[0]
            st.session_state.codigo_actual = ficha['codigo_muestra']
            return ficha
    except:
        pass
    return None

# --- 5. LÓGICA DE CARGA INICIAL ---
if st.session_state.codigo_actual == "Cargando...":
    ultima = cargar_ultima_muestra()
    if not ultima: st.session_state.codigo_actual = "S/C"

# --- 6. BARRA LATERAL (EL COSTADO) ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Ir a:", ["👗 Diseño y Patronaje", "📦 Almacén", "👥 Proveedores"])

# --- 7. MÓDULO DE DISEÑO (PUNTO 1 COMPLETO) ---
if modulo == "👗 Diseño y Patronaje":
    
    # Cabecera superior
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Gestión de Muestras")
    with col_c: st.metric("Código en Pantalla", st.session_state.codigo_actual)
    with col_b: 
        if st.button("➕ Nueva Ficha (Limpiar)"): nueva_ficha()

    tab_diseno, tab_patronaje = st.tabs(["🎨 Área de Diseño", "📐 Área de Patronaje"])

    with tab_diseno:
        # Jalamos datos de la DB para el código actual
        res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
        datos_f = res_ficha.data[0] if (res_ficha.data and st.session_state.codigo_actual != "S/C") else {}

        def detectar_cambio():
            st.session_state.cambios_sin_guardar = True

        # FORMULARIO CON LLAVES DINÁMICAS PARA LIMPIEZA
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                cat_lista = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
                idx_cat = cat_lista.index(datos_f.get('categoria')) if datos_f.get('categoria') in cat_lista else 0
                cat = st.selectbox("Categoría", cat_lista, index=idx_cat, key=f"cat_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear, on_change=detectar_cambio)
                
                est_lista = ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
                idx_est = est_lista.index(datos_f.get('estilo')) if datos_f.get('estilo') in est_lista else 0
                estilo = st.selectbox("Estilo / Fit", est_lista, index=idx_est, key=f"est_{st.session_state.form_id}",
                                      disabled=st.session_state.bloquear, on_change=detectar_cambio)
            
            with c2:
                pat_lista = ["Patronista 1", "Patronista 2", "Patronista 3"]
                idx_pat = pat_lista.index(datos_f.get('patronista_responsable')) if datos_f.get('patronista_responsable') in pat_lista else 0
                patronista = st.selectbox("Asignar a Patronista", pat_lista, index=idx_pat, key=f"pat_{st.session_state.form_id}",
                                          disabled=st.session_state.bloquear, on_change=detectar_cambio)
                
                obs_val = datos_f.get('observaciones_contra', "")
                obs = st.text_area("Notas Técnicas", value=obs_val, key=f"obs_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear, on_change=detectar_cambio)

            st.markdown("---")
            
            # BOTONES DE ACCIÓN
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
                    st.session_state.cambios_sin_guardar = False
                    st.success("Cambios guardados.")
                    st.rerun()

            with b2:
                bloqueo_envio = st.session_state.cambios_sin_guardar or st.session_state.codigo_actual == "S/C"
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=bloqueo_envio):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Enviado a patronaje.")
                if st.session_state.cambios_sin_guardar:
                    st.caption("⚠️ Guarda primero.")

            with b3:
                if st.button("✏️ Habilitar Edición", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab_patronaje:
        st.subheader("Bandeja de Patronista")
        pendientes = supabase.table("fichas_muestras").select("*").eq("estado", "Pendiente Patronaje").execute()
        if pendientes.data:
            for p in pendientes.data:
                with st.expander(f"📋 {p['codigo_muestra']} - {p['estilo']}"):
                    st.write(f"Patronista: {p['patronista_responsable']}")
                    if st.button(f"Iniciar {p['codigo_muestra']}"):
                        st.info("Iniciando...")
        else:
            st.info("Sin pendientes.")

else:
    st.title(modulo)
    st.info("Próximamente...")
