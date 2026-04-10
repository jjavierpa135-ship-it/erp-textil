import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- 2. CONEXIÓN A DB ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión: {e}"); st.stop()

# --- 3. ESTADOS DE SESIÓN ---
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0

# --- 4. FUNCIÓN DE LIMPIEZA ABSOLUTA ---
def limpiar_pantalla_total():
    """Borra toda la memoria de los componentes y resetea el formulario"""
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.form_id += 1 
    # Borrar físicamente las llaves del estado
    for key in list(st.session_state.keys()):
        if key.startswith(('c_', 'e_', 'p_', 'o_')):
            del st.session_state[key]

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
        st.button("➕ Nueva Ficha (Limpiar)", on_click=limpiar_pantalla_total)

    tab1, tab2 = st.tabs(["🎨 Diseño", "📐 Patronaje"])

    with tab1:
        # Obtenemos datos solo si NO es una ficha nueva
        es_nuevo = st.session_state.codigo_actual == "S/C"
        datos_db = {}
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data: datos_db = res.data[0]

        # Listas con opción inicial vacía para OBLIGAR a elegir
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]

        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                # Lógica: Si es nuevo, index=0 ("Seleccionar..."). Si no, busca el valor.
                idx_c = cats.index(datos_db['categoria']) if ('categoria' in datos_db and not es_nuevo) else 0
                val_cat = st.selectbox("Categoría", cats, index=idx_c, key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear)
                
                idx_e = ests.index(datos_db['estilo']) if ('estilo' in datos_db and not es_nuevo) else 0
                val_est = st.selectbox("Estilo", ests, index=idx_e, key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear)
            
            with c2:
                idx_p = pats.index(datos_db['patronista_responsable']) if ('patronista_responsable' in datos_db and not es_nuevo) else 0
                val_pat = st.selectbox("Patronista", pats, index=idx_p, key=f"p_{st.session_state.form_id}", disabled=st.session_state.bloquear)
                
                # Texto: Si es nuevo, forzamos vacío ""
                txt_previo = datos_db.get('observaciones_contra', "") if not es_nuevo else ""
                val_obs = st.text_area("Observaciones", value=txt_previo, key=f"o_{st.session_state.form_id}", disabled=st.session_state.bloquear)

            st.divider()
            
            # --- LÓGICA DE BOTONES ---
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("💾 Guardar", use_container_width=True):
                    # Validación: No dejar guardar si no han seleccionado opciones reales
                    if val_cat == "Seleccionar..." or val_est == "Seleccionar...":
                        st.error("Por favor seleccione Categoría y Estilo antes de guardar.")
                    else:
                        cod = st.session_state.codigo_actual
                        if cod == "S/C":
                            def generar_codigo(c, e):
                                return f"{c[:3].upper()}-{e[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                            cod = generar_codigo(val_cat, val_est)
                        
                        payload = {
                            "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est,
                            "patronista_responsable": val_pat, "observaciones_contra": val_obs, "estado": "Borrador"
                        }
                        supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                        st.session_state.codigo_actual = cod
                        st.session_state.bloquear = True
                        st.success(f"Guardado: {cod}")
                        st.rerun()

            with b2:
                # Solo se envía si ya está guardado y no es S/C
                if st.button("🚀 Enviar", use_container_width=True, disabled=es_nuevo):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Enviado a Patronaje.")

            with b3:
                if st.button("✏️ Editar", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()
