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

def nueva_ficha_callback():
    """Esta función limpia todo ANTES de que Streamlit dibuje la pantalla"""
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.cambios_sin_guardar = False
    st.session_state.form_id += 1 
    # Limpieza profunda de llaves para evitar el mensaje amarillo
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith(('c_', 'e_', 'p_', 'o_'))]
    for k in keys_to_delete:
        del st.session_state[k]

# --- 5. CARGA INICIAL ---
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
        # El callback evita el error amarillo de modificación durante el renderizado
        st.button("➕ Nueva Ficha (Limpiar)", on_click=nueva_ficha_callback)

    tab1, tab2 = st.tabs(["🎨 Diseño", "📐 Patronaje"])

    with tab1:
        # Recuperación de datos
        datos = {}
        if st.session_state.codigo_actual != "S/C":
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data: datos = res.data[0]

        # Listas
        cats = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Patronista 1", "Patronista 2", "Patronista 3"]

        # FORMULARIO
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                # Si el código es S/C, ignoramos cualquier dato previo
                idx_cat = cats.index(datos['categoria']) if ('categoria' in datos and st.session_state.codigo_actual != "S/C") else 0
                val_cat = st.selectbox("Categoría", cats, index=idx_cat, 
                                      disabled=st.session_state.bloquear,
                                      key=f"c_{st.session_state.form_id}")
                
                idx_est = ests.index(datos['estilo']) if ('estilo' in datos and st.session_state.codigo_actual != "S/C") else 0
                val_est = st.selectbox("Estilo", ests, index=idx_est, 
                                      disabled=st.session_state.bloquear,
                                      key=f"e_{st.session_state.form_id}")
            
            with c2:
                idx_pat = pats.index(datos['patronista_responsable']) if ('patronista_responsable' in datos and st.session_state.codigo_actual != "S/C") else 0
                val_pat = st.selectbox("Patronista", pats, index=idx_pat, 
                                      disabled=st.session_state.bloquear,
                                      key=f"p_{st.session_state.form_id}")
                
                txt_obs = datos.get('observaciones_contra', "") if st.session_state.codigo_actual != "S/C" else ""
                val_obs = st.text_area("Observaciones", value=txt_obs, 
                                      disabled=st.session_state.bloquear,
                                      key=f"o_{st.session_state.form_id}")

            # Detección de cambios manual para evitar el warning amarillo de on_change
            if not st.session_state.bloquear and st.session_state.codigo_actual != "S/C":
                # Si los valores actuales son diferentes a los guardados, hay cambios
                if val_cat != datos.get('categoria') or val_est != datos.get('estilo') or val_obs != datos.get('observaciones_contra'):
                    st.session_state.cambios_sin_guardar = True

            st.divider()
            
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("💾 Guardar", use_container_width=True):
                    cod_final = st.session_state.codigo_actual
                    if cod_final == "S/C":
                        cod_final = generar_codigo(val_cat, val_est)
                    
                    payload = {
                        "codigo_muestra": cod_final,
                        "categoria": val_cat, "estilo": val_est,
                        "patronista_responsable": val_pat, "observaciones_contra": val_obs,
                        "estado": "Borrador"
                    }
                    supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                    st.session_state.codigo_actual = cod_final
                    st.session_state.bloquear = True
                    st.session_state.cambios_sin_guardar = False
                    st.success("¡Guardado correctamente!")
                    st.rerun()

            with b2:
                # El botón enviar solo se activa si no hay cambios pendientes
                can_send = not st.session_state.cambios_sin_guardar and st.session_state.codigo_actual != "S/C"
                if st.button("🚀 Enviar", use_container_width=True, disabled=not can_send):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Enviado a Patronaje.")
                if st.session_state.cambios_sin_guardar:
                    st.caption("⚠️ Debes guardar los cambios primero.")

            with b3:
                if st.button("✏️ Editar", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab2:
        st.write("Bandeja de Patronaje...")
