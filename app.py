import streamlit as st
import requests

# 1. Credenciales (Asegúrate de que la llave sea la GIGANTE que sacaste de service_role)
URL_TABLA = st.secrets["SUPABASE_URL"] + "/rest/v1/fichas_muestras"
LLAVE_GIGANTE = st.secrets["SUPABASE_KEY"]

st.set_page_config(page_title="ERP Textil", page_icon="🧵")

st.title("🧵 Registro de Producción")

# 2. Interfaz de usuario
nombre_modelo = st.text_input("Nombre del Modelo (ej: Camisa Denim)")

if st.button("ENVIAR A LA NUBE", type="primary"):
    if nombre_modelo:
        # Preparamos la "maleta" con los datos y las llaves
        headers = {
            "apikey": LLAVE_GIGANTE,
            "Authorization": f"Bearer {LLAVE_GIGANTE}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        payload = {"modelo": nombre_modelo}
        
        try:
            # Enviamos el dato directamente por HTTP (así evitamos el error de 'proxy')
            response = requests.post(URL_TABLA, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                st.balloons()
                st.success(f"✅ ¡'{nombre_modelo}' guardado con éxito!")
            else:
                st.error(f"Error de respuesta: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"Fallo crítico de conexión: {e}")
    else:
        st.warning("Escribe un nombre antes de enviar.")
