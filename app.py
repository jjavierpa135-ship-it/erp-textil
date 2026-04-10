import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ INICIAL ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- 2. CONEXIÓN A BASE DE DATOS ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Error de conexión"); st.stop()

# --- 3. MEMORIA DE ESTADO (Session State) ---
# Controla si los campos están bloqueados y qué código estamos viendo
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = False
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "S/C"

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    return f"{prefijo}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"

def nueva_ficha():
    # Limpia la memoria para empezar desde cero
    st.session_state.bloquear = False
    st.session_state.codigo_actual = "S/C"
    st.rerun()

# --- 5. BARRA LATERAL (Menú que mencionaste) ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Menú Principal", ["👗 Diseño y Patronaje", "📦 Almacén", "👥 Proveedores"])

# --- 6. LÓGICA DEL MÓDULO DE DISEÑO ---
if modulo == "👗 Diseño y Patronaje":
    
    # Cabecera superior con Código y botón Nueva Ficha
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Gestión de Muestras")
    with col_c: st.metric("Código en Pantalla", st.session_state.codigo_actual)
    with col_b: 
        if st.button("➕ Nueva Ficha (Limpiar)"): nueva_ficha()

    # Pestañas para Diseñadora y Patronista
    tab_diseno, tab_patronaje = st.tabs(["🎨 Área de Diseño", "📐 Área de Patronaje"])

    with tab_diseno:
        # --- BUSCADOR PARA MODIFICAR ---
        with st.expander("🔍 Buscar Ficha Existente para Modificar"):
            cod_busqueda = st.text_input("Ingrese código exacto (Ej: PAN-SKI-...)")
            if st.button("Buscar y Cargar"):
                res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", cod_busqueda).execute()
                if res.data:
                    ficha = res.data[0]
                    st.session_state.codigo_actual = ficha['codigo_muestra']
                    st.session_state.bloquear = False # Desbloqueamos para editar
                    st.success(f"Ficha {cod_busqueda} cargada. Puedes modificarla abajo.")
                else:
                    st.error("No se encontró esa ficha.")

        st.markdown("---")

        # --- FORMULARIO DE EDICIÓN / REGISTRO ---
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                categoria = st.selectbox("Categoría", ["Pantalón", "Falda", "Blusa", "Casaca"], disabled=st.session_state.bloquear)
                estilo = st.selectbox("Estilo", ["Skinny", "Mom Fit", "Slim", "Oversize"], disabled=st.session_state.bloquear)
                disenadora = st.selectbox("Diseñadora", ["Ariana", "Otras"], disabled=st.session_state.bloquear)
            
            with c2:
                cliente = st.selectbox("Cliente / Marca", ["Pilar Jeans", "Externo"], disabled=st.session_state.bloquear)
                patronista = st.selectbox("Asignar a", ["Patronista 1", "Patronista 2"], disabled=st.session_state.bloquear)
                obs = st.text_area("Notas Técnicas", disabled=st.session_state.bloquear)

            # Botones de Acción
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("💾 Solo Guardar (Borrador)", disabled=st.session_state.bloquear, use_container_width=True):
                    # Si es ficha nueva, genera código. Si es búsqueda, mantiene el código.
                    if st.session_state.codigo_actual == "S/C":
                        st.session_state.codigo_actual = generar_codigo(categoria, estilo)
                    
                    datos = {
                        "codigo_muestra": st.session_state.codigo_actual,
                        "categoria": categoria, "estilo": estilo,
                        "disenadora_responsable": disenadora,
                        "patronista_responsable": patronista,
                        "estado": "Borrador", "observaciones_contra": obs
                    }
                    # upsert: inserta si no existe, actualiza si ya existe el código
                    supabase.table("fichas_muestras").upsert(datos, on_conflict="codigo_muestra").execute()
                    st.session_state.bloquear = True
                    st.success("Guardado correctamente.")
                    st.rerun()

            with b2:
                if st.button("🚀 Enviar a Patronaje", use_container_width=True):
                    if st.session_state.codigo_actual == "S/C":
                        st.error("Primero guarda para generar un código.")
                    else:
                        supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                        st.success("Enviado. Ahora la patronista puede verlo.")

            with b3:
                if st.button("✏️ Habilitar Edición", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab_patronaje:
        # --- VISTA PARA LA PATRONISTA ---
        st.subheader("Bandeja de Entrada (Tareas Asignadas)")
        # Solo mostramos lo que NO es borrador y está pendiente
        pendientes = supabase.table("fichas_muestras").select("*").eq("estado", "Pendiente Patronaje").execute()
        
        if pendientes.data:
            for p in pendientes.data:
                with st.expander(f"📋 {p['codigo_muestra']} - {p['estilo']}"):
                    st.write(f"Asignado a: {p['patronista_responsable']}")
                    if st.button(f"Iniciar Cronómetro {p['codigo_muestra']}"):
                        st.info("Cronómetro iniciado. (Lógica de tiempo en el Punto 3)")
        else:
            st.write("No hay trabajos pendientes de envío.")

else:
    st.title(modulo)
    st.write("Próximamente...")
