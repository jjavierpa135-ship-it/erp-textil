import streamlit as st
from supabase import create_client, Client

# --- 1. CONEXIÓN ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Error de conexión"); st.stop()

st.title("🧪 MVP: Prueba de Carga Robusta")

# --- 2. ESTADOS DE SESIÓN ---
if 'bloquear_mvp' not in st.session_state:
    st.session_state.bloquear_mvp = True
if 'codigo_mvp' not in st.session_state:
    st.session_state.codigo_mvp = None
if 'curva_mvp' not in st.session_state:
    st.session_state.curva_mvp = []

# --- 3. BUSCADOR ---
try:
    res = supabase.table("fichas_muestras").select("codigo_muestra, estilo").order("fecha_creacion", desc=True).limit(10).execute()
    opciones = {f"{r['codigo_muestra']} - {r['estilo']}": r['codigo_muestra'] for r in res.data}
    
    seleccion = st.selectbox("Selecciona una muestra:", ["Seleccionar..."] + list(opciones.keys()))
    
    if seleccion != "Seleccionar...":
        cod_sel = opciones[seleccion]
        if st.button("🔍 Cargar y Consultar"):
            st.session_state.codigo_mvp = cod_sel
            st.session_state.bloquear_mvp = True
            st.session_state.curva_mvp = [] # Limpiar sesión
            st.rerun()
except:
    st.error("No se pudieron cargar muestras.")

st.divider()

# --- 4. LÓGICA DE CARGA SEGURA ---
if st.session_state.codigo_mvp:
    res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_mvp).execute()
    
    if res_ficha.data:
        ficha_db = res_ficha.data[0]
        st.subheader(f"Viendo: {st.session_state.codigo_mvp}")

        col1, col2 = st.columns(2)
        if col1.button("✏️ Modo Edición"):
            # Aseguramos que cargamos una lista limpia a la sesión
            db_data = ficha_db.get('curva_tallas')
            st.session_state.curva_mvp = db_data if isinstance(db_data, list) else []
            st.session_state.bloquear_mvp = False
            st.rerun()
            
        if col2.button("🔒 Modo Consulta"):
            st.session_state.bloquear_mvp = True
            st.rerun()

        # DETERMINAR FUENTE DE DATOS
        if st.session_state.bloquear_mvp:
            raw_data = ficha_db.get('curva_tallas')
            # Validamos que sea una lista para evitar el TypeError
            datos_finales = raw_data if isinstance(raw_data, list) else []
            st.info("👁️ MODO CONSULTA (Directo de Supabase)")
        else:
            datos_finales = st.session_state.curva_mvp
            st.warning("✍️ MODO EDICIÓN (Sesión temporal)")

        # VISUALIZACIÓN BLINDADA
        if datos_finales:
            for idx, item in enumerate(datos_finales):
                # Validamos que el item sea un diccionario antes de pedir 'talla'
                if isinstance(item, dict) and 'talla' in item:
                    c_talla, c_cant, c_accion = st.columns([2, 2, 1])
                    c_talla.write(f"Talla: **{item['talla']}**")
                    c_cant.write(f"Cant: {item.get('cantidad', 0)}")
                    
                    if not st.session_state.bloquear_mvp:
                        if c_accion.button("🗑️", key=f"btn_del_{idx}"):
                            st.session_state.curva_mvp.pop(idx)
                            st.rerun()
        else:
            st.info("No hay datos válidos o la lista está vacía.")
            
        # AGREGAR (Solo en edición)
        if not st.session_state.bloquear_mvp:
            st.divider()
            nueva_t = st.text_input("Nueva Talla")
            if st.button("➕ Agregar"):
                if nueva_t:
                    st.session_state.curva_mvp.append({"talla": nueva_t, "cantidad": 1})
                    st.rerun()
