import streamlit as st

# --- SIMULACIÓN DE BASE DE DATOS ---
# Esto representa lo que ya está guardado en Supabase
DB_FICTICIA = {
    "codigo": "M-2401",
    "tallas": [{"talla": "30", "cantidad": 2}, {"talla": "32", "cantidad": 1}],
    "insumos": [{"nombre": "Botón", "cant": 5}]
}

st.title("Prueba de Concepto: Consulta vs Edición")

# --- ESTADO DE SESIÓN ---
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
if 'tallas_temp' not in st.session_state:
    st.session_state.tallas_temp = []

# --- BOTONES DE CONTROL ---
col1, col2 = st.columns(2)
if col1.button("✏️ Editar"):
    # AL EDITAR: Cargamos lo de la DB a la sesión para poder manipularlo
    st.session_state.tallas_temp = DB_FICTICIA["tallas"].copy()
    st.session_state.bloquear = False
    st.rerun()

if col2.button("🔒 Consultar (Bloquear)"):
    st.session_state.bloquear = True
    st.rerun()

st.divider()

# --- LÓGICA DE LA SOLUCIÓN ---
# Decidimos qué fuente de datos usar ANTES de mostrar nada
if st.session_state.bloquear:
    datos_a_mostrar = DB_FICTICIA["tallas"]
    st.info("MODO CONSULTA: Viendo datos de la Base de Datos")
else:
    datos_a_mostrar = st.session_state.tallas_temp
    st.warning("MODO EDICIÓN: Viendo datos temporales de la Sesión")

# --- VISUALIZACIÓN ---
st.subheader("Lista de Tallas/Insumos")

if datos_a_mostrar:
    for idx, item in enumerate(datos_a_mostrar):
        c_a, c_b = st.columns([3, 1])
        c_a.write(f"📍 {item['talla']} - Cantidad: {item['cantidad']}")
        
        # El botón de eliminar SOLO aparece en edición
        if not st.session_state.bloquear:
            if c_b.button("🗑️", key=f"del_{idx}"):
                st.session_state.tallas_temp.pop(idx)
                st.rerun()
else:
    st.write("No hay datos.")

# --- AGREGAR (Solo en edición) ---
if not st.session_state.bloquear:
    st.divider()
    st.write("Añadir nueva talla:")
    nueva_t = st.text_input("Talla")
    nueva_c = st.number_input("Cantidad", min_value=1)
    if st.button("Añadir"):
        st.session_state.tallas_temp.append({"talla": nueva_t, "cantidad": nueva_c})
        st.rerun()
