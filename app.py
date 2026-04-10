import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- 2. CONEXIÓN A SUPABASE ---
try:
    # Asegúrate de tener estas credenciales en tu archivo secrets.toml o en Streamlit Cloud
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión a la base de datos: {e}")
    st.stop()

# --- 3. GESTIÓN DE ESTADOS (Session State) ---
# 'bloquear': Controla si los campos son editables o solo lectura
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = True
# 'codigo_actual': Muestra el código de la muestra en pantalla
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "Cargando..."
# 'cambios_sin_guardar': Bloquea el envío a patronaje si hay ediciones pendientes
if 'cambios_sin_guardar' not in st.session_state:
    st.session_state.cambios_sin_guardar = False
# 'form_id': Llave dinámica para forzar el reinicio visual de los selectores
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0

# --- 4. FUNCIONES DE APOYO ---
def generar_codigo(cat, est):
    """Genera un código único basado en categoría, estilo y tiempo real."""
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    marca_tiempo = datetime.datetime.now().strftime('%y%m%d%H%M')
    return f"{prefijo}-{marca_tiempo}"

def nueva_ficha():
    """Limpia la memoria y fuerza el reseteo del formulario."""
    st.session_state.bloquear = False
    st.session_state.codigo_actual = "S/C"
    st.session_state.cambios_sin_guardar = False
    st.session_state.form_id += 1 # Al cambiar, Streamlit recrea los widgets vacíos
    st.rerun()

def cargar_ultima_muestra():
    """Busca en Supabase el último registro creado."""
    try:
        res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).limit(1).execute()
        if res.data:
            ficha = res.data[0]
            st.session_state.codigo_actual = ficha['codigo_muestra']
            return ficha
    except:
        pass
    return None

# --- 5. LÓGICA DE ARRANQUE ---
if st.session_state.codigo_actual == "Cargando...":
    ultima = cargar_ultima_muestra()
    if not ultima:
        st.session_state.codigo_actual = "S/C"

# --- 6. BARRA LATERAL (MENÚ) ---
st.sidebar.title("🏢 ERP Pilar Jeans")
modulo = st.sidebar.radio("Navegación", ["👗 Diseño y Patronaje", "📦 Almacén", "👥 Proveedores"])

# --- 7. MÓDULO PRINCIPAL: DISEÑO Y PATRONAJE ---
if modulo == "👗 Diseño y Patronaje":
    
    # Cabecera con Métricas y Control
    col_t, col_c, col_b = st.columns([2, 1, 1])
    with col_t: st.title("Gestión de Muestras")
    with col_c: st.metric("Código Activo", st.session_state.codigo_actual)
    with col_b: 
        if st.button("➕ Nueva Ficha (Limpiar)"):
            nueva_ficha()

    # Pestañas de Trabajo
    tab_diseno, tab_patronaje = st.tabs(["🎨 Área de Diseño", "📐 Área de Patronaje"])

    with tab_diseno:
        # LÓGICA DE CARGA DE DATOS: 
        # Si es "S/C" (Ficha nueva), vaciamos datos_f para que el formulario salga en blanco.
        if st.session_state.codigo_actual == "S/C":
            datos_f = {}
        else:
            res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            datos_f = res_ficha.data[0] if res_ficha.data else {}

        def detectar_cambio():
            st.session_state.cambios_sin_guardar = True

        # CONTENEDOR DEL FORMULARIO
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                # Listas de opciones
                cat_lista = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
                # Calculamos el índice para mostrar el valor guardado o el primero (0)
                idx_cat = cat_lista.index(datos_f.get('categoria')) if datos_f.get('categoria') in cat_lista else 0
                cat = st.selectbox("Categoría", cat_lista, index=idx_cat, 
                                   key=f"cat_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear, on_change=detectar_cambio)
                
                est_lista = ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
                idx_est = est_lista.index(datos_f.get('estilo')) if datos_f.get('estilo') in est_lista else 0
                estilo = st.selectbox("Estilo / Fit", est_lista, index=idx_est, 
                                      key=f"est_{st.session_state.form_id}",
                                      disabled=st.session_state.bloquear, on_change=detectar_cambio)
            
            with c2:
                pat_lista = ["Patronista 1", "Patronista 2", "Patronista 3"]
                idx_pat = pat_lista.index(datos_f.get('patronista_responsable')) if datos_f.get('patronista_responsable') in pat_lista else 0
                patronista = st.selectbox("Asignar a Patronista", pat_lista, index=idx_pat, 
                                          key=f"pat_{st.session_state.form_id}",
                                          disabled=st.session_state.bloquear, on_change=detectar_cambio)
                
                obs_val = datos_f.get('observaciones_contra', "")
                obs = st.text_area("Notas Técnicas", value=obs_val, 
                                   key=f"obs_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear, on_change=detectar_cambio)

            st.markdown("---")
            
            # BOTONES DE ACCIÓN
            b1, b2, b3 = st.columns(3)
            
            with b1:
                # Botón Guardar: Crea o Actualiza en la base de datos
                if st.button("💾 Guardar Cambios", use_container_width=True):
                    if st.session_state.codigo_actual == "S/C":
                        st.session_state.codigo_actual = generar_codigo(cat, estilo)
                    
                    datos_up = {
                        "codigo_muestra": st.session_state.codigo_actual,
                        "categoria": cat, 
                        "estilo": estilo,
                        "patronista_responsable": patronista,
                        "observaciones_contra": obs,
                        "estado": "Borrador" # Estado inicial oculto para patronistas
                    }
                    supabase.table("fichas_muestras").upsert(datos_up, on_conflict="codigo_muestra").execute()
                    st.session_state.bloquear = True
                    st.session_state.cambios_sin_guardar = False
                    st.success(f"Ficha {st.session_state.codigo_actual} guardada.")
                    st.rerun()

            with b2:
                # Botón Enviar: Solo activo si no hay cambios pendientes de guardado
                bloqueo_envio = st.session_state.cambios_sin_guardar or st.session_state.codigo_actual == "S/C"
                if st.button("🚀 Enviar a Patronaje", use_container_width=True, disabled=bloqueo_envio):
                    supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"}).eq("codigo_muestra", st.session_state.codigo_actual).execute()
                    st.success("Enviado con éxito.")
                if st.session_state.cambios_sin_guardar:
                    st.caption("⚠️ Debes guardar los cambios antes de enviar.")

            with b3:
                # Botón Modificar: Desbloquea los campos para edición
                if st.button("✏️ Habilitar Edición", use_container_width=True):
                    st.session_state.bloquear = False
                    st.rerun()

    with tab_patronaje:
        st.subheader("Bandeja de Entrada para Patronistas")
        # Mostramos solo lo que ya fue "Enviado"
        pendientes = supabase.table("fichas_muestras").select("*").eq("estado", "Pendiente Patronaje").execute()
        
        if pendientes.data:
            for p in pendientes.data:
                with st.expander(f"📋 {p['codigo_muestra']} | {p['categoria']} {p['estilo']}"):
                    st.write(f"**Asignado a:** {p['patronista_responsable']}")
                    st.write(f"**Notas:** {p['observaciones_contra']}")
                    if st.button(f"Iniciar Cronómetro: {p['codigo_muestra']}"):
                        st.info("Iniciando registro de tiempos...")
        else:
            st.info("No hay fichas pendientes en esta bandeja.")

else:
    # Contenido para Almacén o Proveedores
    st.title(modulo)
    st.write("Sección en desarrollo.")
