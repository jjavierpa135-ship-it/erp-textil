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

# --- 3. GESTIÓN DE ESTADOS CRÍTICOS ---
# Usamos un interruptor 'cargado_inicial' para que solo busque en la DB UNA VEZ al abrir la app.
if 'cargado_inicial' not in st.session_state:
    st.session_state.cargado_inicial = False
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "S/C"
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    marca = datetime.datetime.now().strftime('%y%m%d%H%M')
    return f"{prefijo}-{marca}"

def nueva_ficha():
    # Limpieza absoluta
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.cambios_sin_guardar = False
    st.session_state.cargado_inicial = True # Marcamos como cargado para que no busque la última de nuevo
    st.session_state.form_id += 1 # Cambia la identidad de los widgets
    st.rerun()

# --- 5. LÓGICA DE CARGA AL INICIAR (Solo si no se ha forzado una Nueva Ficha) ---
if not st.session_state.cargado_inicial:
    try:
        res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
        if res.data:
            st.session_state.codigo_actual = res.data[0]['codigo_muestra']
        st.session_state.cargado_inicial = True
    except:
        st.session_state.codigo_actual = "S/C"
        st.session_state.cargado_inicial = True

# --- 6. BARRA LATERAL ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Navegación", ["👗 Diseño y Patronaje", "📦 Almacén"])

if modulo == "👗 Diseño y Patronaje":
    
    # Cabecera
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Gestión de Muestras")
    with col_c: st.metric("Código Activo", st.session_state.codigo_actual)
    with col_b: 
        if st.button("➕ Nueva Ficha (Limpiar)"):
            nueva_ficha()

    tab_diseno, tab_patronaje = st.tabs(["🎨 Área de Diseño", "📐 Área de Patronaje"])

    with tab_diseno:
        # Recuperación de datos: SI EL CÓDIGO ES S/C, NO SE BUSCA NADA.
        datos_f = {}
        if st.session_state.codigo_actual != "S/C":
            res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res_ficha.data:
                datos_f = res_ficha.data[0]

        # Listas de opciones fijas
        cat_lista = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        est_lista = ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pat_lista = ["Patronista 1", "Patronista 2", "Patronista 3"]

        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                # La lógica del índice: si no hay datos_f (Ficha Nueva), el índice es 0.
                idx_cat = cat_lista.index(datos_f['categoria']) if 'categoria' in datos_f else 0
                cat = st.selectbox("Categoría", cat_lista, index=idx_cat, 
                                   key=f"cat_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear,
                                   on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
                
                idx_est = est_lista.index(datos_f['estilo']) if 'estilo' in datos_f else 0
                estilo = st.selectbox("Estilo / Fit", est_lista, index=idx_est, 
                                      key=f"est_{st.session_state.form_id}",
                                      disabled=st.session_state.bloquear,
                                      on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
            
            with c2:
                idx_pat = pat_lista.index(datos_f['patronista_responsable']) if 'patronista_responsable' in datos_f else 0
                patronista = st.selectbox("Asignar a Patronista", pat_lista, index=idx_pat, 
                                          key=f"pat_{st.session_state.form_id}",
                                          disabled=st.session_state.bloquear,
                                          on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))
                
                val_obs = datos_f.get('observaciones_contra', "")
                obs = st.text_area("Notas Técnicas", value=val_obs, 
                                   key=f"obs_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear,
                                   on_change=lambda: st.session_state.update({"cambios_sin_guardar": True}))

            st.markdown("---")
            
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
                    st.success(f"Guardado exitoso: {st.session_state.codigo_actual}")
                    st.rerun()

            with b2:
                bloqueo_envio = st.session_state.cambios_sin_guardar or st.session_state.codigo_actual == "S/C"
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=bloqueo_envio):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Ficha enviada a bandeja de patronista.")

            with b3:
                if st.button("✏️ Habilitar Edición", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab_patronaje:
        st.subheader("Bandeja de Entrada Patronaje")
        # (Lógica de patronaje aquí...)
