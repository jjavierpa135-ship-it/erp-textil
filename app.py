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

# --- FUNCIONES DE APOYO ---
def generar_codigo_pilar(categoria, estilo):
    # Genera código: CAT-EST-HORA (Ej: PAN-SKI-1430)
    prefijo = f"{categoria[:3].upper()}-{estilo[:3].upper()}"
    fecha_slug = datetime.datetime.now().strftime("%y%m%d%H%M")
    return f"{prefijo}-{fecha_slug}"

st.title("👗 Módulo de Diseño y Patronaje")

tab_diseno, tab_patronaje = st.tabs(["🎨 Diseñadora (Crear)", "📐 Patronista (Ejecutar)"])

# --- VISTA DE LA DISEÑADORA ---
with tab_diseno:
    st.subheader("Nueva Ficha de Muestra")
    with st.form("form_diseno_pilar"):
        c1, c2 = st.columns(2)
        
        with c1:
            # Ahora el Estilo y la Categoría son selectores para mantener el orden
            cat = st.selectbox("Categoría de Prenda", ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"])
            # El estilo define la especialidad (Skinny, Oversize, Slim, etc.)
            estilo_nom = st.selectbox("Estilo / Fit", ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim", "Flare"])
            disenadora = st.selectbox("Diseñadora Responsable", ["Ariana", "Otras"])
        
        with c2:
            # Selector de Cliente/Marca para evitar variaciones de nombre
            cliente = st.selectbox("Cliente / Marca", ["Pilar Jeans", "Cliente Externo A", "Marca Blanca"])
            
            # ASIGNACIÓN ESPECÍFICA: La diseñadora elige quién hará el molde
            patronista_asignada = st.selectbox("Asignar a Patronista", ["Patronista 1 (Denim)", "Patronista 2 (Punto)", "Patronista 3 (Sastrería)"])
            
            fecha_hoy = st.date_input("Fecha de Creación", datetime.date.today())

        observaciones_diseno = st.text_area("Notas e instrucciones técnicas para el molde")
        
        btn_enviar = st.form_submit_button("✅ ENVIAR A PATRONISTA ASIGNADA")

        if btn_enviar:
            nuevo_codigo = generar_codigo_pilar(cat, estilo_nom)
            datos = {
                "codigo_muestra": nuevo_codigo,
                "categoria": cat,
                "estilo": estilo_nom,
                "disenadora_responsable": disenadora,
                "patronista_responsable": patronista_asignada, # Guardamos quién debe hacerlo
                "estado": "Pendiente Patronaje",
                "fecha_creacion": str(fecha_hoy),
                "observaciones_contra": observaciones_diseno
            }
            try:
                supabase.table("fichas_muestras").insert(datos).execute()
                st.success(f"Ficha {nuevo_codigo} enviada directamente a {patronista_asignada}.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- VISTA DE LA PATRONISTA ---
with tab_patronaje:
    st.subheader("Bandeja de Entrada de Moldes")
    
    # Filtro opcional para que la patronista se busque a sí misma
    filtro_nombre = st.selectbox("Ver tareas de:", ["Patronista 1 (Denim)", "Patronista 2 (Punto)", "Patronista 3 (Sastrería)"])
    
    # Consultamos solo lo pendiente Y asignado a ella
    query = supabase.table("fichas_muestras").select("*")\
            .eq("estado", "Pendiente Patronaje")\
            .eq("patronista_responsable", filtro_nombre).execute()
    
    if query.data:
        for fila in query.data:
            with st.expander(f"📦 {fila['codigo_muestra']} | {fila['categoria']} {fila['estilo']}"):
                st.write(f"**Cliente:** {fila.get('cliente', 'Pilar Jeans')}")
                st.write(f"**Diseñado por:** {fila['disenadora_responsable']}")
                st.write(f"**Instrucciones:** {fila['observaciones_contra']}")
                
                if st.button(f"🚀 Iniciar mi trabajo: {fila['codigo_muestra']}"):
                    hora_inicio = datetime.datetime.now().isoformat()
                    supabase.table("fichas_muestras").update({
                        "estado": "En Patronaje",
                        "fecha_inicio_patronaje": hora_inicio
                    }).eq("codigo_muestra", fila['codigo_muestra']).execute()
                    st.rerun()
    else:
        st.info(f"No tienes tareas pendientes, {filtro_nombre}.")
