import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- CONEXIÓN A BASE DE DATOS (Se mantiene igual) ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error conexión: {e}"); st.stop()

# --- MEJORA PUNTO 1: LÓGICA DE IDENTIFICACIÓN ---
def generar_codigo_pilar(categoria, estilo):
    """Genera código automático: CAT-EST-AÑO-CORRELATIVO"""
    prefijo = f"{categoria[:3].upper()}-{estilo[:3].upper()}"
    fecha_slug = datetime.datetime.now().strftime("%y%m%d%H%M")
    return f"{prefijo}-{fecha_slug}"

st.title("👗 Módulo de Diseño y Patronaje")

# Pestañas para separar el flujo de trabajo
tab_diseno, tab_patronaje = st.tabs(["🎨 Diseñadora (Crear)", "📐 Patronista (Ejecutar)"])

# --- VISTA DE LA DISEÑADORA ---
with tab_diseno:
    st.subheader("Nueva Ficha de Muestra")
    with st.form("form_diseno_pilar"):
        c1, c2 = st.columns(2)
        with c1:
            cat = st.selectbox("Categoría de Prenda", ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"])
            estilo_nom = st.text_input("Nombre del Estilo", placeholder="Ej: Skinny High Waist")
            disenadora = st.selectbox("Diseñadora Responsable", ["Ariana", "Otras"])
        
        with c2:
            cliente = st.text_input("Cliente / Marca", value="Pilar Jeans")
            fecha_hoy = st.date_input("Fecha de Creación", datetime.date.today())
            # El código se genera internamente al guardar
            st.info("El código correlativo se generará automáticamente al enviar.")

        observaciones_diseno = st.text_area("Notas para la Patronista")
        
        btn_enviar = st.form_submit_button("✅ ENVIAR A PATRONAJE")

        if btn_enviar:
            if estilo_nom:
                nuevo_codigo = generar_codigo_pilar(cat, estilo_nom)
                datos = {
                    "codigo_muestra": nuevo_codigo,
                    "categoria": cat,
                    "estilo": estilo_nom,
                    "disenadora_responsable": disenadora,
                    "estado": "Pendiente Patronaje", # Estado inicial
                    "fecha_creacion": str(fecha_hoy),
                    "observaciones_contra": observaciones_diseno
                }
                # Guardamos en Supabase
                supabase.table("fichas_muestras").insert(datos).execute()
                st.success(f"Ficha {nuevo_codigo} enviada con éxito. ¡Buen trabajo, {disenadora}!")
            else:
                st.warning("Por favor, ingresa el nombre del estilo.")

# --- VISTA DE LA PATRONISTA ---
with tab_patronaje:
    st.subheader("Fichas Pendientes por Iniciar")
    # Buscamos solo las fichas que están en estado 'Pendiente'
    pendientes = supabase.table("fichas_muestras").select("*").eq("estado", "Pendiente Patronaje").execute()
    
    if pendientes.data:
        df_pend = pd.DataFrame(pendientes.data)
        for _, fila in df_pend.iterrows():
            with st.expander(f"📌 Muestra: {fila['codigo_muestra']} - {fila['estilo']}"):
                st.write(f"**Diseñada por:** {fila['disenadora_responsable']}")
                st.write(f"**Notas:** {fila['observaciones_contra']}")
                
                if st.button(f"🚀 Iniciar Cronómetro: {fila['codigo_muestra']}"):
                    # Actualizamos estado y grabamos la hora de inicio real
                    hora_inicio = datetime.datetime.now().isoformat()
                    supabase.table("fichas_muestras").update({
                        "estado": "En Patronaje",
                        "fecha_inicio_patronaje": hora_inicio
                    }).eq("codigo_muestra", fila['codigo_muestra']).execute()
                    st.rerun() # Refresca para que pase al siguiente estado
    else:
        st.info("No hay fichas pendientes por ahora. ¡Día despejado!")
