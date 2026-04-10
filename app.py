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

# --- 3. INICIALIZACIÓN DE ESTADOS ---
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False

# --- 4. FUNCIONES DE ACCIÓN ---
def generar_codigo(cat, est):
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    marca = datetime.datetime.now().strftime('%y%m%d%H%M')
    return f"{prefijo}-{marca}"

def reset_para_nueva_ficha():
    """Limpia la memoria del formulario por completo"""
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.cambios_sin_guardar = False
    # Cambiamos el form_id para que Streamlit crea que es un formulario nuevo
    st.session_state.form_id += 1
    # Borramos manualmente los valores de los widgets del session_state
    for key in list(st.session_state.keys()):
        if key.startswith(('c_', 'e_', 'p_', 'o_')):
            del st.session_state[key]

# --- 5. CARGA INICIAL (Solo al abrir) ---
if st.session_state.codigo_actual == "Cargando...":
    try:
        res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
        st.session_state.codigo_actual = res.data[0]['codigo_muestra'] if res.data else "S/C"
    except:
        st.session_state.codigo_actual = "S/C"

# --- 6. INTERFAZ ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Menú", ["👗 Diseño", "📦 Almacén"])

if modulo == "👗 Diseño":
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Ficha Técnica")
    with col_c: st.metric("Código Activo", st.session_state.codigo_actual)
    with col_b: 
        # Al hacer clic, ejecuta la limpieza
        st.button("➕ Nueva Ficha (Limpiar)", on_click=reset_para_nueva_ficha)

    tab1, tab2 = st.tabs(["🎨 Diseño", "📐 Patronaje"])

    with tab1:
        # Recuperación de datos solo si no es una ficha nueva
        datos_db = {}
        if st.session_state.codigo_actual != "S/C":
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]

        # Listas de opciones
        cats = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Patronista 1", "Patronista 2", "Patronista 3"]

        # FORMULARIO
        # Usamos el form_id en la 'key' de cada widget para forzar el vaciado
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                idx_cat = cats.index(datos_db['categoria']) if 'categoria' in datos_db else 0
                val_cat = st.selectbox("Categoría", cats, index=idx_cat, 
                                      disabled=st.session_state.bloquear,
                                      key=f"c_{st.session_state.form_id}")
                
                idx_est = ests.index(datos_db['estilo']) if 'estilo' in datos_db else 0
                val_est = st.selectbox("Estilo", ests, index=idx_est, 
                                      disabled=st.session_state.bloquear,
                                      key=f"e_{st.session_state.form_id}")
            
            with c2:
                idx_pat = pats.index(datos_db['patronista_responsable']) if 'patronista_responsable' in datos_db else 0
                val_pat = st.selectbox("Patronista", pats, index=idx_pat, 
                                      disabled=st.session_state.bloquear,
                                      key=f"p_{st.session_state.form_id}")
                
                # El valor del texto se limpia si el código es S/C
                txt_area = datos_db.get('observaciones_contra', "") if st.session_state.codigo_actual != "S/C" else ""
                val_obs = st.text_area("Observaciones", value=txt_area, 
                                      disabled=st.session_state.bloquear,
                                      key=f"o_{st.session_state.form_id}")

            # Control de cambios simple
            if not st.session_state.bloquear and st.session_state.codigo_actual != "S/C":
                if val_cat != datos_db.get('categoria') or val_est != datos_db.get('estilo') or val_obs != datos_db.get('observaciones_contra'):
                    st.session_state.cambios_sin_guardar = True

            st.divider()
            
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("💾 Guardar", use_container_width=True):
                    cod = st.session_state.codigo_actual
                    if cod == "S/C":
                        cod = generar_codigo(val_cat, val_est)
                    
                    payload = {
                        "codigo_muestra": cod,
                        "categoria": val_cat, "estilo": val_est,
                        "patronista_responsable": val_pat, "observaciones_contra": val_obs,
                        "estado": "Borrador"
                    }
                    supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                    st.session_state.codigo_actual = cod
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
