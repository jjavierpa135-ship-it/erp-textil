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
                if not st.session_state.insumos_temp and datos_db.get('insumos_detalle'):
                    st.session_state.insumos_temp = datos_db.get('insumos_detalle')
                if not st.session_state.curva_dinamica and datos_db.get('curva_tallas'):
                    st.session_state.curva_dinamica = datos_db.get('curva_tallas')

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

        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            telas_lista = ["Seleccionar...", "Denim 12oz", "Denim 10oz", "Gabardina", "Jersey", "Tocuyo"]
            ci1, ci2 = st.columns(2)
            with ci1: val_t1 = st.selectbox("Tela Principal", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_1')), disabled=st.session_state.bloquear or ya_enviado)
            with ci2: val_t2 = st.selectbox("Tela Complemento", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_2')), disabled=st.session_state.bloquear or ya_enviado)
            
            try:
                res_mats = supabase.table("almacen_insumos").select("nombre, precio_unitario").execute()
                opciones_mats = [m['nombre'] for m in res_mats.data] if res_mats.data else []
                precios_mats = {m['nombre']: m['precio_unitario'] for m in res_mats.data} if res_mats.data else {}
            except: opciones_mats, precios_mats = [], {}

            total_insumos = 0.0
            for idx, item in enumerate(st.session_state.insumos_temp):
                p_unit = item.get('precio', 0.0)
                sub = item.get('cantidad', 0) * p_unit
                total_insumos += sub
            st.metric("COSTO TOTAL INSUMOS", f"${total_insumos:.2f}")

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


# --- SECCIÓN 5: TALLAS Y PLANIFICACIÓN (CÓDIGO BLINDADO) ---
        with st.container(border=True):
            col_t_tit, col_t_res = st.columns([3, 1])
            col_t_tit.subheader("5. Tallas y Planificación de Corte")
            
            # Reset de tallas (solo si no está bloqueado)
            if not st.session_state.bloquear and not ya_enviado:
                if col_t_res.button("♻️ Reiniciar Tallas", use_container_width=True):
                    st.session_state.curva_dinamica = []
                    st.rerun()

            # Inicialización de seguridad
            if 'curva_dinamica' not in st.session_state or st.session_state.curva_dinamica is None:
                st.session_state.curva_dinamica = []

            pedido_total = st.number_input("Cantidad total de prendas (Pedido)", min_value=1, 
                                          value=int(datos_db.get('cantidad_paquetes', 10)), 
                                          disabled=st.session_state.bloquear or ya_enviado)
            st.divider()

            # Formulario para añadir tallas
            if not st.session_state.bloquear and not ya_enviado:
                st.markdown("**Agregar Proporción de Corte**")
                c1, c2, c3 = st.columns([2, 2, 1])
                t_opciones = ["Seleccionar...", "26", "28", "30", "32", "34", "36", "S", "M", "L", "XL"]
                t_sel = c1.selectbox("Talla", t_opciones, key="talla_selector_final")
                r_val = c2.number_input("Corte (Ratio)", min_value=1, step=1, key="ratio_input_final")
                
                if c3.button("➕ Añadir"):
                    if t_sel != "Seleccionar...":
                        # Evitar duplicados
                        lista_actual = [item['talla'] for item in st.session_state.curva_dinamica if isinstance(item, dict)]
                        if t_sel in lista_actual:
                            st.warning(f"La talla {t_sel} ya existe.")
                        else:
                            st.session_state.curva_dinamica.append({"talla": t_sel, "cantidad": r_val})
                            st.rerun()

            # Mostrar tabla y realizar cálculos
            if st.session_state.curva_dinamica:
                # Suma segura de ratios
                total_ratios = sum(int(i.get('cantidad', 0)) for i in st.session_state.curva_dinamica if isinstance(i, dict))
                
                header = st.columns([2, 2, 2, 0.5])
                header[0].caption("TALLA"); header[1].caption("RATIO"); header[2].caption("TOTAL UNIDADES")

                conteo_final = 0
                for idx, item in enumerate(st.session_state.curva_dinamica):
                    if not isinstance(item, dict): continue
                    
                    fila = st.columns([2, 2, 2, 0.5])
                    v_ratio = int(item.get('cantidad', 0))
                    
                    # Cálculo con redondeo a entero
                    u_calc = (pedido_total / total_ratios) * v_ratio if total_ratios > 0 else 0
                    u_final = int(round(u_calc))
                    conteo_final += u_final
                    
                    fila[0].write(f"**{item['talla']}**")
                    fila[1].write(f"{v_ratio} partes")
                    fila[2].info(f"{u_final} unidades")
                    
                    if not st.session_state.bloquear and not ya_enviado:
                        if fila[3].button("🗑️", key=f"del_final_{idx}"):
                            st.session_state.curva_dinamica.pop(idx)
                            st.rerun()
                
                st.divider()
                st.metric("RESUMEN DE CORTE", f"{conteo_final} / {pedido_total} prendas")

        # --- SECCIÓN 6: FOTOS ---
        with st.container(border=True):
            st.subheader("6. Fotos")
            st.file_uploader("Subir fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)

        st.divider()
        # --- BOTONES DE ACCIÓN (INDENTACIÓN CORREGIDA) ---
        b_col1, b_col2, b_col3 = st.columns(3)

        with b_col1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                # Generar código si es nuevo
                mi_codigo = st.session_state.codigo_actual
                if mi_codigo == "S/C":
                    mi_codigo = f"M-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                
                payload_db = {
                    "codigo_muestra": mi_codigo,
                    "categoria": val_cat, "estilo": val_est, "disenadora": val_dis, "prioridad": val_prior,
                    "patronista_responsable": val_pat, "observaciones_contra": val_obs_dis, "desc_prenda": val_desc,
                    "tela_1": val_t1, "curva_tallas": st.session_state.curva_dinamica,
                    "cantidad_paquetes": pedido_total, "estado": "Borrador"
                }
                try:
                    supabase.table("fichas_muestras").upsert(payload_db, on_conflict="codigo_muestra").execute()
                    st.session_state.codigo_actual = mi_codigo
                    st.session_state.bloquear = True
                    st.success(f"Guardado: {mi_codigo}"); st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

        with b_col2:
            bloqueado = st.session_state.bloquear
            no_es_nuevo = st.session_state.codigo_actual != "S/C"
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not (no_es_nuevo and bloqueado and not ya_enviado)):
                    st.session_state.confirmar_envio = True; st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                c_si, c_no = st.columns(2)
                if c_si.button("✅ Sí", use_container_width=True):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": datetime.datetime.now().isoformat()}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.session_state.confirmar_envio = False; st.rerun()
                if c_no.button("❌ No", use_container_width=True):
                    st.session_state.confirmar_envio = False; st.rerun()

        with b_col3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False; st.rerun()
