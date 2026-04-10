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

# BLOQUE 3: TELAS E INSUMOS (MODIFICADO)
        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            
            # --- SECCIÓN TELAS (Combos) ---
            # Puedes editar esta lista con los nombres de tus telas reales
            lista_telas = ["Seleccionar...", "Denim 12oz", "Denim 10oz", "Gabardina", "Jersey", "Tocuyo"]
            
            ci1, ci2 = st.columns(2)
            with ci1:
                val_t1 = st.selectbox("Tela Principal", lista_telas, 
                                     index=obtener_indice(lista_telas, datos_db.get('tela_1')), 
                                     key=f"t1_{st.session_state.form_id}",
                                     disabled=st.session_state.bloquear or ya_enviado)
            with ci2:
                val_t2 = st.selectbox("Tela Complemento", lista_telas, 
                                     index=obtener_indice(lista_telas, datos_db.get('tela_2')), 
                                     key=f"t2_{st.session_state.form_id}",
                                     disabled=st.session_state.bloquear or ya_enviado)

            st.divider()

            # --- SECCIÓN INSUMOS (Tabla Dinámica) ---
            st.markdown("**Detalle de Insumos**")
            
            # Sincronizar con base de datos al cargar
            if not st.session_state.insumos_temp and not es_nuevo:
                st.session_state.insumos_temp = datos_db.get('insumos_detalle', [])

            # Cabecera de la tabla
            h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 1, 1, 1, 0.5])
            h1.caption("Código/Insumo")
            h2.caption("Color")
            h3.caption("Diseño")
            h4.caption("Tamaño")
            h5.caption("Cantidad")
            h6.caption("Acción")

            # Mostrar registros agregados
            for idx, item in enumerate(st.session_state.insumos_temp):
                r1, r2, r3, r4, r5, r6 = st.columns([1.5, 1, 1, 1, 1, 0.5])
                r1.write(item.get('codigo', ''))
                r2.write(item.get('color', ''))
                r3.write(item.get('diseno', ''))
                r4.write(item.get('tamano', ''))
                r5.write(str(item.get('cantidad', '')))
                if not st.session_state.bloquear and not ya_enviado:
                    if r6.button("🗑️", key=f"del_ins_{idx}"):
                        st.session_state.insumos_temp.pop(idx)
                        st.rerun()

            # Formulario de entrada (Solo si no está bloqueado)
            if not st.session_state.bloquear and not ya_enviado:
                with st.expander("➕ Adicionar línea de insumo", expanded=True):
                    f1, f2, f3, f4, f5, f6 = st.columns([1.5, 1, 1, 1, 1, 1])
                    new_cod = f1.text_input("Código", key="ins_cod")
                    new_col = f2.text_input("Color", key="ins_col")
                    new_dis = f3.text_input("Diseño", key="ins_dis")
                    new_tam = f4.text_input("Tamaño", key="ins_tam")
                    new_can = f5.number_input("Cant.", min_value=0.0, key="ins_can")
                    if f6.button("Añadir", use_container_width=True):
                        if new_cod:
                            st.session_state.insumos_temp.append({
                                "codigo": new_cod, "color": new_col, 
                                "diseno": new_dis, "tamano": new_tam, "cantidad": new_can
                            })
                            st.rerun()
                        else: st.warning("Escribe un código/nombre")

# --- 4. FUNCIONES DE APOYO ---
def limpiar_pantalla_total():
    st.session_state.codigo_actual = "S/C"
    st.session_state.bloquear = False
    st.session_state.confirmar_envio = False
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

        # Listas (Asegúrate que coincidan con lo que hay en DB)
        cats = ["Seleccionar...", "Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
        ests = ["Seleccionar...", "Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
        pats = ["Seleccionar...", "Patronista 1", "Patronista 2", "Patronista 3"]
        dis_lista = ["Seleccionar...", "Ariana", "Diseñadora 2", "Diseñadora 3"]
        prioridades = ["Normal", "Urgente", "Muestra VIP"]

        # BLOQUE 1: DATOS GENERALES
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

        # BLOQUE 2: DISEÑO PROPIAMENTE
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

        # BLOQUE 3: TELAS E INSUMOS
        with st.container(border=True):
            st.subheader("3. Telas e Insumos")
            ci1, ci2 = st.columns(2)
            with ci1:
                val_t1 = st.text_input("Tela Principal", value=datos_db.get('tela_1', ""), disabled=st.session_state.bloquear or ya_enviado)
                val_t2 = st.text_input("Tela Complemento", value=datos_db.get('tela_2', ""), disabled=st.session_state.bloquear or ya_enviado)
            with ci2:
                val_ins = st.text_area("Insumos", value=datos_db.get('insumos', ""), disabled=st.session_state.bloquear or ya_enviado, height=100)

        # BLOQUE 4: SERVICIOS Y LAVANDERÍA
        with st.container(border=True):
            st.subheader("4. Servicios y Lavandería")
            cs1, cs2 = st.columns(2)
            with cs1:
                val_lav = st.text_input("Lavado / Proceso", value=datos_db.get('color_lavado', ""), disabled=st.session_state.bloquear or ya_enviado)
            with cs2:
                val_art = st.text_input("Bordado / Estampado", value=datos_db.get('detalles_arte', ""), disabled=st.session_state.bloquear or ya_enviado)

        # BLOQUE 5: TALLAS Y CORTE
        with st.container(border=True):
            st.subheader("5. Tallas y Corte")
            tallas_lista = ["26", "28", "30", "32", "34", "36"]
            cols_t = st.columns(len(tallas_lista) + 1)
            curva_datos = {}
            total_prendas = 0
            
            with cols_t[0]: st.write("**Talla**")
            for i, t in enumerate(tallas_lista):
                with cols_t[i+1]: st.write(f"**{t}**")
            
            with cols_t[0]: st.write("**Corte (2,2,1...)**")
            db_curva = datos_db.get('curva_tallas', {}) if isinstance(datos_db.get('curva_tallas'), dict) else {}
            for i, t in enumerate(tallas_lista):
                with cols_t[i+1]:
                    curva_datos[t] = st.number_input(f"T{t}", min_value=0, value=int(db_curva.get(t, 0)), label_visibility="collapsed", key=f"curva_{t}")

            st.divider()
            cc1, cc2 = st.columns([1, 2])
            with cc1:
                val_paq = st.number_input("Cantidad de Paquetes", min_value=1, value=int(datos_db.get('cantidad_paquetes', 1)), disabled=st.session_state.bloquear or ya_enviado)
            with cc2:
                totales_str = " | ".join([f"{t}: {curva_datos[t]*val_paq}" for t in tallas_lista if curva_datos[t]>0])
                total_general = sum(curva_datos.values()) * val_paq
                st.metric("TOTAL PRENDAS A CORTE", total_general, help=totales_str)

        # BLOQUE 6: FOTOS
        with st.container(border=True):
            st.subheader("6. Fotos y Multimedia")
            fotos = st.file_uploader("Subir fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], disabled=st.session_state.bloquear or ya_enviado)
            if fotos:
                cf = st.columns(5)
                for i, f in enumerate(fotos):
                    with cf[i % 5]: st.image(f, use_container_width=True)

        st.divider()
        # BOTONES
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Guardar Todo", use_container_width=True, disabled=ya_enviado):
                if "Seleccionar..." in [val_cat, val_est, val_dis]:
                    st.error("Faltan datos en el Bloque 1.")
                else:
                    cod = st.session_state.codigo_actual
                    if cod == "S/C":
                        cod = f"{val_cat[:3].upper()}-{val_est[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                    payload = {
                        "codigo_muestra": cod, "categoria": val_cat, "estilo": val_est, "disenadora": val_dis,
                        "prioridad": val_prior, "patronista_responsable": val_pat, "observaciones_contra": val_obs_dis,
                        "desc_prenda": val_desc, "ref_entalle": val_entalle, "procesos_aux": val_proc,
                        "rec_observaciones": val_rec, "obs_molde": val_obs_molde, "tela_1": val_t1, "tela_2": val_t2,
                        "insumos": val_ins, "color_lavado": val_lav, "detalles_arte": val_art,
                        "curva_tallas": curva_datos, "cantidad_paquetes": val_paq, "estado": "Borrador"
                    }
                    try:
                        supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                        st.session_state.codigo_actual = cod
                        st.session_state.bloquear = True
                        st.success(f"Guardado: {cod}")
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

        with b2:
            puede_env = not es_nuevo and st.session_state.bloquear and not ya_enviado
            if not st.session_state.confirmar_envio:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=not puede_env):
                    st.session_state.confirmar_envio = True
                    st.rerun()
            else:
                st.warning("¿Confirmar envío?")
                cs, cn = st.columns(2)
                with cs:
                    if st.button("✅ Sí"):
                        ahora = datetime.datetime.now().isoformat()
                        supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje", "fecha_envio_patronaje": ahora}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                        st.session_state.confirmar_envio = False
                        st.rerun()
                with cn:
                    if st.button("❌ No"):
                        st.session_state.confirmar_envio = False
                        st.rerun()

        with b3:
            if st.button("✏️ Editar", use_container_width=True, disabled=ya_enviado):
                st.session_state.bloquear = False
                st.rerun()

    with tab2:
        st.subheader("📏 Módulo de Patronista")
        if not ya_enviado: st.info("Esperando envío de Diseño.")
        else: st.success(f"Trabajando en: {st.session_state.codigo_actual}")
