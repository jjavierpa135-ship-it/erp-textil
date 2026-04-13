import streamlit as st
from supabase import create_client, Client

# --- 1. CONEXIÓN ---
# Asegúrate de tener SUPABASE_URL y SUPABASE_KEY en tus Secrets
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Error de conexión a la base de datos.")
    st.stop()

st.title("🧪 MVP: Sistema de Consulta y Carga Robusta")
st.markdown("Usa este programa para verificar que las tallas se guardan y consultan correctamente.")

# --- 2. ESTADOS DE SESIÓN ---
if 'bloquear_mvp' not in st.session_state:
    st.session_state.bloquear_mvp = True
if 'codigo_mvp' not in st.session_state:
    st.session_state.codigo_mvp = None
if 'curva_mvp' not in st.session_state:
    st.session_state.curva_mvp = []

# --- 3. BUSCADOR DE FICHAS ---
try:
    res = supabase.table("fichas_muestras").select("codigo_muestra, estilo").order("fecha_creacion", desc=True).limit(10).execute()
    opciones = {f"{r['codigo_muestra']} - {r['estilo']}": r['codigo_muestra'] for r in res.data}
    
    seleccion = st.selectbox("Selecciona una muestra existente:", ["Seleccionar..."] + list(opciones.keys()))
    
    if seleccion != "Seleccionar...":
        cod_sel = opciones[seleccion]
        if st.button("🔍 Cargar Ficha"):
            st.session_state.codigo_mvp = cod_sel
            st.session_state.bloquear_mvp = True  # Iniciar siempre en modo consulta
            st.session_state.curva_mvp = []       # Limpiar datos temporales
            st.rerun()
except:
    st.error("No se pudieron cargar muestras de Supabase.")

st.divider()

# --- 4. LÓGICA PRINCIPAL ---
if st.session_state.codigo_mvp:
    # 4.1 Obtener datos frescos de Supabase
    res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_mvp).execute()
    
    if res_ficha.data:
        ficha_db = res_ficha.data[0]
        st.subheader(f"Ficha Activa: {st.session_state.codigo_mvp}")

        # 4.2 Botones de Control de Estado
        col_c1, col_c2 = st.columns(2)
        
        if col_c1.button("✏️ Entrar a Modo Edición", use_container_width=True):
            # AL EDITAR: Volcamos lo que hay en DB a la sesión
            db_data = ficha_db.get('curva_tallas')
            st.session_state.curva_mvp = db_data if isinstance(db_data, list) else []
            st.session_state.bloquear_mvp = False
            st.rerun()
            
        if col_c2.button("🔒 Volver a Modo Consulta", use_container_width=True):
            st.session_state.bloquear_mvp = True
            st.rerun()

        st.divider()

        # 4.3 Determinación de Fuente de Datos (EL FIX)
        if st.session_state.bloquear_mvp:
            # MODO CONSULTA: Leemos directo del objeto de la base de datos
            raw_data = ficha_db.get('curva_tallas')
            datos_finales = raw_data if isinstance(raw_data, list) else []
            st.info("👁️ MODO CONSULTA: Mostrando datos grabados en Supabase.")
        else:
            # MODO EDICIÓN: Leemos de la variable temporal en sesión
            datos_finales = st.session_state.curva_mvp
            st.warning("✍️ MODO EDICIÓN: Estás modificando datos localmente.")

        # 4.4 Visualización de Datos
        if datos_finales:
            # Encabezados de tabla
            h1, h2, h3 = st.columns([2, 2, 1])
            h1.caption("TALLA")
            h2.caption("CANTIDAD")
            h3.caption("ACCIÓN")

            for idx, item in enumerate(datos_finales):
                if isinstance(item, dict) and 'talla' in item:
                    f1, f2, f3 = st.columns([2, 2, 1])
                    f1.write(f"**{item['talla']}**")
                    f2.write(f"{item.get('cantidad', 0)} uds")
                    
                    # Solo mostrar botón eliminar en edición
                    if not st.session_state.bloquear_mvp:
                        if f3.button("🗑️", key=f"del_{idx}"):
                            st.session_state.curva_mvp.pop(idx)
                            st.rerun()
        else:
            st.write("La ficha no tiene tallas registradas o el formato es incorrecto.")

        # 4.5 Herramientas de Edición (Solo visibles en Modo Edición)
        if not st.session_state.bloquear_mvp:
            st.divider()
            st.markdown("### 🛠️ Herramientas de Edición")
            
            c_add1, c_add2, c_add3 = st.columns([2, 2, 1])
            nueva_t = c_add1.text_input("Nueva Talla (ej: 30, L, M)")
            nueva_c = c_add2.number_input("Cant.", min_value=1, value=1)
            
            if c_add3.button("➕ Añadir"):
                if nueva_t:
                    st.session_state.curva_mvp.append({"talla": nueva_t, "cantidad": nueva_c})
                    st.rerun()
                else:
                    st.error("Escribe una talla.")

            st.divider()
            # BOTÓN PARA GRABAR EN DB
            if st.button("💾 GUARDAR CAMBIOS EN SUPABASE", type="primary", use_container_width=True):
                try:
                    supabase.table("fichas_muestras").update({
                        "curva_tallas": st.session_state.curva_mvp
                    }).eq("codigo_muestra", st.session_state.codigo_mvp).execute()
                    
                    st.success("¡Datos guardados con éxito! Cambiando a modo consulta...")
                    st.session_state.bloquear_mvp = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

else:
    st.info("Selecciona una muestra arriba para empezar la prueba.")
