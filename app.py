import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

# --- CONEXIÓN ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Error conexión"); st.stop()

# --- MEMORIA DE ESTADO (Para bloquear campos y guardar datos) ---
if 'bloquear' not in st.session_state:
    st.session_state.bloquear = False # Si es True, no deja editar
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = "S/C"

# --- FUNCIONES ---
def generar_codigo(cat, est):
    prefijo = f"{cat[:3].upper()}-{est[:3].upper()}"
    return f"{prefijo}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"

def nueva_ficha():
    st.session_state.bloquear = False
    st.session_state.codigo_actual = "S/C"
    st.rerun()

# --- INTERFAZ CABECERA ---
col_t, col_c, col_b = st.columns([2, 1, 1])
with col_t: st.subheader("Gestión de Ficha Técnica")
with col_c: st.metric("Código Actual", st.session_state.codigo_actual)
with col_b: 
    if st.button("➕ Nueva Ficha / Limpiar"): nueva_ficha()

# --- FORMULARIO DE DISEÑO ---
# Usamos 'disabled' para bloquear los campos si ya se guardó
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        cat = st.selectbox("Categoría", ["Pantalón", "Falda", "Blusa"], disabled=st.session_state.bloquear)
        estilo = st.selectbox("Estilo", ["Skinny", "Mom Fit", "Slim"], disabled=st.session_state.bloquear)
        disenadora = st.selectbox("Diseñadora", ["Ariana", "Otras"], disabled=st.session_state.bloquear)
    
    with c2:
        cliente = st.selectbox("Cliente", ["Pilar Jeans", "Externo"], disabled=st.session_state.bloquear)
        patronista = st.selectbox("Asignar a", ["Patronista 1", "Patronista 2"], disabled=st.session_state.bloquear)
        obs = st.text_area("Observaciones", disabled=st.session_state.bloquear)

    st.markdown("---")
    
    # --- BOTONES DE ACCIÓN ---
    b1, b2, b3 = st.columns(3)
    
    with b1:
        # SOLO GUARDAR: Registra pero no lo envía a la patronista (Estado: Borrador)
        if st.button("💾 Solo Guardar", disabled=st.session_state.bloquear):
            nuevo_cod = generar_codigo(cat, estilo)
            st.session_state.codigo_actual = nuevo_cod
            st.session_state.bloquear = True # Bloqueamos campos
            
            datos = {
                "codigo_muestra": nuevo_cod, "categoria": cat, "estilo": estilo,
                "disenadora_responsable": disenadora, "patronista_responsable": patronista,
                "estado": "Borrador", "observaciones_contra": obs
            }
            supabase.table("fichas_muestras").insert(datos).execute()
            st.success("Guardado como borrador. Puedes seguir editando después (próximamente) o enviar ahora.")
            st.rerun()

    with b2:
        # ENVIAR A PATRONAJE: Cambia el estado para que aparezca en la otra pestaña
        if st.button("🚀 Enviar a Patronaje", help="La patronista podrá ver la ficha"):
            if st.session_state.codigo_actual == "S/C":
                st.error("Primero debes 'Guardar' para generar un código.")
            else:
                supabase.table("fichas_muestras").update({"estado": "Pendiente Patronaje"})\
                    .eq("codigo_muestra", st.session_state.codigo_actual).execute()
                st.success("Ficha enviada a la cola de trabajo de la patronista.")

    with b3:
        # MODIFICAR: Desbloquea los campos si necesitas corregir algo antes de enviar
        if st.button("✏️ Modificar Datos"):
            st.session_state.bloquear = False
            st.rerun()
