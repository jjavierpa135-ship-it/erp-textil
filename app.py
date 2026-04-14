import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="ERP Pilar Jeans", page_icon="👗", layout="wide")

try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Error de conexión: {e}"); st.stop()

# --- 2. ESTADOS DE SESIÓN ---
if 'codigo_actual' not in st.session_state: st.session_state.codigo_actual = "S/C"
if 'bloquear' not in st.session_state: st.session_state.bloquear = True
if 'insumos_temp' not in st.session_state: st.session_state.insumos_temp = []
if 'form_id' not in st.session_state: st.session_state.form_id = 0

# --- 3. CARGA DE DATOS ---
datos_db = {}
if st.session_state.codigo_actual != "S/C":
    res = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
    if res.data:
        datos_db = res.data[0]
        if not st.session_state.insumos_temp:
            st.session_state.insumos_temp = datos_db.get('insumos_detalle') or []

# --- 4. INTERFAZ: SECCIÓN 3 (TELAS E INSUMOS) ---
st.header("3. Telas e Insumos")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    # Listas de opciones
    lista_telas = ["Seleccionar...", "Denim 12oz", "Denim 10oz", "Gabardina", "Jersey", "Tocuyo"]
    
    with col1:
        val_tela_p = st.selectbox(
            "Tela Principal", 
            lista_telas, 
            index=lista_telas.index(datos_db.get('tela_principal')) if datos_db.get('tela_principal') in lista_telas else 0,
            disabled=st.session_state.bloquear
        )
    
    with col2:
        val_tela_c = st.selectbox(
            "Tela Complemento", 
            lista_telas, 
            index=lista_telas.index(datos_db.get('tela_complemento')) if datos_db.get('tela_complemento') in lista_telas else 0,
            disabled=st.session_state.bloquear
        )

    st.divider()
    st.write("**Detalle de Insumos:**")

    # --- CÁLCULO DE COSTO SEGURO ---
    total_insumos = 0.0
    if st.session_state.insumos_temp:
        for item in st.session_state.insumos_temp:
            try:
                # Forzamos conversión a float para evitar el TypeError
                cant = float(item.get('cantidad', 0))
                prec = float(item.get('precio', 0.0))
                total_insumos += (cant * prec)
                
                # Mostrar fila de insumo
                c_ins1, c_ins2, c_ins3 = st.columns([3, 1, 1])
                c_ins1.write(f"🔹 {item.get('codigo')}")
                c_ins2.write(f"{cant} unid.")
                c_ins3.write(f"${prec:.2f}")
            except:
                continue

    st.metric("COSTO TOTAL INSUMOS", f"${total_insumos:.2f}")

# --- 5. BOTÓN GUARDAR (Corrección de NameError) ---
st.divider()
if st.button("💾 Guardar Todo", use_container_width=True):
    # Definimos todas las variables necesarias para el payload
    # Si alguna no existe en tu formulario actual, usa un valor por defecto o datos_db.get()
    
    payload = {
        "codigo_muestra": st.session_state.codigo_actual,
        "tela_principal": val_tela_p,
        "tela_complemento": val_tela_c,
        "insumos_detalle": st.session_state.insumos_temp,
        # Aquí agregamos las que daban error por no estar definidas:
        "prioridad": datos_db.get('prioridad', 'Normal'),
        "patronista_responsable": datos_db.get('patronista_responsable', 'Sin Asignar'),
        "observaciones_contra": datos_db.get('observaciones_contra', ''),
        "estado": "Borrador"
    }
    
    try:
        supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
        st.success("¡Datos actualizados correctamente!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar en Supabase: {e}")
