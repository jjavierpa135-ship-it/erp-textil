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

# --- 4. FUNCIONES DE APOYO ---
def limpiar_pantalla_total():
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.confirmar_envio = False
    st.session_state.form_id += 1 
    for key in list(st.session_state.keys()):
        if key.startswith(('c_', 'e_', 'p_', 'o_', 'd_', 'pr_')):
            del st.session_state[key]

def obtener_indice(lista, valor):
    try:
        return lista.index(valor)
    except (ValueError, KeyError):
        return 0

# --- 5. CARGA INICIAL ---
if st.session_state.codigo_actual == "Cargando...":
    try:
        res = supabase.table("fichas_muestras").select("codigo_muestra").order("fecha_creacion", desc=True).limit(1).execute()
        st.session_state.codigo_actual = res.data[0]['codigo_muestra'] if res.data else "S/C"
    except:
        st.session_state.codigo_actual = "S/C"

# --- 6. INTERFAZ ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Menú", ["👗 Diseño", "📦 Almacén"])

if modulo == "👗 Diseño":
    # --- SECCIÓN DE BÚSQUEDA CON FECHA ---
    with st.expander("🔍 Buscador de Muestras", expanded=False):
        try:
            res_busqueda = supabase.table("fichas_muestras").select("codigo_muestra, estilo, estado, fecha_creacion").order("fecha_creacion", desc=True).limit(50).execute()
            
            # Formateamos: FECHA | CODIGO | ESTILO | [ESTADO]
            opciones_busqueda = ["Seleccionar..."] + [
                f"{str(r['fecha_creacion'])[:10]} | {r['codigo_muestra']} | {r['estilo']} | [{r['estado'].upper()}]" 
                for r in res_busqueda.data
            ]
            
            seleccion = st.selectbox("Escribe para filtrar:", opciones_busqueda)
            
            if seleccion != "Seleccionar...":
                nuevo_cod = seleccion.split(" | ")[1] # El código ahora es el segundo elemento
                if st.button("Abrir Ficha Seleccionada"):
                    st.session_state.codigo_actual = nuevo_cod
                    st.session_state.bloquear = True
                    st.session_state.confirmar_envio = False
                    st.rerun()
        except:
            st.warning("No se pudo cargar el historial.")

    st.divider()

    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Ficha Técnica")
    with col_c: st.metric("Muestra Activa", st.session_state.codigo_actual)
    with col_b: 
        st.button("➕ Nueva Ficha (Limpiar)", on_click=limpiar_pantalla_total, use_container_width=True)

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

        # Listas
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        with st.container():
            # FILA 1: Fechas y Diseñadora
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                idx_d = obtener_indice(dis_lista, datos_db.get('disenadora')) if not es_nuevo else 0
                val_dis = st.selectbox("Diseñadora", dis_lista, index=idx_d, key=f"d_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            with c2:
                fecha_f = datos_db.get('fecha_creacion', datetime.date.today().strftime('%Y-%m-%d'))
                st.text_input("Fecha Creación", value=str(fecha_f)[:10], disabled=True)
            with c3:
                # MOSTRAR FECHA Y HORA DE ENVÍO
                f_envio = datos_db.get('fecha_envio_patronaje')
                f_envio_str = f_envio.replace("T", " ")[:16] if f_envio else "No enviado"
                st.text_input("Fecha/Hora Envío", value=f_envio_str, disabled=True)
            with c4:
                idx_pr = obtener_indice(prioridades, datos_db.get('prioridad')) if not es_nuevo else 0
                val_prior = st.selectbox("Prioridad", prioridades, index=idx_pr, key=f"pr_{st.session_state.form_id}", 
                                         disabled=st.session_state.bloquear or ya_enviado)

            # FILA 2: Especificaciones
            c5, c6, c7 = st.columns(3)
            with c5:
                idx_c = obtener_indice(cats, datos_db.get('categoria')) if not es_nuevo else 0
                val_cat = st.selectbox("Categoría", cats, index=idx_c, key=f"c_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            with c6:
                idx_e = obtener_indice(ests, datos_db.get('estilo')) if not es_nuevo else 0
                val_est = st.selectbox("Estilo", ests, index=idx_e, key=f"e_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            with c7:
                idx_p = obtener_indice(pats, datos_db.get('patronista_responsable')) if not es_nuevo else 0
                val_pat = st.selectbox("Patronista", pats, index=idx_p, key=f"p_{st.session_state.form_id}", 
                                       disabled=st.session_state.bloquear or ya_enviado)
            
            val_obs = st.text_area("Observaciones Técnicas", value=datos_db.get('observaciones_contra', ""), 
                                   key=f"o_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

            st.divider()
            
            # BOTONES
            b1, b2, b3 = st.columns(3)
            with b1: # GUARDAR
                if st.button("💾 Guardar", use_container_width=True, disabled=ya_enviado):
                    if "Seleccionar..." in [val_cat, val_est, val_dis]:
                        st.error("Campos incompletos.")
                    else:
                        cod = st.session_state.codigo_actual
                        if cod == "S/C":
                            cod = f"{val_cat[:3].upper()}-{val_est[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                        
                        payload = {
                            "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est,
                            "disenadora": val_dis, "prioridad": val_prior,
                            "patronista_responsable": val_pat, "observaciones_contra": val_obs, "estado": "Borrador"
                        }
                        try:
                            supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                            st.session_state.codigo_actual = cod
                            st.session_state.bloquear = True
                            st.success(f"Guardado: {cod}")
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")

            with b2: # ENVIAR
                puede_enviar = not es_nuevo and st.session_state.bloquear and not ya_enviado
                if not st.session_state.confirmar_envio:
                    if st.button("🚀 Enviar", use_container_width=True, disabled=not puede_enviar):
                        st.session_state.confirmar_envio = True
                        st.rerun()
                else:
                    st.warning("¿Confirmar envío?")
                    cs, cn = st.columns(2)
                    with cs:
                        if st.button("✅ Sí", use_container_width=True):
                            # Actualizamos el estado Y la fecha de envío
                            ahora = datetime.datetime.now().isoformat()
                            supabase.table("fichas_muestras").update({
                                "estado": "Pendiente Patronaje",
                                "fecha_envio_patronaje": ahora
                            }).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                            st.session_state.confirmar_envio = False
                            st.rerun()
                    with cn:
                        if st.button("❌ No", use_container_width=True):
                            st.session_state.confirmar_envio = False
                            st.rerun()
                if ya_enviado: st.info("✅ En Patronaje")

            with b3: # EDITAR
                if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab2:
        st.subheader("Bandeja de Patronaje")
        st.info("Muestras en proceso...")
