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
        if key.startswith(('c_', 'e_', 'p_', 'o_', 'd_', 'pr_', 'foto_', 'tela_')):
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
    # --- BUSCADOR INTELIGENTE (TODO INCLUIDO) ---
    with st.expander("🔍 Buscador de Muestras", expanded=False):
        try:
            res_busqueda = supabase.table("fichas_muestras").select("codigo_muestra, estilo, estado, fecha_creacion").order("fecha_creacion", desc=True).limit(50).execute()
            opciones_busqueda = ["Seleccionar..."] + [
                f"{str(r['fecha_creacion'])[:10]} | {r['codigo_muestra']} | {r['estilo']} | [{r['estado'].upper()}]" 
                for r in res_busqueda.data
            ]
            seleccion = st.selectbox("Escribe para filtrar:", opciones_busqueda)
            if seleccion != "Seleccionar...":
                nuevo_cod = seleccion.split(" | ")[1]
                if st.button("Abrir Ficha Seleccionada"):
                    st.session_state.codigo_actual = nuevo_cod
                    st.session_state.bloquear = True
                    st.session_state.confirmar_envio = False
                    st.rerun()
        except: st.warning("No se pudo cargar el historial.")

    st.divider()

    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Ficha Técnica")
    with col_c: st.metric("Muestra Activa", st.session_state.codigo_actual)
    with col_b: st.button("➕ Nueva Ficha (Limpiar)", on_click=limpiar_pantalla_total, use_container_width=True)

    tab1, tab2 = st.tabs(["🎨 Diseño y Materiales", "📐 Patronaje"])

    with tab1:
        es_nuevo = st.session_state.codigo_actual == "S/C"
        datos_db = {}
        ya_enviado = False
        
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]
                ya_enviado = datos_db.get('estado') == "Pendiente Patronaje"

        # Listas de opciones
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        # BLOQUE 1: IDENTIFICACIÓN
        with st.container(border=True):
            st.subheader("1. Información General")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c2:
                fecha_f = datos_db.get('fecha_creacion', datetime.date.today().strftime('%Y-%m-%d'))
                st.text_input("Fecha Creación", value=str(fecha_f)[:10], disabled=True)
            with c3:
                f_envio = datos_db.get('fecha_envio_patronaje')
                f_envio_str = f_envio.replace("T", " ")[:16] if f_envio else "No enviado"
                st.text_input("Fecha/Hora Envío", value=f_envio_str, disabled=True)
            with c4:
                val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key=f"pr_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

        # BLOQUE 2: FOTOS CON MINIATURAS
        with st.container(border=True):
            st.subheader("2. Multimedia de Diseño")
            fotos_subidas = st.file_uploader("Subir fotos (Diseño, Bordado, etc.)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)
            if fotos_subidas:
                cols_f = st.columns(5)
                for idx, f in enumerate(fotos_subidas):
                    with cols_f[idx % 5]: st.image(f, caption=f.name, width=120)

        # BLOQUE 3: TELAS Y ARTES
        with st.container(border=True):
            st.subheader("3. Materiales y Arte")
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                val_t1 = st.text_input("Tela Principal", value=datos_db.get('tela_1', ""), disabled=st.session_state.bloquear or ya_enviado)
                val_t2 = st.text_input("Tela Complementaria", value=datos_db.get('tela_2', ""), disabled=st.session_state.bloquear or ya_enviado)
                val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), disabled=st.session_state.bloquear or ya_enviado)
                val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), disabled=st.session_state.bloquear or ya_enviado)
            with c_t2:
                val_col = st.text_input("Color / Lavado", value=datos_db.get('color_lavado', ""), disabled=st.session_state.bloquear or ya_enviado)
                val_art = st.text_area("Bordado / Estampado / Detalles", value=datos_db.get('detalles_arte', ""), disabled=st.session_state.bloquear or ya_enviado)
                val_pat = st.selectbox("Patronista Asignado", pats, index=obtener_indice(pats, datos_db.get('patronista_responsable')), disabled=st.session_state.bloquear or ya_enviado)

        st.divider()
        # BOTONES DE ACCIÓN
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                if "Seleccionar..." in [val_cat, val_est, val_dis]:
                    st.error("Completa los campos obligatorios.")
                else:
                    cod = st.session_state.codigo_actual
                    if cod == "S/C":
                        cod = f"{val_cat[:3].upper()}-{val_est[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                    
                    payload = {
                        "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est,
                        "disenadora": val_dis, "prioridad": val_prior, "patronista_responsable": val_pat,
                        "tela_1": val_t1, "tela_2": val_t2, "color_lavado": val_col, "detalles_arte": val_art,
                        "estado": "Borrador"
                    }
                    try:
                        supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                        st.session_state.codigo_actual = cod
                        st.session_state.bloquear = True
                        st.success("¡Guardado exitoso!")
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

        with b2: # ENVIAR CON CONFIRMACIÓN
            puede_env = not es_nuevo and st.session_state.bloquear and not ya_enviado
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not puede_env):
                    st.session_state.confirmar_envio = True
                    st.rerun()
            else:
                st.warning("¿Seguro de enviar? Se bloqueará la edición.")
                cs, cn = st.columns(2)
                with cs:
                    if st.button("✅ Sí, enviar"):
                        ahora = datetime.datetime.now().isoformat()
                        supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": ahora}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                        st.session_state.confirmar_envio = False
                        st.rerun()
                with cn:
                    if st.button("❌ No"):
                        st.session_state.confirmar_envio = False
                        st.rerun()
            if ya_enviado: st.info("✅ Esta ficha ya está en Patronaje.")

        with b3:
            if st.button("✏️ Editar Datos", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False
                st.rerun()

    with tab2:
        st.subheader("📏 Segunda Parte: Módulo de Patronaje")
        if not ya_enviado:
            st.info("Esperando que Diseño envíe la ficha para comenzar el patronaje.")
        else:
            st.success(f"Ficha recibida: {st.session_state.codigo_actual}. Iniciando cuadro de medidas...")
