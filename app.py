import streamlit as st
from supabase import create_client, Client

# --- 1. CONEXIÓN (Asegúrate de tener tus secrets) ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Error de conexión"); st.stop()

st.title("🧪 MVP: Prueba de Carga y Consulta")

# --- 2. ESTADOS DE SESIÓN ---
if 'bloquear_mvp' not in st.session_state:
    st.session_state.bloquear_mvp = True
if 'codigo_mvp' not in st.session_state:
    st.session_state.codigo_mvp = None
if 'curva_mvp' not in st.session_state:
    st.session_state.curva_mvp = []

# --- 3. BUSCADOR REAL ---
try:
    res = supabase.table("fichas_muestras").select("codigo_muestra, estilo").order("fecha_creacion", desc=True).limit(10).execute()
    opciones = {f"{r['codigo_muestra']} - {r['estilo']}": r['codigo_muestra'] for r in res.data}
    
    seleccion = st.selectbox("Selecciona una muestra para probar:", ["Seleccionar..."] + list(opciones.keys()))
    
    if seleccion != "Seleccionar...":
        cod_sel = opciones[seleccion]
        if st.button("🔍 Cargar y Consultar"):
            st.session_state.codigo_mvp = cod_sel
            st.session_state.bloquear_mvp = True
            st.session_state.curva_mvp = [] # Limpiamos sesión para forzar ver DB
            st.rerun()
except:
    st.error("No se pudieron cargar muestras de la base de datos.")

st.divider()

# --- 4. LÓGICA DE CARGA (EL FIX) ---
if st.session_state.codigo_mvp:
    # Traemos datos frescos de la DB
    res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_mvp).execute()
    
    if res_ficha.data:
        ficha_db = res_ficha.data[0]
        st.subheader(f"Viendo: {st.session_state.codigo_mvp}")

        # BOTONES DE CONTROL
        col1, col2 = st.columns(2)
        if col1.button("✏️ Modo Edición"):
            # Pasamos lo de la DB a la sesión para editar
            st.session_state.curva_mvp = ficha_db.get('curva_tallas', [])
            st.session_state.bloquear_mvp = False
            st.rerun()
            
        if col2.button("🔒 Modo Consulta"):
            st.session_state.bloquear_mvp = True
            st.rerun()

        # DETERMINAR QUÉ MOSTRAR
        # Si está bloqueado, usamos ficha_db (DATOS REALES)
        # Si está desbloqueado, usamos st.session_state (DATOS TEMPORALES)
        if st.session_state.bloquear_mvp:
            datos_finales = ficha_db.get('curva_tallas', [])
            st.info("👁️ Estás en MODO CONSULTA (Datos directos de Supabase)")
        else:
            datos_finales = st.session_state.curva_mvp
            st.warning("✍️ Estás en MODO EDICIÓN (Cambios no guardados aún)")

        # MOSTRAR TABLA
        if datos_finales:
            for idx, item in enumerate(datos_finales):
                c_talla, c_cant, c_accion = st.columns([2, 2, 1])
                c_talla.write(f"Talla: **{item['talla']}**")
                c_cant.write(f"Cant: {item['cantidad']}")
                
                if not st.session_state.bloquear_mvp:
                    if c_accion.button("🗑️", key=f"btn_del_{idx}"):
                        st.session_state.curva_mvp.pop(idx)
                        st.rerun()
        else:
            st.write("Esta ficha no tiene tallas registradas.")
            
        # AGREGAR (Solo en edición)
        if not st.session_state.bloquear_mvp:
            st.divider()
            st.write("Añadir nueva talla a la sesión:")
            nueva_t = st.text_input("Talla")
            if st.button("➕ Agregar"):
                st.session_state.curva_mvp.append({"talla": nueva_t, "cantidad": 1})
                st.rerun()
