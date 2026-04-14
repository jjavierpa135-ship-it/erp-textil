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
if 'telas_temp' not in st.session_state: # NUEVO: Estado para telas dinámicas
    st.session_state.telas_temp = []
if 'curva_dinamica' not in st.session_state:
    st.session_state.curva_dinamica = []

# --- 4. FUNCIONES DE APOYO ---
def limpiar_pantalla_total():
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.confirmar_envio = False
    st.session_state.insumos_temp = []
    st.session_state.telas_temp = [] # Limpiar telas
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
                            st.session_state.telas_temp = [] # Reset al cargar
                            st.session_state.curva_dinamica = []
                            st.session_state.form_id += 1 
                            st.rerun()
        except: pass
                
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
                
                # CARGA DE INSUMOS
                if not st.session_state.insumos_temp:
                    st.session_state.insumos_temp = datos_db.get('insumos_detalle', [])

                # CARGA DE TELAS (Dinamizada)
                if not st.session_state.telas_temp:
                    # Cargamos el JSON de telas de la nueva columna 'telas_detalle'
                    st.session_state.telas_temp = datos_db.get('telas_detalle', [])

                # CARGA DE TALLAS
                if not st.session_state.curva_dinamica:
                    st.session_state.curva_dinamica = datos_db.get('curva_tallas', [])

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
            
            # --- MODIFICACIÓN: LISTA DE TELAS DINÁMICA ---
            st.write("**🧵 Detalle de Telas (Consumo Estimado):**")
            telas_catalog = ["Seleccionar...", "Denim 12oz", "Denim 10oz", "Gabardina", "Jersey", "Tocuyo", "Popelina (Forro)"]
            
            if st.session_state.telas_temp:
                for idx, t in enumerate(st.session_state.telas_temp):
                    tcol1, tcol2, tcol3 = st.columns([3, 1, 0.5])
                    tcol1.write(f"▪️ {t['nombre']} ({t['tipo']})")
                    tcol2.write(f"{t['cantidad']} mts.")
                    if not st.session_state.bloquear and not ya_enviado:
                        if tcol3.button("🗑️", key=f"del_tel_{idx}"):
                            st.session_state.telas_temp.pop(idx); st.rerun()
            
            if not st.session_state.bloquear and not ya_enviado:
                with st.expander("➕ Añadir Tela (Principal o Secundaria)"):
                    at1, at2, at3 = st.columns([2, 1, 1])
                    nt = at1.selectbox("Seleccionar Tela", telas_catalog, key="ntela")
                    tt = at2.selectbox("Uso", ["Principal", "Secundaria", "Forro"], key="ttipo")
                    ct = at3.number_input("Cant. (mts)", min_value=0.0, step=0.05, format="%.2f", key="ncant")
                    if st.button("Agregar Tela a la Lista"):
                        if nt != "Seleccionar...":
                            st.session_state.telas_temp.append({"nombre": nt, "tipo": tt, "cantidad": ct})
                            st.rerun()

            st.divider()
            
            # --- INSUMOS (SE MANTIENE IGUAL) ---
            try:
                res_mats = supabase.table("almacen_insumos").select("nombre, precio_unitario").execute()
                opciones_mats = [m['nombre'] for m in res_mats.data] if res_mats.data else []
                precios_mats = {m['nombre']: m['precio_unitario'] for m in res_mats.data} if res_mats.data else {}
            except: opciones_mats, precios_mats = [], {}

            if st.session_state.insumos_temp:
                st.write("**📦 Detalle de Insumos:**")
                for idx, item in enumerate(st.session_state.insumos_temp):
                    icol1, icol2, icol3, icol4 = st.columns([3, 1, 1, 0.5])
                    icol1.write(f"🔹 {item.get('codigo')}")
                    icol2.write(f"{item.get('cantidad')} unid.")
                    icol3.write(f"${item.get('precio', 0.0):.2f}")
                    if not st.session_state.bloquear and not ya_enviado:
                        if icol4.button("🗑️", key=f"del_ins_{idx}"):
                            st.session_state.insumos_temp.pop(idx); st.rerun()

            total_insumos = sum(float(item.get('cantidad', 0)) * float(item.get('precio', 0.0)) for item in st.session_state.insumos_temp)
            st.metric("COSTO TOTAL INSUMOS", f"${total_insumos:.2f}")

            if not st.session_state.bloquear and not ya_enviado:
                with st.expander("➕ Añadir Material de Almacén"):
                    f1, f2, f3 = st.columns([2, 1, 1])
                    ins_nom = f1.selectbox("Seleccionar Insumo", ["Buscar..."] + opciones_mats)
                    ins_cant = f2.number_input("Cantidad", min_value=0.0)
                    if f3.button("Agregar Insumo"):
                        if ins_nom != "Buscar...":
                            st.session_state.insumos_temp.append({"codigo": ins_nom, "cantidad": ins_cant, "precio": precios_mats.get(ins_nom, 0.0)})
                            st.rerun()

        with st.container(border=True):
            st.subheader("5. Tallas y Planificación de Corte")
            if not st.session_state.bloquear and not ya_enviado:
                tc1, tc2, tc3 = st.columns([2, 2, 1])
                t_ops = ["Seleccionar...", "26", "28", "30", "32", "34", "36", "S", "M", "L", "XL"]
                t_sel = tc1.selectbox("Seleccione Talla", t_ops)
                r_val = tc2.number_input("Piezas (Ratio)", min_value=1, step=1)
                if tc3.button("➕ Añadir Talla"):
                    if t_sel != "Seleccionar...":
                        st.session_state.curva_dinamica.append({"talla": t_sel, "cantidad": r_val}); st.rerun()

            suma_tizado = sum(int(i.get('cantidad', 0)) for i in st.session_state.curva_dinamica)
            if suma_tizado > 0:
                cant_pedida = st.number_input("Cantidad total deseada:", min_value=1, value=max(suma_tizado, int(datos_db.get('cantidad_paquetes', suma_tizado))), disabled=st.session_state.bloquear or ya_enviado)
                n_capas = (cant_pedida + suma_tizado - 1) // suma_tizado
                total_real = n_capas * suma_tizado
                for idx, item in enumerate(st.session_state.curva_dinamica):
                    fila = st.columns([2, 2, 2, 0.5])
                    fila[0].write(f"**{item['talla']}**")
                    fila[1].write(f"{item['cantidad']} pzs")
                    fila[2].success(f"{n_capas * int(item['cantidad'])} uds")
                    if not st.session_state.bloquear and not ya_enviado:
                        if fila[3].button("🗑️", key=f"del_talla_{idx}"):
                            st.session_state.curva_dinamica.pop(idx); st.rerun()
                st.metric("TOTAL FINAL ORDEN", f"{total_real} prendas")
            else:
                total_real = 0

        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                cod_id = st.session_state.codigo_actual if st.session_state.codigo_actual != "S/C" else f"M-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                payload = {
                    "codigo_muestra": cod_id, "categoria": val_cat, "estilo": val_est, "disenadora": val_dis, 
                    "prioridad": val_prior, "patronista_responsable": val_pat, "observaciones_contra": val_obs_dis, 
                    "desc_prenda": val_desc, "curva_tallas": st.session_state.curva_dinamica,
                    "insumos_detalle": st.session_state.insumos_temp, 
                    "telas_detalle": st.session_state.telas_temp, # NUEVO: Guardado de lista de telas
                    "cantidad_paquetes": total_real, "estado": "Borrador"
                }
                try:
                    supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                    st.session_state.codigo_actual = cod_id
                    st.session_state.bloquear = True
                    st.success(f"Guardado: {cod_id}"); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

        with b2:
            p_e = st.session_state.bloquear and st.session_state.codigo_actual != "S/C" and not ya_enviado
            if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not p_e):
                supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": datetime.datetime.now().isoformat()}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                st.rerun()

        with b3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False; st.rerun()
