# ... (Todo el código anterior igual hasta la sección de GUARDAR)

            with b1:
                if st.button("💾 Guardar", use_container_width=True, disabled=ya_enviado):
                    if "Seleccionar..." in [val_cat, val_est, val_dis]:
                        st.error("Por favor complete todos los campos obligatorios.")
                    else:
                        cod = st.session_state.codigo_actual
                        if cod == "S/C":
                            def generar_codigo(c, e):
                                return f"{c[:3].upper()}-{e[:3].upper()}-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
                            cod = generar_codigo(val_cat, val_est)
                        
                        # Payload con los campos adicionales
                        payload = {
                            "codigo_muestra": cod, 
                            "categoria": val_cat, 
                            "estilo": val_est,
                            "disenadora": val_dis,     # Asegúrate que en Supabase se llame igual
                            "prioridad": val_prior,    # Asegúrate que en Supabase se llame igual
                            "patronista_responsable": val_pat, 
                            "observaciones_contra": val_obs, 
                            "estado": "Borrador"
                        }
                        
                        try:
                            # Intento de guardado
                            supabase.table("fichas_muestras").upsert(payload, on_conflict="codigo_muestra").execute()
                            st.session_state.codigo_actual = cod
                            st.session_state.bloquear = True
                            st.success(f"Ficha Guardada: {cod}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error de base de datos: {e}")
                            st.info("💡 Verifica que las columnas 'disenadora' y 'prioridad' existan en Supabase.")

# ... (Resto del código igual)
