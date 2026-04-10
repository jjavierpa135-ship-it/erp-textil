with tab_diseno:
        # --- CAMBIO CLAVE: Si es ficha nueva, datos_f DEBE estar vacío ---
        if st.session_state.codigo_actual == "S/C":
            datos_f = {} 
        else:
            res_ficha = supabase.table("fichas_muestras").select("*").eq("codigo_muestra", st.session_state.codigo_actual).execute()
            datos_f = res_ficha.data[0] if res_ficha.data else {}

        def detectar_cambio():
            st.session_state.cambios_sin_guardar = True

        # --- FORMULARIO ---
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                cat_lista = ["Pantalón", "Falda", "Blusa", "Casaca", "Polo"]
                # Forzamos índice 0 si no hay datos (Ficha Nueva)
                idx_cat = cat_lista.index(datos_f.get('categoria')) if datos_f.get('categoria') in cat_lista else 0
                cat = st.selectbox("Categoría", cat_lista, index=idx_cat, 
                                   key=f"cat_{st.session_state.form_id}", # La llave cambia al limpiar
                                   disabled=st.session_state.bloquear, on_change=detectar_cambio)
                
                est_lista = ["Skinny", "Mom Fit", "Oversize", "Straight", "Slim"]
                idx_est = est_lista.index(datos_f.get('estilo')) if datos_f.get('estilo') in est_lista else 0
                estilo = st.selectbox("Estilo / Fit", est_lista, index=idx_est, 
                                      key=f"est_{st.session_state.form_id}",
                                      disabled=st.session_state.bloquear, on_change=detectar_cambio)
            
            with c2:
                pat_lista = ["Patronista 1", "Patronista 2", "Patronista 3"]
                idx_pat = pat_lista.index(datos_f.get('patronista_responsable')) if datos_f.get('patronista_responsable') in pat_lista else 0
                patronista = st.selectbox("Asignar a Patronista", pat_lista, index=idx_pat, 
                                          key=f"pat_{st.session_state.form_id}",
                                          disabled=st.session_state.bloquear, on_change=detectar_cambio)
                
                # Para el texto, si es ficha nueva, el valor es vacío obligatoriamente
                obs_val = datos_f.get('observaciones_contra', "")
                obs = st.text_area("Notas Técnicas", value=obs_val, 
                                   key=f"obs_{st.session_state.form_id}",
                                   disabled=st.session_state.bloquear, on_change=detectar_cambio)
