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
    # --- BUSCADOR ---
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

    # --- CABECERA ---
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

        # Listas para Selectbox
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        # --- SECCIONES 1 A 4 ---
        with st.container(border=True):
            st.subheader("1. Datos de Cabecera")
            c1, c2, c3, c4 = st.columns(4)
            with c1: val_dis = st.selectbox("Diseñadora", dis_lista, index=obtener_indice(dis_lista, datos_db.get('disenadora')), key=f"d_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c2: val_cat = st.selectbox("Categoría", cats, index=obtener_indice(cats, datos_db.get('categoria')), key=f"c_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c3: val_est = st.selectbox("Estilo", ests, index=obtener_indice(ests, datos_db.get('estilo')), key=f"e_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)
            with c4: val_prior = st.selectbox("Prioridad", prioridades, index=obtener_indice(prioridades, datos_db.get('prioridad')), key=f"pr_{st.session_state.form_id}", disabled=st.session_state.bloquear or ya_enviado)

        with st.container(border=True):
            st.subheader("2. Especificaciones de Diseño")
            cd1, cd2 = st.columns(2)
            with cd1:
                val_desc = st.text_area("Descripción de la Prenda", value=datos_db.get('desc_prenda', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
                val_entalle = st.text_input("Referencia de Entalle", value=datos_db.get('ref_entalle', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cd2:
                val_obs_dis = st.text_area("Observaciones de Diseño", value=datos_db.get('observaciones_contra', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)
                val_rec = st.text_area("Recomendaciones", value=datos_db.get('rec_observaciones', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)

        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            telas_lista = ["Seleccionar...", "Denim 12oz", "Denim 10oz", "Gabardina", "Jersey", "Tocuyo"]
            ci1, ci2 = st.columns(2)
            with ci1: val_t1 = st.selectbox("Tela Principal", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_1')), disabled=st.session_state.bloquear or ya_enviado)
            with ci2: val_t2 = st.selectbox("Tela Complemento", telas_lista, index=obtener_indice(telas_lista, datos_db.get('tela_2')), disabled=st.session_state.bloquear or ya_enviado)

        with st.container(border=True):
            st.subheader("4. Servicios y Lavandería")
            cs1, cs2 = st.columns(2)
            with cs1: val_lav = st.text_input("Lavado", value=datos_db.get('color_lavado', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cs2: val_art = st.text_input("Arte", value=datos_db.get('detalles_arte', ""), disabled=st.session_state.bloquear or ya_enviado)

        # --- SECCIÓN 5: TALLAS (ESTA ES LA QUE DABA ERROR) ---
        with st.container(border=True):
            col_t_tit, col_t_res = st.columns([3, 1])
            col_t_tit.subheader("5. Tallas y Planificación de Corte")
            
            if not isinstance(st.session_state.curva_dinamica, list):
                st.session_state.curva_dinamica = []

            if not st.session_state.bloquear and not ya_enviado:
                if col_t_res.button("♻️ Reiniciar Tallas", use_container_width=True):
                    st.session_state.curva_dinamica = []
                    st.rerun()

                st.markdown("**1. Armar el Tizado (Proporción por capa)**")
                c_tal, c_can, c_add = st.columns([2, 2, 1])
                t_ops = ["Seleccionar...", "26", "28", "30", "32", "34", "36", "S", "M", "L", "XL"]
                t_sel = c_tal.selectbox("Talla", t_ops, key="selector_talla_final")
                r_val = c_can.number_input("Piezas en Tizado", min_value=1, step=1, key="ratio_final")
                
                if c_add.button("➕ Añadir"):
                    if t_sel != "Seleccionar...":
                        actuales = [item['talla'] for item in st.session_state.curva_dinamica if isinstance(item, dict)]
                        if t_sel not in actuales:
                            st.session_state.curva_dinamica.append({"talla": t_sel, "cantidad": r_val})
                            st.rerun()

            # Cálculo Seguro
            suma_tizado = sum(int(i.get('cantidad', 0)) for i in st.session_state.curva_dinamica if isinstance(i, dict))
            
            if suma_tizado > 0:
                st.divider()
                st.markdown(f"**2. Definir Cantidad del Pedido** (Tizado: {suma_tizado} pzs/capa)")
                
                cant_pedida = st.number_input("Prendas totales deseadas", min_value=1, value=max(suma_tizado, int(datos_db.get('cantidad_paquetes', suma_tizado))), disabled=st.session_state.bloquear or ya_enviado)

                # Cálculo de capas y total
                n_capas = (cant_pedida + suma_tizado - 1) // suma_tizado
                total_real = n_capas * suma_tizado
                
                if total_real != cant_pedida:
                    st.info(f"Se cortarán **{n_capas} capas** para un total de **{total_real}** prendas.")

                # Tabla de Resumen
                for idx, item in enumerate(st.session_state.curva_dinamica):
                    f_col = st.columns([2, 2, 2, 0.5])
                    v_pzs = int(item.get('cantidad', 0))
                    f_col[0].write(f"Talla {item['talla']}")
                    f_col[1].write(f"{v_pzs} pzs")
                    f_col[2].info(f"{n_capas * v_pzs} unidades")
                    if not st.session_state.bloquear and not ya_enviado:
                        if f_col[3].button("🗑️", key=f"del_final_{idx}"):
                            st.session_state.curva_dinamica.pop(idx); st.rerun()
                
                st.metric("TOTAL FINAL A CORTAR", f"{total_real} prendas")
            else:
                st.info("Agregue tallas para habilitar los cálculos de corte.")
                total_real = 0

        # --- BOTONES FINALES ---
        st.divider()
        b1, b2, b3 = st.columns(3)

        with b1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                cod_id = st.session_state.codigo_actual if st.session_state.codigo_actual != "S/C" else f"M-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                payload = {
                    "codigo_muestra": cod_id, "categoria": val_cat, "estilo": val_est, "disenadora": val_dis,
                    "prioridad": val_prior, "patronista_responsable": val_pat, "desc_prenda": val_desc,
                    "tela_1": val_t1, "curva_tallas": st.session_state.curva_dinamica,
                    "cantidad_paquetes": total_real, "estado": "Borrador"
                }
                supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                st.session_state.codigo_actual = cod_id; st.session_state.bloquear = True
                st.success("Guardado correctamente"); st.rerun()

        with b2:
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not (st.session_state.bloquear and not ya_enviado)):
                    st.session_state.confirmar_envio = True; st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                if st.button("✅ Confirmar"):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": datetime.datetime.now().isoformat()}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.session_state.confirmar_envio = False; st.rerun()
                if st.button("❌ Cancelar"):
                    st.session_state.confirmar_envio = False; st.rerun()

        with b3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False; st.rerun()
