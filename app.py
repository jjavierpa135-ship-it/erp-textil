import streamlit as st
from supabase import create_client, Client
import datetime
import json

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
        if res.data:
            st.session_state.codigo_actual = res.data[0]['codigo_muestra']
            st.session_state.bloquear = True
        else:
            st.session_state.codigo_actual = "S/C"
            st.session_state.bloquear = False
    except:
        st.session_state.codigo_actual = "S/C"

# --- 6. INTERFAZ ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Menú", ["👗 Diseño", "📦 Almacén"])

if modulo == "👗 Diseño":
    with st.expander("🔍 Buscador de Muestras", expanded=False):
        try:
            res_busqueda = supabase.table("fichas_muestras").select("codigo_muestra, estilo, estado, fecha_creacion").order("fecha_creacion", desc=True).limit(50).execute()
            if res_busqueda.data:
                opciones = ["Seleccionar..."] + [
                    f"{str(r['fecha_creacion'])[:10]} | {r['codigo_muestra']} | {r.get('estilo', 'S/E')} | [{str(r.get('estado', 'BORRADOR')).upper()}]" 
                    for r in res_busqueda.data
                ]
                seleccion = st.selectbox("Buscar por código o estilo:", opciones, index=0)
                if seleccion != "Seleccionar...":
                    nuevo_cod = seleccion.split(" | ")[1]
                    if nuevo_cod != st.session_state.codigo_actual:
                        if st.button("🔓 Abrir Ficha Seleccionada", use_container_width=True):
                            st.session_state.codigo_actual = nuevo_cod
                            st.session_state.bloquear = True
                            st.session_state.confirmar_envio = False
                            st.session_state.insumos_temp = [] 
                            st.session_state.curva_dinamica = []
                            st.session_state.form_id += 1 
                            st.rerun()
            else:
                st.info("No hay registros disponibles.")
        except Exception as e:
            if "RerunData" not in str(type(e)):
                st.error(f"Error al conectar con el historial: {e}")
                
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
                
                if not st.session_state.insumos_temp:
                    detalle_db = datos_db.get('insumos_detalle')
                    if isinstance(detalle_db, list):
                        st.session_state.insumos_temp = detalle_db
                    elif isinstance(detalle_db, str) and detalle_db.strip():
                        try: st.session_state.insumos_temp = json.loads(detalle_db)
                        except: st.session_state.insumos_temp = []

                if not st.session_state.curva_dinamica:
                    curva_db = datos_db.get('curva_tallas')
                    if isinstance(curva_db, list):
                        st.session_state.curva_dinamica = curva_db

        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        with st.container(border=True):
            st.subheader("1. Datos de Cabecera")
            c1, c2, c3, c4 = st.columns(4)
            with c1: val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c2: val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c3: val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c4: val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key=f"pr_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

            c5, c6, c7 = st.columns(3)
            with c5:
                fecha_f = datos_db.get('fecha_creacion', datetime.date.today().strftime('%Y-%m-%d'))
                st.text_input("Fecha Creación", value=str(fecha_f)[:10], disabled=True)
            with c6:
                val_pat = st.selectbox("Patronista Asignado", pats, index=obtener_indice(pats, datos_db.get('patronista_responsable')), key=f"p_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c7:
                f_envio = datos_db.get('fecha_envio_patronaje', "No enviado")
                st.text_input("Fecha/Hora Envío", value=str(f_envio).replace("T", " ")[:16], disabled=True)

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

        # --- SECCIÓN 3: TELAS E INSUMOS (VERSIÓN ROBUSTA) ---
        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            
            # Carga de telas desde el Maestro de Telas
            try:
                # Intentamos traer todas las columnas para evitar errores de nombre específico
                res_telas = supabase.table("maestro_telas").select("*").execute()
                
                if res_telas.data:
                    # Buscamos la columna de precio sin importar si tiene tilde o no en la DB
                    # Esto busca una columna que contenga 'precio' y 'reposicion'
                    dict_telas = {}
                    for t in res_telas.data:
                        nombre = t.get('nombre_interno')
                        # Intentamos obtener el precio de varias formas posibles
                        precio = t.get('precio_reposicion_usd') or t.get('precio_reposición_usd') or 0.0
                        if nombre:
                            dict_telas[nombre] = float(precio)
                    
                    opciones_telas = ["Seleccionar..."] + list(dict_telas.keys())
                else:
                    opciones_telas = ["Seleccionar..."]
                    dict_telas = {}
            except Exception as e:
                st.error(f"Error al conectar con Maestro de Telas: {e}")
                opciones_telas = ["Seleccionar...", "Error de Conexión"]
                dict_telas = {}
        
            # Bloque de Tela Principal
            st.write("**Tela Principal (Cuerpo)**")
            ctp1, ctp2, ctp3 = st.columns([2, 1, 1])
            val_t1 = ctp1.selectbox("Seleccionar Tela", opciones_telas, index=obtener_indice(opciones_telas, datos_db.get('tela_1')), key="t1_sel", disabled=st.session_state.bloquear or ya_enviado)
            
            # Aseguramos que el consumo sea un número válido
            try:
                val_cons_t1 = float(datos_db.get('consumo_t1', 1.20))
            except:
                val_cons_t1 = 1.20
        
            cant_t1 = ctp2.number_input("Consumo (m)", min_value=0.0, value=val_cons_t1, key="t1_cant", disabled=st.session_state.bloquear or ya_enviado)
            costo_t1 = dict_telas.get(val_t1, 0.0) * cant_t1
            ctp3.metric("Subtotal Tela", f"${costo_t1:.2f}")
        
            # Bloque de Tela Secundaria
            st.write("**Tela Complemento (Forros/Combinación)**")
            cts1, cts2, cts3 = st.columns([2, 1, 1])
            val_t2 = cts1.selectbox("Seleccionar Tela Secund.", opciones_telas, index=obtener_indice(opciones_telas, datos_db.get('tela_2')), key="t2_sel", disabled=st.session_state.bloquear or ya_enviado)
            
            try:
                val_cons_t2 = float(datos_db.get('consumo_t2', 0.0))
            except:
                val_cons_t2 = 0.0
        
            cant_t2 = cts2.number_input("Consumo Sec. (m)", min_value=0.0, value=val_cons_t2, key="t2_cant", disabled=st.session_state.bloquear or ya_enviado)
            costo_t2 = dict_telas.get(val_t2, 0.0) * cant_t2
            cts3.metric("Subtotal Sec.", f"${costo_t2:.2f}")
            
 

            st.divider()

            # Gestión de Insumos
            try:
                res_mats = supabase.table("almacen_insumos").select("nombre, precio_unitario").execute()
                opciones_mats = [m['nombre'] for m in res_mats.data] if res_mats.data else []
                precios_mats = {m['nombre']: float(m['precio_unitario']) for m in res_mats.data} if res_mats.data else {}
            except: opciones_mats, precios_mats = [], {}

            if st.session_state.insumos_temp:
                st.write("**Detalle de Insumos:**")
                for idx, item in enumerate(st.session_state.insumos_temp):
                    icol1, icol2, icol3, icol4 = st.columns([3, 1, 1, 0.5])
                    icol1.write(f"🔹 {item.get('codigo')}")
                    icol2.write(f"{item.get('cantidad')} unid.")
                    icol3.write(f"${float(item.get('precio', 0.0)):.2f}")
                    if not st.session_state.bloquear and not ya_enviado:
                        if icol4.button("🗑️", key=f"del_ins_{idx}"):
                            st.session_state.insumos_temp.pop(idx); st.rerun()

            total_insumos = sum(float(item.get('cantidad', 0)) * float(item.get('precio', 0.0)) for item in st.session_state.insumos_temp)
            
            # CÁLCULO TOTAL DE MATERIALES
            costo_materiales = costo_t1 + costo_t2 + total_insumos
            
            m1, m2 = st.columns(2)
            m1.metric("COSTO TOTAL INSUMOS", f"${total_insumos:.2f}")
            m2.subheader(f"💰 COSTO TOTAL MATERIALES: ${costo_materiales:.2f}")

            if not st.session_state.bloquear and not ya_enviado:
                with st.expander("➕ Añadir Material de Almacén"):
                    f1, f2, f3 = st.columns([2, 1, 1])
                    insumo_nom = f1.selectbox("Seleccionar Insumo", ["Buscar..."] + opciones_mats)
                    insumo_cant = f2.number_input("Cantidad", min_value=0.0)
                    if f3.button("Agregar Insumo"):
                        if insumo_nom != "Buscar...":
                            st.session_state.insumos_temp.append({"codigo": insumo_nom, "cantidad": insumo_cant, "precio": precios_mats.get(insumo_nom, 0.0)})
                            st.rerun()

        with st.container(border=True):
            st.subheader("4. Servicios y Lavandería")
            cs1, cs2 = st.columns(2)
            with cs1: val_lav = st.text_input("Lavado", value=datos_db.get('color_lavado', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cs2: val_art = st.text_input("Arte", value=datos_db.get('detalles_arte', ""), disabled=st.session_state.bloquear or ya_enviado)

        with st.container(border=True):
            st.subheader("5. Tallas y Planificación de Corte")
            if not st.session_state.bloquear and not ya_enviado:
                c1, c2, c3 = st.columns([2, 2, 1])
                t_ops = ["Seleccionar...", "26", "28", "30", "32", "34", "36", "S", "M", "L", "XL"]
                t_sel = c1.selectbox("Seleccione Talla", t_ops, key="selector_talla_v6")
                r_val = c2.number_input("Piezas en el Tizado (Ratio)", min_value=1, step=1, key="ratio_v6")
                if c3.button("➕ Añadir Talla", use_container_width=True):
                    if t_sel != "Seleccionar...":
                        actuales = [item['talla'] for item in st.session_state.curva_dinamica]
                        if t_sel not in actuales:
                            st.session_state.curva_dinamica.append({"talla": t_sel, "cantidad": r_val})
                            st.rerun()
                        else: st.error("Talla ya agregada.")

            suma_tizado = sum(int(i.get('cantidad', 0)) for i in st.session_state.curva_dinamica)
            if suma_tizado > 0:
                st.divider()
                st.info(f"Cada capa de tela contiene **{suma_tizado}** prendas.")
                val_inicial = max(suma_tizado, int(datos_db.get('cantidad_paquetes', suma_tizado)))
                cant_pedida = st.number_input("Cantidad total deseada:", min_value=1, value=val_inicial, disabled=st.session_state.bloquear or ya_enviado)
                n_capas = (cant_pedida + suma_tizado - 1) // suma_tizado
                total_real = n_capas * suma_tizado
                
                h = st.columns([2, 2, 2, 0.5])
                h[0].caption("TALLA"); h[1].caption("TIZADO"); h[2].caption("TOTAL")
                for idx, item in enumerate(st.session_state.curva_dinamica):
                    fila = st.columns([2, 2, 2, 0.5])
                    fila[0].write(f"**{item['talla']}**")
                    fila[1].write(f"{item['cantidad']} pzs")
                    fila[2].success(f"{n_capas * int(item['cantidad'])} uds")
                    if not st.session_state.bloquear and not ya_enviado:
                        if fila[3].button("🗑️", key=f"del_v6_{idx}"):
                            st.session_state.curva_dinamica.pop(idx); st.rerun()
                st.metric("TOTAL FINAL ORDEN", f"{total_real} prendas")
            else:
                st.info("Agregue tallas para planificar.")
                total_real = 0

        with st.container(border=True):
            st.subheader("6. Fotos")
            st.file_uploader("Subir fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)

        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                cod_id = st.session_state.codigo_actual if st.session_state.codigo_actual != "S/C" else f"M-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                payload = {
                    "codigo_muestra": cod_id, "categoria": val_cat, "estilo": val_est, "disenadora": val_dis, 
                    "prioridad": val_prior, "patronista_responsable": val_pat, "observaciones_contra": val_obs_dis, 
                    "desc_prenda": val_desc, "tela_1": val_t1, "consumo_t1": cant_t1, "tela_2": val_t2, "consumo_t2": cant_t2,
                    "curva_tallas": st.session_state.curva_dinamica, "insumos_detalle": st.session_state.insumos_temp, 
                    "cantidad_paquetes": total_real, "estado": "Borrador"
                }
                supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                st.session_state.codigo_actual = cod_id
                st.session_state.bloquear = True
                st.success(f"Guardado: {cod_id}"); st.rerun()

        with b2:
            p_e = st.session_state.bloquear and st.session_state.codigo_actual != "S/C" and not ya_enviado
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not p_e):
                    st.session_state.confirmar_envio = True; st.rerun()
            else:
                st.warning("¿Confirmar?")
                c_si, c_no = st.columns(2)
                if c_si.button("✅ Sí"):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": datetime.datetime.now().isoformat()}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.session_state.confirmar_envio = False; st.rerun()
                if c_no.button("❌ No"):
                    st.session_state.confirmar_envio = False; st.rerun()

        with b3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False; st.rerun()
