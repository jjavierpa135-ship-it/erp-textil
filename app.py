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
def generar_codigo(cat, est):
    # Crea código tipo PANT-SKI-001 basado en categoría y estilo
    prefix = f"{cat[:3].upper()}-{est[:3].upper()}"
    return f"{prefix}-{datetime.datetime.now().strftime('%M%S')}"

# --- MENÚ LATERAL ---
modulo = st.sidebar.radio("Módulos", ["👗 Ficha de Muestras", "👥 Proveedores"])

if modulo == "👗 Ficha de Muestras":
    st.title("👗 Desarrollo de Ficha Técnica")
    tab1, tab2 = st.tabs(["📝 Registro Técnico", "🔍 Historial"])

    with tab1:
        with st.form("form_pilar"):
            # SECCIÓN 1: Identificación
            st.subheader("1. Identificación de Estilo")
            c1, c2, c3 = st.columns(3)
            with c1:
                cat = st.selectbox("Categoría", ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"])
                est = st.text_input("Estilo", placeholder="Ej: Skinny")
            with c2:
                disenadora = st.selectbox("Diseñadora", ["Ariana", "Otras"])
                patronista = st.selectbox("Patronista", ["Patronista 1", "Patronista 2"])
            with c3:
                codigo = generar_codigo(cat, est)
                st.info(f"Código sugerido: {codigo}")

            # SECCIÓN 2: Ingeniería de Tallas y Cantidades
            st.subheader("2. Curva de Tallas y Cálculo")
            c4, c5, c6 = st.columns(3)
            with c4:
                tallas_sel = st.multiselect("Tallas", ["26", "28", "30", "32", "34", "36"], default=["28", "30", "32"])
            with c5:
                ratio = st.text_input("Ratio (Ej: 2,2,1)", value="1,1,1")
                series = st.number_input("Cantidad de Series", min_value=1, value=1)
            with c6:
                # Lógica de cálculo: suma ratio * series
                total_prendas = sum([int(x) for x in ratio.split(',') if x.strip().isdigit()]) * series
                st.metric("Total Prendas a Cortar", total_prendas)

            # SECCIÓN 3: Materiales y Proveedores
            st.subheader("3. Materiales e Insumos")
            c7, c8 = st.columns(2)
            with c7:
                t_pri = st.text_input("Tela Principal")
                t_com = st.text_input("Tela Complementaria")
            with c8:
                # Jalamos proveedores de la tabla que creaste
                prov_res = supabase.table("proveedores").select("nombre").execute()
                lista_prov = [p['nombre'] for p in prov_res.data]
                prov_sel = st.selectbox("Proveedor de Tela", lista_prov if lista_prov else ["Sin proveedores"])
                insumos = st.text_area("Otros Insumos (Botones, hilos, remaches...)")

            # SECCIÓN 4: Gestión Visual (Moodboard)
            st.subheader("4. Moodboard y Archivos")
            f1, f2, f3, f4 = st.columns(4)
            with f1: img_ref = st.file_uploader("Foto Referencia", type=['jpg','png'])
            with f2: img_col = st.file_uploader("Foto Color", type=['jpg','png'])
            with f3: img_bor = st.file_uploader("Foto Bordado", type=['jpg','png'])
            with f4: pdf_tec = st.file_uploader("Ficha PDF", type=['pdf'])

            # BOTÓN DE GUARDADO
            if st.form_submit_button("🚀 GUARDAR Y EMPEZAR PATRONAJE"):
                # (Aquí va la lógica de subida a Storage y INSERT en DB similar a la anterior)
                st.success("Ficha técnica creada y tiempos de patronista en marcha.")

    with tab2:
        st.write("Aquí verás el historial con las miniaturas de lo que subas.")

elif modulo == "👥 Proveedores":
    st.title("👥 Gestión de Proveedores")
    # Formulario simple para añadir nuevos proveedores a tu lista
    with st.form("nuevo_prov"):
        n = st.text_input("Nombre de Empresa")
        t = st.selectbox("Tipo", ["Lavandería", "Telas", "Insumos", "Taller"])
        if st.form_submit_button("Añadir Proveedor"):
            supabase.table("proveedores").insert({"nombre": n, "tipo": t}).execute()
            st.success("Proveedor añadido.")
