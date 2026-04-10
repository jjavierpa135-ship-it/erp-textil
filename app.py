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
    # --- SECCIÓN DE BÚSQUEDA ---
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

        # --- ESTRUCTURA POR BLOQUES ---

        # 1. DATOS GENERALES
        with st.container(border=True):
            st.subheader("1. Datos Generales")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c2:
                val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c3:
                val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c4:
                val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key=f"pr_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

            c5, c6, c7 = st.columns([1,1,2])
            with c5:
                fecha_f = datos_db.get('fecha_creacion', datetime.date.today().strftime('%Y-%m-%d'))
                st.text_input("Fecha Creación", value=str(fecha_f)[:10], disabled=True)
            with c6:
                val_pat = st.selectbox("Patronista Asignado", pats, index=obtener_indice(pats, datos_db.get('patronista_responsable')), key=f"p_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c7:
                val_obs = st.text_area("Observaciones de Diseño", value=datos_db.get('observaciones_contra', ""), key=f"o_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado, height=68)

        # 2. TELAS E INSUMOS
        with st.container(border=True):
            st.subheader("2. Telas e Insumos")
            ci1, ci2 = st.columns(2)
            with ci1:
                val_tela1 = st.text_input("Tela Principal", value=datos_db.get('tela_1', ""), placeholder="Ej: Denim 12oz", disabled=st.session_state.bloquear or ya_enviado)
                val_tela2 = st.text_input("Tela Complemento", value=datos_db.get('tela_2', ""), placeholder="Ej: Tocuyo", disabled=st.session_state.bloquear or ya_enviado)
            with ci2:
                val_insumos = st.text_area("Insumos (Hilos, cierres, botones, etiquetas)", value=datos_db.get('insumos', ""), disabled=st.session_state.bloquear or ya_enviado, height=110)

        # 3. SERVICIOS Y LAVANDERÍA
        with st.container(border=True):
            st.subheader("3. Servicios y Lavandería")
            cs1, cs2 = st.columns(2)
            with cs1:
                val_lavado = st.text_input("Tipo de Lavado / Proceso", value=datos_db.get('color_lavado', ""), placeholder="Ej: Stone Wash + Localizado", disabled=st.session_state.bloquear or ya_enviado)
            with cs2:
                val_bordado = st.text_input("Servicios (Bordado / Estampado)", value=datos_db.get('detalles_arte', ""), placeholder="Ej: Bordado logo bolsillo posterior", disabled=st.session_state.bloquear or ya_enviado)

        # 4. FOTOS (Tallas, Corte, Diseño)
        with st.container(border=True):
            st.subheader("4. Fotos y Multimedia")
            st.caption("Suba fotos de referencia, cuadros de tallas o trazos de corte.")
            fotos_subidas = st.file_uploader("Arrastre sus archivos aquí", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)
            
            if fotos_subidas:
                cols_foto = st.columns(5)
                for i, foto in enumerate(fotos_subidas):
                    with cols_foto[i % 5]:
                        st.image(foto, caption=f"Vista previa: {foto.name}", use_container_width=True)

        st.divider()
        
        # --- BOTONES DE CONTROL ---
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Ficha", use_container_width=True, disabled=ya_enviado):
                if "Seleccionar..." in [val_cat, val_est, val_dis]:
                    st.error("Faltan datos en el Bloque 1.")
                else:
                    cod = st.session_state.codigo_actual
                    if cod == "S/C":
                        cod = f"{val_cat[:3].upper()}-{val_est[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                    
                    # Preparamos el payload con los nuevos campos
                    payload = {
                        "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est,
                        "disenadora": val_dis, "prioridad": val_prior,
                        "patronista_responsable": val_pat, "observaciones_contra": val_obs,
                        "tela_1": val_tela1, "tela_2": val_tela2, "insumos": val_insumos,
                        "color_lavado": val_lavado, "detalles_arte": val_bordado,
                        "estado": "Borrador"
                    }
                    try:
                        supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                        st.session_state.codigo_actual = cod
                        st.session_state.bloquear = True
                        st.success(f"Guardado correctamente: {cod}")
                        st.rerun()
                    except Exception as e: st.error(f"Error al guardar: {e}")

        with b2:
            puede_enviar = not es_nuevo and st.session_state.bloquear and not ya_enviado
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not puede_enviar):
                    st.session_state.confirmar_envio = True
                    st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                cs, cn = st.columns(2)
                with cs:
                    if st.button("✅ Sí", use_container_width=True):
                        ahora = datetime.datetime.now().isoformat()
                        supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": ahora}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                        st.session_state.confirmar_envio = False
                        st.rerun()
                with cn:
                    if st.button("❌ No", use_container_width=True):
                        st.session_state.confirmar_envio = False
                        st.rerun()
            if ya_enviado: st.info("✅ Ficha enviada y bloqueada.")

        with b3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False
                st.rerun()

    with tab2:
        st.subheader("Bandeja de Patronaje")
        st.info("Espacio para el cuadro de medidas y moldes.")
