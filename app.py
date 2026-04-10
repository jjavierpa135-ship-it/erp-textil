import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="ERP Pilar Jeans - Javier", page_icon="👗", layout="wide")

# --- CONEXIÓN A SUPABASE (SECRETS) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error de conexión a la base de datos: {e}")
    st.stop()

# --- BARRA LATERAL (MENÚ DE NAVEGACIÓN) ---
st.sidebar.title("🏢 ERP Pilar Jeans")
st.sidebar.subheader("Gestión Operativa")

menu_opciones = [
    "👗 Diseño (Ficha Muestra)",
    "✂️ Producción (Corte/Taller)",
    "📦 Almacén",
    "🧾 Facturación/SUNAT",
    "💰 Finanzas/Bancos"
]

modulo_actual = st.sidebar.radio("Ir a:", menu_opciones)

# ==========================================
# MÓDULO 1: DISEÑO (FICHA DE MUESTRAS)
# ==========================================
if modulo_actual == "👗 Diseño (Ficha Muestra)":
    st.title("👗 Desarrollo de Muestras y Patronaje")
    
    tab1, tab2 = st.tabs(["📝 Registrar Nueva Muestra", "🔍 Consultar Historial"])

    # --- TAB 1: REGISTRAR ---
    with tab1:
        with st.form("form_registro_muestra", clear_on_submit=True):
            st.subheader("Datos Generales y Personal")
            c1, c2, c3 = st.columns(3)
            with c1:
                modelo = st.text_input("Nombre del Modelo / Estilo", placeholder="Ej: Casaca Denim Ariana")
                disenadora = st.selectbox("Diseñadora Responsable", ["Ariana", "Otras"])
            with c2:
                patronista = st.selectbox("Patronista Responsable", ["Patronista 1", "Patronista 2"])
                tallas = st.text_input("Curva de Tallas", value="28-30-32-34-36")
            with c3:
                tipo_tela = st.text_input("Tipo de Tela", placeholder="Ej: Zef Strech")
                medida_cierre = st.text_input("Medida de Cierre")

            st.subheader("Especificaciones de Producción")
            c4, c5, c6 = st.columns(3)
            with c4:
                consumo = st.number_input("Consumo por prenda (metros)", format="%.2f", min_value=0.0)
            with c5:
                lavado = st.checkbox("¿Requiere Lavado Industrial?")
                proveedor_lavado = st.text_input("Proveedor / Lavandería")
            with c6:
                costo_lavado = st.number_input("Costo Lavado Muestra (S/.)", min_value=0.0)

            st.markdown("---")
            st.subheader("📸 Archivos y Documentación")
            col_files1, col_files2 = st.columns(2)
            with col_files1:
                foto_ref = st.file_uploader("Foto de Referencia (Imagen)", type=['png', 'jpg', 'jpeg'])
            with col_files2:
                ficha_tecnica = st.file_uploader("Ficha de Elaboración (PDF o Imagen Técnica)", type=['pdf', 'png', 'jpg'])
            
            observaciones = st.text_area("Observaciones de la Contramuestra")

            st.markdown("---")
            submit = st.form_submit_button("🚀 INICIAR PATRONAJE Y GUARDAR", type="primary")

            if submit:
                if not modelo:
                    st.error("⚠️ El nombre del modelo es obligatorio.")
                else:
                    try:
                        url_foto = ""
                        url_ficha = ""
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

                        # 1. Subir Foto de Referencia a Storage
                        if foto_ref:
                            path_foto = f"fotos/{timestamp}_{foto_ref.name}"
                            supabase.storage.from_("erp_pilar").upload(path_foto, foto_ref.getvalue())
                            url_foto = supabase.storage.from_("erp_pilar").get_public_url(path_foto)

                        # 2. Subir Ficha Técnica a Storage
                        if ficha_tecnica:
                            path_ficha = f"fichas/{timestamp}_{ficha_tecnica.name}"
                            supabase.storage.from_("erp_pilar").upload(path_ficha, ficha_tecnica.getvalue())
                            url_ficha = supabase.storage.from_("erp_pilar").get_public_url(path_ficha)

                        # 3. Insertar en Base de Datos
                        datos_insert = {
                            "modelo": modelo,
                            "disenadora_responsable": disenadora,
                            "patronista_responsable": patronista,
                            "estado": "Patronaje",
                            "fecha_inicio_patronaje": datetime.datetime.now().isoformat(),
                            "tipo_tela": tipo_tela,
                            "tallas": tallas,
                            "consumo_prenda": consumo,
                            "medida_cierre": medida_cierre,
                            "requiere_lavado": lavado,
                            "proveedor_lavado": proveedor_lavado,
                            "costo_lavado_muestra": costo_lavado,
                            "url_foto_referencia": url_foto,
                            "url_ficha_elaboracion": url_ficha,
                            "observaciones_contra": observaciones
                        }

                        supabase.table("fichas_muestras").insert(datos_insert).execute()
                        st.success(f"✅ ¡Estilo '{modelo}' registrado correctamente! El tiempo de patronaje ha empezado a contar.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")

    # --- TAB 2: CONSULTAR ---
    with tab2:
        st.subheader("Buscador de Fichas y Tiempos")
        try:
            # Consultamos los datos reales de Supabase
            res = supabase.table("fichas_muestras").select("*").order("fecha_creacion", desc=True).execute()
            df = pd.DataFrame(res.data)
            
            if not df.empty:
                # Mostrar tabla resumida
                st.dataframe(df[["modelo", "disenadora_responsable", "patronista_responsable", "estado", "fecha_creacion"]])
                
                # Selector para ver detalle
                modelo_sel = st.selectbox("Selecciona un modelo para ver detalles y fotos:", df["modelo"].tolist())
                detalle = df[df["modelo"] == modelo_sel].iloc[0]
                
                c_det1, c_det2 = st.columns(2)
                with c_det1:
                    if detalle["url_foto_referencia"]:
                        st.image(detalle["url_foto_referencia"], caption="Foto de Referencia", use_column_width=True)
                with c_det2:
                    st.write(f"**Diseñadora:** {detalle['disenadora_responsable']}")
                    st.write(f"**Patronista:** {detalle['patronista_responsable']}")
                    st.write(f"**Tela:** {detalle['tipo_tela']}")
                    st.write(f"**Estado Actual:** {detalle['estado']}")
                    if detalle["url_ficha_elaboracion"]:
                        st.link_button("📄 Ver Ficha de Elaboración", detalle["url_ficha_elaboracion"])
            else:
                st.info("Aún no hay fichas registradas.")
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

# ==========================================
# OTROS MÓDULOS (PRÓXIMAMENTE)
# ==========================================
else:
    st.title(modulo_actual)
    st.info("Módulo en construcción. Próximamente integraremos las funciones de este departamento.")
