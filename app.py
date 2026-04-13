import streamlit as st
from supabase import create_client, Client
import json

# --- 1. CONEXIÓN ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Error de conexión"); st.stop()

st.title("🚀 Diagnóstico de Guardado")

# --- 2. ESTADOS ---
if 'codigo_mvp' not in st.session_state: st.session_state.codigo_mvp = None
if 'curva_mvp' not in st.session_state: st.session_state.curva_mvp = []
if 'modo_edicion' not in st.session_state: st.session_state.modo_edicion = False

# --- 3. SELECCIÓN ---
res = supabase.table("fichas_muestras").select("codigo_muestra, estilo").order("fecha_creacion", desc=True).limit(5).execute()
opciones = {f"{r['codigo_muestra']} - {r['estilo']}": r['codigo_muestra'] for r in res.data}
seleccion = st.selectbox("Selecciona ficha:", ["Seleccionar..."] + list(opciones.keys()))

if seleccion != "Seleccionar..." and st.button("🔍 Cargar Datos Reales"):
    cod = opciones[seleccion]
    res_f = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", cod).execute()
    if res_f.data:
        st.session_state.codigo_mvp = cod
        # CARGA SEGURA: Si es None o String, convertir a lista vacía
        raw_curva = res_f.data[0].get('curva_tallas')
        if isinstance(raw_curva, list):
            st.session_state.curva_mvp = raw_curva
        else:
            st.session_state.curva_mvp = []
        st.session_state.modo_edicion = False
        st.rerun()

st.divider()

# --- 4. ÁREA DE TRABAJO ---
if st.session_state.codigo_mvp:
    st.subheader(f"Ficha: {st.session_state.codigo_mvp}")
    
    if st.checkbox("🛠️ Activar Modo Edición"):
        st.session_state.modo_edicion = True
    else:
        st.session_state.modo_edicion = False

    # MOSTRAR DATOS ACTUALES
    st.write("### Datos en Memoria:")
    if st.session_state.curva_mvp:
        st.table(st.session_state.curva_mvp)
    else:
        st.info("La lista está vacía actualmente.")

    # AGREGAR TALLAS (Solo si modo edición está activo)
    if st.session_state.modo_edicion:
        with st.expander("Añadir Nueva Talla", expanded=True):
            col1, col2, col3 = st.columns(3)
            t = col1.text_input("Talla")
            c = col2.number_input("Cantidad", min_value=1, value=1)
            if col3.button("➕ Agregar a Lista"):
                st.session_state.curva_mvp.append({"talla": t, "cantidad": c})
                st.rerun()

        st.divider()
        
        # BOTÓN DE GUARDADO CRÍTICO
        if st.button("💾 GRABAR EN BASE DE DATOS", type="primary"):
            # DEBUG: Ver qué se envía
            st.write("Enviando a Supabase:", st.session_state.curva_mvp)
            
            try:
                # El truco: Asegurar que curva_tallas sea una lista limpia
                resultado = supabase.table("fichas_muestras").update({
                    "curva_tallas": st.session_state.curva_mvp 
                }).eq("codigo_muestra", st.session_state.codigo_mvp).execute()
                
                if resultado.data:
                    st.success("✅ ¡Guardado exitoso! Verifica en tu panel de Supabase.")
                else:
                    st.error("❌ Supabase no devolvió confirmación de guardado.")
            except Exception as e:
                st.error(f"❌ Error técnico al guardar: {e}")
