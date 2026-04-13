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
        if key.startswith(('c_', 'e_', 'p_', 'o_', 'd_', 'pr_', 'curva_', 'add_', 'input_')):
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
                    st.session_state.curva_dinamica = [] # Forzamos recarga de tallas
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
                # Cargar insumos de DB
                if not st.session_state.insumos_temp and datos_db.get('insumos_detalle'):
                    st.session_state.insumos_temp = datos_db.get('insumos_detalle')
                # Cargar tallas dinámicas de DB
                if not st.session_state.curva_dinamica and datos_db.get('curva_tallas'):
                    db_curva = datos_db.get('curva_tallas')
                    if isinstance(db_curva, dict): # Soporte para formato antiguo
                        st.session_state.curva_dinamica = [{"talla": k, "cantidad": v} for k, v in db_curva.items()]
                    else:
                        st.session_state.curva_dinamica = db_curva

        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        # 1. DATOS GENERALES
        with st.container(border=True):
            st.subheader("1. Datos de Cabecera")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c2:
                val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c3:
                val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c4:
                val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key=f"pr_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

            c5, c6, c7 = st.columns(3)
            with c5:
                fecha_f = datos_db.get('fecha_creacion', datetime.date.today().strftime('%Y-%m-%d'))
                st.text_input("Fecha Creación", value=str(fecha_f)[:10], disabled=True)
            with c6:
                val_pat = st.selectbox("Patronista Asignado", pats, index=obtener_indice(pats, datos_db.get('patronista_responsable')), key=f"p_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c7:
                f_envio = datos_db.get('fecha_envio_patronaje', "No enviado")
                st.text_input("Fecha/Hora Envío", value=str(f_envio).replace("T", " ")[:16], disabled=True)

        # 2. ESPECIFICACIONES
        with st.container(border=True):
            st.subheader("2. Especificaciones de Diseño")
            cd1, cd2 = st.columns(2)
            with cd1:
                val_desc = st.text_area("Descripción de la Prenda", value=datos_db.get('desc_prenda', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
                val_entalle = st.text_input("Referencia de Entalle", value=datos_db.get('ref_entalle', ""), disabled=st.session_state.bloquear or ya_enviado)
                val_proc = st.text_input("Procesos Auxiliares", value=datos_db.get('procesos_aux', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cd2:
                val_obs_dis = st.text_area("Observaciones de Diseño", value=datos_db.get('observaciones_contra', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
                val_rec = st.text_area("Recomendaciones y Observaciones", value=datos_db.get('rec_observaciones', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
            val_obs_molde = st.text_input("Observaciones de Molde", value=datos_db.get('obs_molde', ""), disabled=st.session_state.bloquear or ya_enviado)

        # 3. TELAS E INSUMOS
        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            telas_lista = ["Seleccionar...", "Denim 12oz", "Denim 10oz", "Gabardina", "Jersey", "Tocuyo"]
            ci1, ci2 = st.columns(2)
            with ci1:
                val_t1 = st.selectbox("Tela Principal", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_1')), disabled=st.session_state.bloquear or ya_enviado)
            with ci2:
                val_t2 = st.selectbox("Tela Complemento", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_2')), disabled=st.session_state.bloquear or ya_enviado)
            
            st.divider()
            st.markdown("**Detalle de Insumos desde Almacén**")

            try:
                res_mats = supabase.table("almacen_insumos").select("nombre, precio_unitario").execute()
                opciones_mats = [m['nombre'] for m in res_mats.data] if res_mats.data else []
                precios_mats = {m['nombre']: m['precio_unitario'] for m in res_mats.data} if res_mats.data else {}
            except: opciones_mats, precios_mats = [], {}

            h = st.columns([2, 1, 1, 1, 0.5])
            h[0].caption("Material"); h[1].caption("Cant."); h[2].caption("Precio U."); h[3].caption("Subtotal"); h[4].caption("")

            total_insumos = 0.0
            for idx, item in enumerate(st.session_state.insumos_temp):
                r = st.columns([2, 1, 1, 1, 0.5])
                p_unit = item.get('precio', 0.0)
                sub = item.get('cantidad', 0) * p_unit
                total_insumos += sub
                r[0].write(item.get('codigo'))
                r[1].write(str(item.get('cantidad')))
                r[2].write(f"${p_unit:.2f}")
                r[3].write(f"${sub:.2f}")
                if not st.session_state.bloquear and not ya_enviado:
                    if r[4].button("🗑️", key=f"del_ins_{idx}"):
                        st.session_state.insumos_temp.pop(idx); st.rerun()

            st.divider()
            st.columns([2,1])[1].metric("COSTO TOTAL INSUMOS", f"${total_insumos:.2f}")

            if not st.session_state.bloquear and not ya_enviado:
                with st.expander("➕ Añadir Material de Almacén"):
                    f1, f2, f3 = st.columns([2, 1, 1])
                    insumo_nom = f1.selectbox("Seleccionar Insumo", ["Buscar..."] + opciones_mats, key="sel_ins_bus")
                    insumo_cant = f2.number_input("Cantidad", min_value=0.0, key="num_ins_can")
                    if f3.button("Agregar a Ficha"):
                        if insumo_nom != "Buscar..." and insumo_cant > 0:
                            st.session_state.insumos_temp.append({"codigo": insumo_nom, "cantidad": insumo_cant, "precio": precios_mats.get(insumo_nom, 0.0)})
                            st.rerun()

        # 4. SERVICIOS
        with st.container(border=True):
            st.subheader("4. Servicios y Lavandería")
            cs1, cs2 = st.columns(2)
            with cs1:
                val_lav = st.text_input("Lavado / Proceso", value=datos_db.get('color_lavado', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cs2:
                val_art = st.text_input("Bordado / Estampado", value=datos_db.get('detalles_arte', ""), disabled=st.session_state.bloquear or ya_enviado)

        # --- 5. TALLAS DINÁMICAS (MODIFICADO) ---
        with st.container(border=True):
            st.subheader("5. Tallas y Planificación de Corte")
            
            c_paq1, c_paq2 = st.columns([1, 2])
            with c_paq1:
                val_paq = st.number_input("N° de Paquetes", min_value=1, value=int(datos_db.get('cantidad_paquetes', 1)), 
                                         disabled=st.session_state.bloquear or ya_enviado, key="input_paquetes")

            st.divider()

            if not st.session_state.bloquear and not ya_enviado:
                st.markdown("**Añadir Talla al Corte**")
                col_add1, col_add2, col_add3 = st.columns([2, 2, 1])
                nueva_t = col_add1.text_input("Talla (ej: 30, XL)", key="add_talla_nom")
                nueva_c = col_add2.number_input("Cant. x Paquete", min_value=1, step=1, key="add_talla_cant")
                if col_add3.button("➕ Añadir"):
                    if nueva_t:
                        st.session_state.curva_dinamica.append({"talla": nueva_t, "cantidad": nueva_c})
                        st.rerun()

            if st.session_state.curva_dinamica:
                h_t = st.columns([2, 2, 2, 0.5])
                h_t[0].caption("TALLA"); h_t[1].caption("CANT. X PAQUETE"); h_t[2].caption("TOTAL A CORTAR")

                total_general_prendas = 0
                for idx, t_item in enumerate(st.session_state.curva_dinamica):
                    r_t = st.columns([2, 2, 2, 0.5])
                    
                    # --- CORRECCIÓN AQUÍ: Validamos que sean números ---
                    cant_unid = t_item.get('cantidad', 0)
                    # Si por alguna razón cant_unid o val_paq son None, usamos 0
                    cant_unid = int(cant_unid) if cant_unid else 0
                    n_paquetes = int(val_paq) if val_paq else 0
                    
                    t_final = cant_unid * n_paquetes
                    total_general_prendas += t_final
                    
                    r_t[0].write(f"**{t_item['talla']}**")
                    r_t[1].write(f"{cant_unid} und.")
                    r_t[2].info(f"{t_final} unidades")
                    
                    if not st.session_state.bloquear and not ya_enviado:
                        if r_t[3].button("🗑️", key=f"del_talla_{idx}"):
                            st.session_state.curva_dinamica.pop(idx)
                            st.rerun()
                
                st.divider()
                st.metric("TOTAL PRENDAS EN ESTA FICHA", f"{total_general_prendas} Unidades")

        # 6. FOTOS
        with st.container(border=True):
            st.subheader("6. Fotos")
            st.file_uploader("Subir fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)

        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                if "Seleccionar..." in [val_cat, val_est, val_dis]:
                    st.error("Faltan datos obligatorios.")
                else:
                    cod = st.session_state.codigo_actual
                    if cod == "S/C":
                        cod = f"{val_cat[:3].upper()}-{val_est[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                    
                    payload = {
                        "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est, "disenadora": val_dis,
                        "prioridad": val_prior, "patronista_responsable": val_pat, "observaciones_contra": val_obs_dis,
                        "desc_prenda": val_desc, "ref_entalle": val_entalle, "procesos_aux": val_proc,
                        "rec_observaciones": val_rec, "obs_molde": val_obs_molde, "tela_1": val_t1, "tela_2": val_t2,
                        "insumos_detalle": st.session_state.insumos_temp, "color_lavado": val_lav, "detalles_arte": val_art,
                        "curva_tallas": st.session_state.curva_dinamica, # FORMATO DINÁMICO
                        "cantidad_paquetes": val_paq, "estado": "Borrador"
                    }
                    try:
                        supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                        st.session_state.codigo_actual = cod
                        st.session_state.bloquear = True
                        st.success(f"Guardado: {cod}"); st.rerun()
                    except Exception as e: st.error(f"Error al guardar: {e}")

        with b2:
            puede_env = not es_nuevo and st.session_state.bloquear and not ya_enviado
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not puede_env):
                    st.session_state.confirmar_envio = True; st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                cs, cn = st.columns(2)
                if cs.button("✅ Sí"):
                    ahora = datetime.datetime.now().isoformat()
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": ahora}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.session_state.confirmar_envio = False; st.rerun()
                if cn.button("❌ No"):
                    st.session_state.confirmar_envio = False; st.rerun()

        with b3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False; st.rerun()

    with tab2:
        st.subheader("📏 Módulo de Patronista")
        if not ya_enviado: st.info("Esperando envío de Diseño.")
        else: st.success(f"Trabajando en: {st.session_state.codigo_actual}")
