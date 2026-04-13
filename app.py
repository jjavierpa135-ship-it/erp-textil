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

# --- 3. ESTADOS DE SESIÓN (Inicialización Robusta) ---
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
if 'curva_dinamica' not in st.session_state or st.session_state.curva_dinamica is None:
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
                    st.session_state.confirmar_envio = False
                    st.session_state.insumos_temp = [] 
                    st.session_state.curva_dinamica = [] 
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
        
        if not es_nuevo:
            res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            if res.data:
                datos_db = res.data[0]
                ya_enviado = datos_db.get('estado') == "Pendiente Patronaje"
                
                # Sincronización de Insumos
                if not st.session_state.insumos_temp and datos_db.get('insumos_detalle'):
                    st.session_state.insumos_temp = datos_db.get('insumos_detalle')
                
                # Sincronización de Tallas (Verificando que sea lista)
                if not st.session_state.curva_dinamica:
                    val_tallas = datos_db.get('curva_tallas')
                    if isinstance(val_tallas, list):
                        st.session_state.curva_dinamica = val_tallas

        # Listas de opciones
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        # 1. Datos de Cabecera
        with st.container(border=True):
            st.subheader("1. Datos de Cabecera")
            c1, c2, c3, c4 = st.columns(4)
            with c1: val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c2: val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c3: val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c4: val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key=f"pr_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

        # 2. Especificaciones
        with st.container(border=True):
            st.subheader("2. Especificaciones de Diseño")
            cd1, cd2 = st.columns(2)
            with cd1:
                val_desc = st.text_area("Descripción de la Prenda", value=datos_db.get('desc_prenda', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
                val_entalle = st.text_input("Referencia de Entalle", value=datos_db.get('ref_entalle', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cd2:
                val_obs_dis = st.text_area("Observaciones de Diseño", value=datos_db.get('observaciones_contra', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
                val_rec = st.text_area("Recomendaciones", value=datos_db.get('rec_observaciones', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)

        # 5. Tallas y Planificación (SECCIÓN CORREGIDA)
        with st.container(border=True):
            st.subheader("5. Tallas y Planificación de Corte")
            
            # Asegurar que siempre sea lista para evitar AttributeError: 'NoneType'
            if st.session_state.curva_dinamica is None:
                st.session_state.curva_dinamica = []

            # Agregar Tallas
            if not st.session_state.bloquear and not ya_enviado:
                c1, c2, c3 = st.columns([2, 2, 1])
                t_ops = ["Seleccionar...", "26", "28", "30", "32", "34", "36", "S", "M", "L", "XL"]
                t_sel = c1.selectbox("Talla", t_ops, key="selector_talla_final")
                r_val = c2.number_input("Piezas en Tizado", min_value=1, step=1, key="ratio_final")
                
                if c3.button("➕ Añadir"):
                    if t_sel != "Seleccionar...":
                        # Validar si ya existe
                        actuales = [str(item.get('talla')) for item in st.session_state.curva_dinamica if isinstance(item, dict)]
                        if t_sel not in actuales:
                            st.session_state.curva_dinamica.append({"talla": t_sel, "cantidad": r_val})
                            st.rerun()

            # Cálculos de Capas
            # Usamos una validación interna para evitar ZeroDivisionError
            suma_tizado = sum(int(i.get('cantidad', 0)) for i in st.session_state.curva_dinamica if isinstance(i, dict))
            
            if suma_tizado > 0:
                st.divider()
                cant_pedida = st.number_input("¿Cantidad total de prendas?", min_value=1, 
                                              value=max(suma_tizado, int(datos_db.get('cantidad_paquetes', suma_tizado))), 
                                              disabled=st.session_state.bloquear or ya_enviado)

                n_capas = (cant_pedida + suma_tizado - 1) // suma_tizado
                total_real = n_capas * suma_tizado
                
                # Mostrar Tabla
                cols = st.columns([2, 2, 2, 0.5])
                cols[0].caption("TALLA"); cols[1].caption("TIZADO"); cols[2].caption("TOTAL")
                
                for idx, item in enumerate(st.session_state.curva_dinamica):
                    if isinstance(item, dict):
                        f = st.columns([2, 2, 2, 0.5])
                        f[0].write(item['talla'])
                        f[1].write(f"{item['cantidad']} pzs")
                        f[2].info(f"{int(item['cantidad']) * n_capas} und.")
                        if not st.session_state.bloquear and not ya_enviado:
                            if f[3].button("🗑️", key=f"del_{idx}"):
                                st.session_state.curva_dinamica.pop(idx)
                                st.rerun()
                st.metric("Total a cortar", f"{total_real} prendas")
            else:
                st.info("Agregue al menos una talla para definir la cantidad.")
                total_real = 0

        # Botones de Acción
        st.divider()
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                cod_id = st.session_state.codigo_actual if st.session_state.codigo_actual != "S/C" else f"M-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                payload = {
                    "codigo_muestra": cod_id,
                    "categoria": val_cat, "estilo": val_est, "disenadora": val_dis, "prioridad": val_prior,
                    "curva_tallas": st.session_state.curva_dinamica,
                    "cantidad_paquetes": total_real, "estado": "Borrador"
                }
                supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                st.session_state.codigo_actual = cod_id
                st.session_state.bloquear = True
                st.success("Guardado correctamente"); st.rerun()

        with col_btn2:
            puede_enviar = st.session_state.bloquear and st.session_state.codigo_actual != "S/C" and not ya_enviado
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not puede_enviar):
                    st.session_state.confirmar_envio = True; st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                cs = st.columns(2)
                if cs[0].button("✅ Sí"):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": datetime.datetime.now().isoformat()}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.session_state.confirmar_envio = False; st.rerun()
                if cs[1].button("❌ No"):
                    st.session_state.confirmar_envio = False; st.rerun()

        with col_btn3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False; st.rerun()
