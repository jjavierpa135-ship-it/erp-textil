import streamlit as st
from supabase import create_client, Client

# Conexión
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📦 Almacén de Telas - Ingreso de Rollos")

# 1. Obtener telas del maestro para el selector
res_maestro = supabase.table("maestro_telas").select("nombre_interno").execute()
lista_telas = [t['nombre_interno'] for t in res_maestro.data] if res_maestro.data else []

with st.form("registro_rollo"):
    st.subheader("Datos del Rollo Físico")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tela_sel = st.selectbox("Seleccionar Tela", lista_telas)
        lote = st.text_input("Código de Lote / Partida")
    with col2:
        metraje = st.number_input("Metraje (m)", min_value=0.0)
        ancho = st.number_input("Ancho Útil (m)", min_value=0.0, value=1.50)
    with col3:
        peso = st.number_input("Peso Bruto (kg)", min_value=0.0)
        precio = st.number_input("Precio Factura ($/m)", min_value=0.0)

    st.divider()
    st.subheader("Datos de Facturación (Cuentas por Pagar)")
    cf1, cf2 = st.columns(2)
    factura = cf1.text_input("Número de Factura")
    vencimiento = cf2.date_input("Fecha de Vencimiento de Pago")

    if st.form_submit_button("📥 Registrar Ingreso de Rollo"):
        data = {
            "nombre_tela": tela_sel,
            "codigo_lote": lote,
            "metraje_ingreso": metraje,
            "ancho_util": ancho,
            "peso_bruto_kg": peso,
            "precio_compra_metro": precio,
            "nro_factura": factura,
            "fecha_vencimiento_pago": str(vencimiento)
        }
        supabase.table("inventario_rollos").insert(data).execute()
        st.success("Rollo registrado y cuenta por pagar proyectada.")