import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- CONEXIÓN A BASE DE DATOS ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error conexión: {e}"); st.stop()

# --- MEMORIA DE LA APP (SESSION STATE) ---
# Inicializamos el código y un disparador para limpiar el formulario
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "S/C" # S/C = Sin Código

def limpiar_formulario():
    # Esta función borra el código y prepara la app para una nueva entrada
    st.session_state.codigo_actual = "S/C"
    # st.rerun() se usa para refrescar la pantalla inmediatamente
    st.rerun()

# --- FUNCIONES DE APOYO ---
def generar_codigo_pilar(categoria, estilo):
    # Genera el código técnico basado en el momento exacto
    prefijo = f"{categoria[:3].upper()}-{estilo[:3].upper()}"
    fecha_slug = datetime.datetime.now().strftime("%y%m%d%H%M")
    return f"{prefijo}-{fecha_slug}"

st.title("👗 Módulo de Diseño y Patronaje")

tab_diseno, tab_patronaje = st.tabs(["🎨 Diseñadora (Crear)", "📐 Patronista (Ejecutar)"])

# --- VISTA DE LA DISEÑADORA ---
with tab_diseno:
    # Cabecera con Código a la derecha y Botón de Limpiar
    col_titulo, col_codigo, col_limpiar = st.columns([2, 1, 1])
    with col_titulo:
        st.subheader("Nueva Ficha de Muestra")
    with col_codigo:
        # Mostramos el código generado de forma llamativa
        st.metric("Código Generado", st.session_state.codigo_actual)
    with col_limpiar:
        # Botón para resetear todo el trabajo
        if st.button("➕ Nueva Ficha (Limpiar)"):
            limpiar_formulario()

    # Formulario de Registro
    with st.form("form_diseno_pilar", clear_on_submit=True):
        c1, c2 = st.columns(2)
        
        with c1:
            cat = st.selectbox("Categoría de Prenda", ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"])
            estilo_nom = st.selectbox("Estilo / Fit", ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim", "Flare"])
            disenadora = st.selectbox("Diseñadora Responsable", ["Ariana", "Otras"])
        
        with c2:
            cliente = st.selectbox("Cliente / Marca", ["Pilar Jeans", "Marca Blanca", "Exportación"])
            patronista_asignada = st.selectbox("Asignar a Patronista", ["Patronista 1", "Patronista 2", "Patronista 3"])
            fecha_hoy = st.date_input("Fecha de Creación", datetime.date.today())

        observaciones_diseno = st.text_area("Instrucciones técnicas para el molde")
        
        # Botón de Enviar
        btn_enviar = st.form_submit_button("✅ ENVIAR A PATRONAJE")

        if btn_enviar:
            # Generamos el código y lo guardamos en la 'memoria' para que aparezca arriba
            nuevo_cod = generar_codigo_pilar(cat, estilo_nom)
            st.session_state.codigo_actual = nuevo_cod
            
            datos = {
                "codigo_muestra": nuevo_cod,
                "categoria": cat,
                "estilo": estilo_nom,
                "disenadora_responsable": disenadora,
                "patronista_responsable": patronista_asignada,
                "estado": "Pendiente Patronaje",
                "fecha_creacion": str(fecha_hoy),
                "observaciones_contra": observaciones_diseno
            }
            
            try:
                supabase.table("fichas_muestras").insert(datos).execute()
                st.success(f"Ficha {nuevo_cod} registrada. Código visible en cabecera.")
                # Forzamos refresco para actualizar el st.metric de arriba
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- VISTA DE LA PATRONISTA (Se mantiene igual para no romper el flujo) ---
with tab_patronaje:
    st.info("Bandeja de entrada lista para recibir asignaciones.")
