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
    # --- BUSCADOR ---
    with st.expander("🔍 Buscador de Muestras", expanded=False):
        try:
            res_busqueda = supabase.table("fichas_muestras").select("codigo_muestra, estilo, estado, fecha_creacion").order("fecha_creacion", desc=True).limit(50).execute()
            opciones_busqueda = ["Seleccionar..."] + [f"{str(r['fecha_creacion'])[:10]} | {r['codigo_muestra']} | {r['estilo']} | [{r['estado'].upper()}]" for r in res_busqueda.data]
            seleccion = st.selectbox("Filtrar:", opciones_busqueda)
            if seleccion != "Seleccionar...":
                nuevo_cod = seleccion.split(" | ")[1]
                if st.button("Abrir Ficha"):
                    st.session_state.codigo_actual = nuevo_cod
                    st.session_state.bloquear = True
                    st.rerun()
        except: pass

    st.divider()

    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Ficha Técnica")
    with col_c: st.metric("Muestra Activa", st.session_state.codigo_actual)
    with col_b: st.button("➕ Nueva Ficha", on_click=limpiar_pantalla_total, use_container_width=True)

    tab1, tab2 = st.tabs(["🎨 Diseño / Materiales", "📐 Patronaje"])

    with tab1:
        es_nuevo = st.session_state.codigo_actual == "S/C"
        datos_db = {}
        ya_enviado = False
        
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]
                ya_enviado = datos_db.get('estado') == "Pendiente Patronaje"

        # Listas de opciones básicas
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]

        # --- BLOQUE 1: IDENTIFICACIÓN (CONGELADO SI SE ENVÍA) ---
        with st.container(border=True):
            st.subheader("1. Identificación y Estado")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key="d_1", disabled=st.session_state.bloquear or ya_enviado)
            with c2:
                st.text_input("Fecha Creación", value=str(datos_db.get('fecha_creacion', datetime.date.today()))[:10], disabled=True)
            with c3:
                f_envio = datos_db.get('fecha_envio_patronaje', "No enviado").replace("T", " ")[:16]
                st.text_input("Fecha/Hora Envío", value=f_envio, disabled=True)
            with c4:
                val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key="pr_1", disabled=st.session_state.bloquear or ya_enviado)

        # --- BLOQUE 2: MATERIALES Y MULTIMEDIA (NUEVO) ---
        with st.container(border=True):
            st.subheader("2. Fotos de Diseño y Detalles")
            st.info("Puedes subir varias fotos (Diseño, Bordado, Avíos, etc.)")
            
            # Subida de múltiples fotos con miniatura
            fotos_subidas = st.file_uploader("Cargar Fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)
            
            if fotos_subidas:
                cols_fotos = st.columns(4)
                for i, foto in enumerate(fotos_subidas):
                    with cols_fotos[i % 4]:
                        st.image(foto, caption=f"Miniatura: {foto.name}", width=150)

        with st.container(border=True):
            st.subheader("3. Especificaciones de Telas y Color")
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                st.markdown("**Telas Principales y Complementos**")
                # Aquí simulamos la entrada de múltiples telas
                tela_1 = st.text_input("Tela 1 (Principal)", value=datos_db.get('tela_1', ""), disabled=st.session_state.bloquear or ya_enviado)
                tela_2 = st.text_input("Tela 2 (Complemento)", value=datos_db.get('tela_2', ""), disabled=st.session_state.bloquear or ya_enviado)
                # Espacio para más si es necesario
                with st.expander("Agregar más telas..."):
                    tela_extra = st.text_area("Otras telas y composiciones", disabled=st.session_state.bloquear or ya_enviado)
            
            with c_t2:
                st.markdown("**Arte (Bordado / Estampado / Color)**")
                color_det = st.text_input("Color / Lavado", value=datos_db.get('color_lavado', ""), disabled=st.session_state.bloquear or ya_enviado)
                arte_det = st.text_area("Detalles de Bordado o Aplicaciones", value=datos_db.get('detalles_arte', ""), disabled=st.session_state.bloquear or ya_enviado)

        # --- BOTONES DE ACCIÓN ---
        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Cambios", use_container_width=True, disabled=ya_enviado):
                # Aquí iría el upsert con los nuevos campos tela_1, tela_2, etc.
                st.success("Información guardada temporalmente.")
        
        with b2:
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=st.session_state.bloquear or ya_enviado):
                    st.session_state.confirmar_envio = True
                    st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                cs, cn = st.columns(2)
                with cs:
                    if st.button("✅ Confirmar"):
                        ahora = datetime.datetime.now().isoformat()
                        supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": ahora}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                        st.session_state.confirmar_envio = False
                        st.rerun()
                with cn:
                    if st.button("❌ Cancelar"):
                        st.session_state.confirmar_envio = False
                        st.rerun()

        with b3:
            if st.button("✏️ Editar Ficha", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False
                st.rerun()

    with tab2:
        st.subheader("📏 Módulo de Patronista")
        if not ya_enviado:
            st.warning("Esta ficha aún no ha sido enviada por Diseño.")
        else:
            st.success(f"Trabajando sobre la Muestra: {st.session_state.codigo_actual}")
            # Aquí empezaremos a construir el cuadro de medidas, etc.
