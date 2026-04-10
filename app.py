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

# --- 4. FUNCIONES DE APOYO ---
def limpiar_pantalla_total():
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.confirmar_envio = False
    st.session_state.insumos_temp = []
    st.session_state.form_id += 1 
    for key in list(st.session_state.keys()):
        if key.startswith(('c_', 'e_', 'p_', 'o_', 'd_', 'pr_', 'curva_')):
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
    # BUSCADOR
    with st.expander("🔍 Buscador de Muestras", expanded=False):
        try:
            res_busqueda = supabase.table("fichas_muestras").select("codigo_muestra, estilo, estado, fecha_creacion").order("fecha_creacion", desc=True).limit(50).execute()
            opciones = ["Seleccionar..."] + [f"{str(r['fecha_creacion'])[:10]} | {r['codigo_muestra']} | {r['estilo']}" for r in res_busqueda.data]
            seleccion = st.selectbox("Buscar:", opciones)
            if seleccion != "Seleccionar..." and st.button("Abrir Ficha"):
                st.session_state.codigo_actual = seleccion.split(" | ")[1]
                st.session_state.bloquear = True
                st.rerun()
        except: st.warning("Historial no disponible.")

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
        
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]
                ya_enviado = datos_db.get('estado') == "Pendiente Patronaje"
                # Cargar insumos de la DB al estado temporal si es la primera vez que se abre la ficha
                if not st.session_state.insumos_temp and 'insumos_detalle' in datos_db:
                    st.session_state.insumos_temp = datos_db['insumos_detalle'] or []

        # Listas de Selección
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2"]
        cats = ["Seleccionar...", "Pantalón", "Falda", "Casaca"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize"]
        telas_lista = ["Seleccionar...", "Denim 12oz", "Gabardina", "Tocuyo"]

        # BLOQUE 1: CABECERA
        with st.container(border=True):
            st.subheader("1. Datos de Cabecera")
            c1, c2, c3 = st.columns(3)
            with c1: val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear)
            with c2: val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear)
            with c3: val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear)

        # BLOQUE 2: DISEÑO
        with st.container(border=True):
            st.subheader("2. Especificaciones de Diseño")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                val_desc = st.text_area("Descripción de Prenda", value=datos_db.get('desc_prenda', ""), disabled=st.session_state.bloquear)
                val_ent = st.text_input("Ref. Entalle", value=datos_db.get('ref_entalle', ""), disabled=st.session_state.bloquear)
            with col_d2:
                val_obs = st.text_area("Observaciones Diseño", value=datos_db.get('observaciones_contra', ""), disabled=st.session_state.bloquear)
                val_mol = st.text_input("Obs. Molde", value=datos_db.get('obs_molde', ""), disabled=st.session_state.bloquear)

        # BLOQUE 3: TELAS E INSUMOS (EL MEJORADO)
        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            ct1, ct2 = st.columns(2)
            with ct1: val_t1 = st.selectbox("Tela Principal", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_1')), disabled=st.session_state.bloquear)
            with ct2: val_t2 = st.selectbox("Tela Complemento", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_2')), disabled=st.session_state.bloquear)
            
            st.markdown("---")
            st.markdown("**Listado de Insumos**")
            
            # Tabla de insumos cargados
            if st.session_state.insumos_temp:
                cols_h = st.columns([2, 1, 1, 1, 1, 0.5])
                cols_h[0].caption("Código/Nombre")
                cols_h[1].caption("Color")
                cols_h[2].caption("Diseño")
                cols_h[3].caption("Tamaño")
                cols_h[4].caption("Cant.")
                
                for idx, item in enumerate(st.session_state.insumos_temp):
                    r = st.columns([2, 1, 1, 1, 1, 0.5])
                    r[0].write(item['codigo'])
                    r[1].write(item['color'])
                    r[2].write(item['diseno'])
                    r[3].write(item['tamano'])
                    r[4].write(str(item['cantidad']))
                    if not st.session_state.bloquear and r[5].button("🗑️", key=f"del_{idx}"):
                        st.session_state.insumos_temp.pop(idx)
                        st.rerun()

            # Formulario para agregar insumo
            if not st.session_state.bloquear:
                with st.expander("➕ Agregar Nuevo Insumo", expanded=False):
                    f1, f2, f3 = st.columns(3)
                    f4, f5, f6 = st.columns([1, 1, 1])
                    i_cod = f1.text_input("Código/Nombre")
                    i_col = f2.text_input("Color")
                    i_dis = f3.text_input("Diseño")
                    i_tam = f4.text_input("Tamaño")
                    i_can = f5.number_input("Cantidad", min_value=0.0)
                    if f6.button("✅ Añadir Insumo", use_container_width=True):
                        if i_cod:
                            st.session_state.insumos_temp.append({"codigo": i_cod, "color": i_col, "diseno": i_dis, "tamano": i_tam, "cantidad": i_can})
                            st.rerun()

        # BLOQUE 5: CORTE Y TALLAS
        with st.container(border=True):
            st.subheader("5. Tallas y Corte")
            t_lista = ["26", "28", "30", "32", "34", "36"]
            c_t = st.columns(len(t_lista) + 1)
            curva = {}
            db_curva = datos_db.get('curva_tallas', {}) or {}
            
            with c_t[0]: st.write("Talla")
            for i, t in enumerate(t_lista):
                with c_t[i+1]: 
                    st.write(f"**{t}**")
                    curva[t] = st.number_input(f"v_{t}", min_value=0, value=int(db_curva.get(t, 0)), label_visibility="collapsed")
            
            st.divider()
            cc1, cc2 = st.columns([1, 2])
            with cc1: val_paq = st.number_input("Paquetes", min_value=1, value=int(datos_db.get('cantidad_paquetes', 1)), disabled=st.session_state.bloquear)
            with cc2:
                total = sum(curva.values()) * val_paq
                st.metric("TOTAL PRENDAS", total)

        # BLOQUE 6: FOTOS
        with st.container(border=True):
            st.subheader("6. Fotos")
            st.file_uploader("Subir", accept_multiple_files=True, disabled=st.session_state.bloquear)

        st.divider()
        # BOTONES DE ACCIÓN
        ba1, ba2, ba3 = st.columns(3)
        with ba1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                cod = st.session_state.codigo_actual
                if cod == "S/C": cod = f"{val_cat[:3].upper()}-{datetime.datetime.now().strftime('%M%S')}"
                payload = {
                    "codigo_muestra": cod, "disenadora": val_dis, "categoria": val_cat, "estilo": val_est,
                    "desc_prenda": val_desc, "ref_entalle": val_ent, "observaciones_contra": val_obs, "obs_molde": val_mol,
                    "tela_1": val_t1, "tela_2": val_t2, "insumos_detalle": st.session_state.insumos_temp,
                    "curva_tallas": curva, "cantidad_paquetes": val_paq, "estado": "Borrador"
                }
                try:
                    supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                    st.session_state.codigo_actual = cod
                    st.session_state.bloquear = True
                    st.success("¡Guardado!")
                    st.rerun()
                except Exception as e: st.error(f"Error DB: {e}")

        with ba2:
            if st.button("🚀 Enviar", use_container_width=True, disabled=es_nuevo or ya_enviado):
                supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                st.rerun()
        
        with ba3:
            if st.button("✏️ Editar", use_container_width=True):
                st.session_state.bloquear = False
                st.rerun()

    with tab2:
        st.info("Módulo de Patronaje en desarrollo...")
