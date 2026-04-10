import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- 2. CONEXIÓN A DB ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión: {e}"); st.stop()

# --- 3. INICIALIZACIÓN DE ESTADOS CRÍTICOS ---
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    marca = datetime.datetime.now().strftime('%y%m%d%H%M')
    return f"{prefijo}-{marca}"

def nueva_ficha_action():
    # Esta es la única forma de garantizar limpieza: resetear el session_state manualmente
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.cambios_sin_guardar = False
    st.session_state.form_id += 1 
    # Borramos cualquier rastro de valores previos en el estado
    for key in list(st.session_state.keys()):
        if any(prefix in key for prefix in ["cat_", "est_", "pat_", "obs_"]):
            del st.session_state[key]
    st.rerun()

# --- 5. CARGA INICIAL (Solo al abrir la app) ---
if st.session_state.codigo_actual == "Cargando...":
    try:
        res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
        if res.data:
            st.session_state.codigo_actual = res.data[0]['codigo_muestra']
        else:
            st.session_state.codigo_actual = "S/C"
    except:
        st.session_state.codigo_actual = "S/C"

# --- 6. INTERFAZ ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Menú", ["👗 Diseño", "📦 Almacén"])

if modulo == "👗 Diseño":
    # Cabecera fija
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Ficha Técnica")
    with col_c: st.metric("Código Activo", st.session_state.codigo_actual)
    with col_b: 
        # IMPORTANTE: Usamos on_click para ejecutar la limpieza antes de renderizar
        st.button("➕ Nueva Ficha (Limpiar)", on_click=nueva_ficha_action)

    tab1, tab2 = st.tabs(["🎨 Diseño", "📐 Patronaje"])

    with tab1:
        # Recuperación de datos segura
        if st.session_state.codigo_actual == "S/C":
            datos = {}
        else:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            datos = res.data[0] if res.data else {}

        # Listas
        cats = ["Pantalón", "Falda", "Blusa", "Casaca"]
        ests = ["Skinny", "Mom Fit", "Oversize", "Straight"]
        pats = ["Patronista 1", "Patronista 2", "Patronista 3"]

        # FORMULARIO CON KEY ÚNICA (form_id)
        # Al cambiar el form_id, TODO el contenedor se destruye y renace
        with st.container(key=f"main_form_{st.session_state.form_id}"):
            c1, c2 = st.columns(2)
            with c1:
                # Si no hay datos (Nueva Ficha), forzamos index=0
                idx_cat = cats.index(datos['categoria']) if 'categoria' in datos else 0
                val_cat = st.selectbox("Categoría", cats, index=idx_cat, disabled=st.session_state.bloquear,
                                      key=f"cat_input_{st.session_state.form_id}",
                                      on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
                
                idx_est = ests.index(datos['estilo']) if 'estilo' in datos else 0
                val_est = st.selectbox("Estilo", ests, index=idx_est, disabled=st.session_state.bloquear,
                                      key=f"est_input_{st.session_state.form_id}",
                                      on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
            
            with c2:
                idx_pat = pats.index(datos['patronista_responsable']) if 'patronista_responsable' in datos else 0
                val_pat = st.selectbox("Patronista", pats, index=idx_pat, disabled=st.session_state.bloquear,
                                      key=f"pat_input_{st.session_state.form_id}",
                                      on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
                
                txt_obs = datos.get('observaciones_contra', "")
                val_obs = st.text_area("Observaciones", value=txt_obs, disabled=st.session_state.bloquear,
                                      key=f"obs_input_{st.session_state.form_id}",
                                      on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))

            st.divider()
            
            # BOTONES
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("💾 Guardar", use_container_width=True):
                    if st.session_state.codigo_actual == "S/C":
                        st.session_state.codigo_actual = generar_codigo(val_cat, val_est)
                    
                    payload = {
                        "codigo_muestra": st.session_state.codigo_actual,
                        "categoria": val_cat, "estilo": val_est,
                        "patronista_responsable": val_pat, "observaciones_contra": val_obs,
                        "estado": "Borrador"
                    }
                    supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                    st.session_state.bloquear = True
                    st.session_state.cambios_sin_guardar = False
                    st.success("Guardado.")
                    st.rerun()

            with b2:
                can_send = not st.session_state.cambios_sin_guardar and st.session_state.codigo_actual != "S/C"
                if st.button("🚀 Enviar", use_container_width=True, disabled=not can_send):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Enviado.")

            with b3:
                if st.button("✏️ Editar", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab2:
        st.write("Bandeja de Patronaje...")
