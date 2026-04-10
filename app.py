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
if 'confirmar_envio' not in st.session_state:
    st.session_state.confirmar_envio = False

# --- 4. FUNCIÓN DE LIMPIEZA TOTAL ---
def limpiar_pantalla_total():
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.confirmar_envio = False
    st.session_state.form_id += 1 
    # Limpiamos todas las llaves de los widgets
    for key in list(st.session_state.keys()):
        if key.startswith(('c_', 'e_', 'p_', 'o_', 'd_', 'pr_')):
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
        es_nuevo = st.session_state.codigo_actual == "S/C"
        datos_db = {}
        ya_enviado = False
        
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]
                if datos_db.get('estado') == "Pendiente Patronaje":
                    ya_enviado = True

        # Listas de opciones
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Diseñadora 1", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        with st.container():
            # FILA 1: Datos de Identificación y Trazabilidad
            c1, c2, c3 = st.columns(3)
            with c1:
                idx_d = dis_lista.index(datos_db['disenadora']) if ('disenadora' in datos_db and not es_nuevo) else 0
                val_dis = st.selectbox("Diseñadora", dis_lista, index=idx_d, key=f"d_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            with c2:
                fecha_f = datos_db.get('fecha_creacion', datetime.date.today().strftime('%Y-%m-%d'))
                st.text_input("Fecha de Creación", value=fecha_f, disabled=True)
            with c3:
                idx_pr = prioridades.index(datos_db['prioridad']) if ('prioridad' in datos_db and not es_nuevo) else 0
                val_prior = st.selectbox("Prioridad", prioridades, index=idx_pr, key=f"pr_{st.session_state.form_id}", 
                                         disabled=st.session_state.bloquear or ya_enviado)

            # FILA 2: Especificaciones Técnicas
            c4, c5, c6 = st.columns(3)
            with c4:
                idx_c = cats.index(datos_db['categoria']) if ('categoria' in datos_db and not es_nuevo) else 0
                val_cat = st.selectbox("Categoría", cats, index=idx_c, key=f"c_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            with c5:
                idx_e = ests.index(datos_db['estilo']) if ('estilo' in datos_db and not es_nuevo) else 0
                val_est = st.selectbox("Estilo", ests, index=idx_e, key=f"e_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            with c6:
                idx_p = pats.index(datos_db['patronista_responsable']) if ('patronista_responsable' in datos_db and not es_nuevo) else 0
                val_pat = st.selectbox("Patronista", pats, index=idx_p, key=f"p_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            
            val_obs = st.text_area("Observaciones Técnicas", value=datos_db.get('observaciones_contra', ""), 
                                   key=f"o_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

            st.divider()
            
            # --- LÓGICA DE BOTONES ---
            b1, b2, b3 = st.columns(3)
            
            with b1: # BOTÓN GUARDAR
                if st.button("💾 Guardar", use_container_width=True, disabled=ya_enviado):
                    if "Seleccionar..." in [val_cat, val_est, val_dis]:
                        st.error("Por favor complete todos los campos obligatorios.")
                    else:
                        cod = st.session_state.codigo_actual
                        if cod == "S/C":
                            def generar_codigo(c, e):
                                return f"{c[:3].upper()}-{e[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                            cod = generar_codigo(val_cat, val_est)
                        
                        payload = {
                            "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est,
                            "disenadora": val_dis, "prioridad": val_prior,
                            "patronista_responsable": val_pat, "observaciones_contra": val_obs, "estado": "Borrador"
                        }
                        
                        try:
                            supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                            st.session_state.codigo_actual = cod
                            st.session_state.bloquear = True
                            st.success(f"Ficha Guardada: {cod}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

            with b2: # BOTÓN ENVIAR (Con Confirmación)
                puede_enviar = not es_nuevo and st.session_state.bloquear and not ya_enviado
                
                if not st.session_state.confirmar_envio:
                    if st.button("🚀 Enviar", use_container_width=True, disabled=not puede_enviar):
                        st.session_state.confirmar_envio = True
                        st.rerun()
                else:
                    st.warning("¿Confirmar envío a patronaje?")
                    c_si, c_no = st.columns(2)
                    with c_si:
                        if st.button("✅ Sí, enviar", use_container_width=True):
                            supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                            st.session_state.confirmar_envio = False
                            st.success("Enviado con éxito.")
                            st.rerun()
                    with c_no:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state.confirmar_envio = False
                            st.rerun()
                
                if ya_enviado: st.info("✅ Ficha en Patronaje")
                elif not st.session_state.bloquear: st.caption("⚠️ Guarda cambios para enviar")

            with b3: # BOTÓN EDITAR
                if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                    st.session_state.bloquear = False
                    st.session_state.confirmar_envio = False
                    st.rerun()

    with tab2:
        st.subheader("Bandeja de Patronaje")
        st.info("Fichas en proceso de revisión...")
                
