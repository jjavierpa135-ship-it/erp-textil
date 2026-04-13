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
if 'insumos_temp' not in st.session_state:
    st.session_state.insumos_temp = []
if 'curva_dinamica' not in st.session_state:
    st.session_state.curva_dinamica = []

# --- 4. FUNCIONES DE APOYO ---
def limpiar_pantalla_total():
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.confirmar_envio = False
    st.session_state.insumos_temp = []
    st.session_state.curva_dinamica = []
    st.session_state.form_id += 1 
    for key in list(st.session_state.keys()):
        if key.startswith(('c_', 'e_', 'p_', 'o_', 'd_', 'pr_', 'curva_', 'add_', 'tmp_')):
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
    with st.expander("🔍 Buscador de Muestras", expanded=False):
        try:
            res_busqueda = supabase.table("fichas_muestras").select("codigo_muestra, estilo, estado, fecha_creacion").order("fecha_creacion", desc=True).limit(50).execute()
            opciones_busqueda = ["Seleccionar..."] + [
                f"{str(r['fecha_creacion'])[:10]} | {r['codigo_muestra']} | {r['estilo']} | [{r['estado'].upper()}]" 
                for r in res_busqueda.data
            ]
            seleccion = st.selectbox("Filtrar:", opciones_busqueda)
            if seleccion != "Seleccionar...":
                nuevo_cod = seleccion.split(" | ")[1]
                if st.button("Abrir Ficha"):
                    st.session_state.codigo_actual = nuevo_cod
                    st.session_state.bloquear = True
                    st.session_state.curva_dinamica = [] # Reset para forzar recarga
                    st.rerun()
        except: st.warning("No se pudo cargar el historial.")

    st.divider()

    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Ficha Técnica")
    with col_c: st.metric("Muestra Activa", st.session_state.codigo_actual)
    with col_b: st.button("➕ Nueva Ficha", on_click=limpiar_pantalla_total, use_container_width=True)

    tab1, tab2 = st.tabs(["🎨 Ficha de Diseño", "📐 Patronaje"])

    with tab1:
        es_nuevo = st.session_state.codigo_actual == "S/C"
        datos_db = {}
        ya_enviado = False
        
        # --- CARGA Y SINCRONIZACIÓN DE CONSULTA ---
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]
                ya_enviado = datos_db.get('estado') == "Pendiente Patronaje"
                # Sincronizar tallas al estado de la sesión si están vacías
                if not st.session_state.curva_dinamica:
                    st.session_state.curva_dinamica = datos_db.get('curva_tallas', [])

        # --- SECCIONES DE FORMA (SIN CAMBIOS) ---
        with st.container(border=True):
            st.subheader("1. Datos de Cabecera")
            col_f1, col_f2 = st.columns([3, 1])
            with col_f1:
                c1, c2, c3, c4 = st.columns(4)
                dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2"]
                cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa"]
                with c1: val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), disabled=st.session_state.bloquear)
                with c2: val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), disabled=st.session_state.bloquear)
                with c3: val_est = st.text_input("Estilo", value=datos_db.get('estilo', ""), disabled=st.session_state.bloquear)
                with c4: val_prior = st.selectbox("Prioridad", ["Normal", "Urgente"], index=obtener_indice(["Normal", "Urgente"], datos_db.get('prioridad')), disabled=st.session_state.bloquear)
            with col_f2:
                st.info("Espacio para Foto")
                st.image("https://via.placeholder.com/150", caption="Vista Previa")

        with st.container(border=True):
            st.subheader("2. Especificaciones y 3. Insumos")
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                val_desc = st.text_area("Descripción", value=datos_db.get('desc_prenda', ""), disabled=st.session_state.bloquear)
            with col_e2:
                val_t1 = st.text_input("Tela Principal", value=datos_db.get('tela_1', ""), disabled=st.session_state.bloquear)

        # --- MEJORA ESPECÍFICA EN SECCIÓN 5 (CONSULTA) ---
        with st.container(border=True):
            st.subheader("5. Tallas y Planificación de Corte")
            
            # Aseguramos que sea una lista
            if not isinstance(st.session_state.curva_dinamica, list):
                st.session_state.curva_dinamica = []

            # Solo mostrar input si no está bloqueado
            if not st.session_state.bloquear and not ya_enviado:
                ci1, ci2, ci3 = st.columns([2, 2, 1])
                t_new = ci1.selectbox("Talla", ["26", "28", "30", "32", "34", "S", "M", "L"], key="nt")
                c_new = ci2.number_input("Cantidad", min_value=1, value=1, key="nc")
                if ci3.button("Añadir"):
                    st.session_state.curva_dinamica.append({"talla": t_new, "cantidad": c_new})
                    st.rerun()

            # Renderizado de la consulta de tallas
            if st.session_state.curva_dinamica:
                # Sumar tizado para cálculos
                suma_tizado = sum(int(i['cantidad']) for i in st.session_state.curva_dinamica)
                cant_paq = int(datos_db.get('cantidad_paquetes', suma_tizado))
                
                # Mostrar Tabla
                cols = st.columns(len(st.session_state.curva_dinamica) if len(st.session_state.curva_dinamica) > 0 else 1)
                for idx, item in enumerate(st.session_state.curva_dinamica):
                    with cols[idx]:
                        st.metric(f"Talla {item['talla']}", f"{item['cantidad']} pzs")
                        if not st.session_state.bloquear:
                            if st.button("❌", key=f"del_{idx}"):
                                st.session_state.curva_dinamica.pop(idx)
                                st.rerun()
                
                st.write(f"**Total Tizado:** {suma_tizado} pzs | **Total Pedido:** {cant_paq} pzs")
            else:
                st.warning("No hay tallas registradas.")

        # --- BOTONES (SIN CAMBIOS) ---
        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar", use_container_width=True):
                payload = {
                    "codigo_muestra": st.session_state.codigo_actual,
                    "curva_tallas": st.session_state.curva_dinamica,
                    "estilo": val_est, "categoria": val_cat, "disenadora": val_dis
                }
                supabase.table("fichas_muestras").upsert(payload).execute()
                st.success("Guardado"); st.rerun()
        with b2:
            st.button("🚀 Enviar", use_container_width=True, disabled=st.session_state.bloquear)
        with b3:
            if st.button("✏️ Editar", use_container_width=True):
                st.session_state.bloquear = False; st.rerun()
