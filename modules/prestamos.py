import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta
from utils.calculos_financieros import calcular_cuotas_prestamo, validar_capacidad_pago

def modulo_prestamos():
    """Módulo principal para gestión de préstamos"""
    
    st.header("🏦 Gestión de Préstamos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Nueva Solicitud", "✅ Aprobar Préstamos", "📊 Préstamos Activos", "📋 Historial"])
    
    with tab1:
        nueva_solicitud_prestamo()
    
    with tab2:
        aprobar_prestamos()
    
    with tab3:
        prestamos_activos()
    
    with tab4:
        historial_prestamos()

def nueva_solicitud_prestamo():
    """Formulario para nueva solicitud de préstamo"""
    
    st.subheader("Nueva Solicitud de Préstamo")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo socios de un grupo pueden solicitar préstamos")
        return
    
    with st.form("form_solicitud_prestamo"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleccionar socio solicitante
            socios = obtener_socios_grupo(st.session_state.id_grupo)
            id_socio = st.selectbox(
                "👤 Socio Solicitante",
                options=[(s['id_socio'], f"{s['nombre']} {s['apellido']}") for s in socios],
                format_func=lambda x: x[1]
            )
            
            monto_solicitado = st.number_input(
                "💰 Monto Solicitado",
                min_value=0.0,
                step=100.0,
                value=1000.0
            )
            
            plazo_meses = st.slider(
                "📅 Plazo (meses)",
                min_value=1,
                max_value=24,
                value=12
            )
        
        with col2:
            # Información de capacidad de pago
            st.markdown("### 📊 Capacidad de Pago")
            
            # Obtener información del socio
            if id_socio:
                info_socio = obtener_info_socio(id_socio[0])
                if info_socio:
                    st.write(f"**Saldo de ahorro:** ${info_socio['saldo_ahorro']:,.2f}")
                    st.write(f"**Préstamos activos:** {info_socio['prestamos_activos']}")
                    
                    # Verificar capacidad de pago
                    capacidad = validar_capacidad_pago(
                        id_socio[0], 
                        monto_solicitado, 
                        plazo_meses,
                        st.session_state.id_grupo
                    )
                    
                    if capacidad['aprobado']:
                        st.success("✅ Capacidad de pago adecuada")
                    else:
                        st.error(f"❌ {capacidad['mensaje']}")
            
            proposito = st.text_area(
                "🎯 Propósito del Préstamo",
                placeholder="Describa el propósito del préstamo..."
            )
        
        # Cálculo de cuotas preliminar
        if monto_solicitado > 0 and plazo_meses > 0:
            st.markdown("### 📈 Simulación de Pagos")
            
            # Obtener tasa de interés del grupo
            tasa_interes = obtener_tasa_interes_grupo(st.session_state.id_grupo)
            
            if tasa_interes:
                cuotas = calcular_cuotas_prestamo(monto_solicitado, tasa_interes, plazo_meses)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Cuota Mensual", f"${cuotas['cuota_mensual']:,.2f}")
                with col2:
                    st.metric("📈 Interés Total", f"${cuotas['interes_total']:,.2f}")
                with col3:
                    st.metric("💰 Total a Pagar", f"${cuotas['total_pagar']:,.2f}")
                
                # Mostrar tabla de amortización
                with st.expander("📋 Ver Tabla de Amortización"):
                    for i, cuota in enumerate(cuotas['amortizacion']):
                        st.write(f"Mes {i+1}: Capital ${cuota['capital']:,.2f} | Interés ${cuota['interes']:,.2f} | Saldo ${cuota['saldo']:,.2f}")
        
        submitted = st.form_submit_button("📨 Enviar Solicitud")
        
        if submitted:
            if id_socio and monto_solicitado > 0 and proposito:
                # Validaciones adicionales
                if not capacidad.get('aprobado', False):
                    st.error("❌ No se puede enviar la solicitud. Verifique la capacidad de pago.")
                    return
                
                # Verificar límite máximo de préstamo
                limite_maximo = obtener_limite_prestamo_grupo(st.session_state.id_grupo)
                if monto_solicitado > limite_maximo:
                    st.error(f"❌ El monto solicitado excede el límite máximo de ${limite_maximo:,.2f}")
                    return
                
                # Crear solicitud de préstamo
                id_prestamo = crear_solicitud_prestamo(
                    id_socio[0], monto_solicitado, plazo_meses, proposito,
                    st.session_state.id_grupo
                )
                
                if id_prestamo:
                    st.success("✅ Solicitud de préstamo enviada exitosamente")
                    st.info("📋 La solicitud será revisada por la directiva en la próxima reunión")
            else:
                st.error("❌ Complete todos los campos obligatorios")

def aprobar_prestamos():
    """Aprobación de solicitudes de préstamo por la directiva"""
    
    st.subheader("Aprobación de Solicitudes de Préstamo")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede aprobar préstamos")
        return
    
    # Obtener solicitudes pendientes
    solicitudes = obtener_solicitudes_pendientes(st.session_state.id_grupo)
    
    if not solicitudes:
        st.info("ℹ️ No hay solicitudes de préstamo pendientes")
        return
    
    st.markdown(f"### 📋 Solicitudes Pendientes ({len(solicitudes)})")
    
    for solicitud in solicitudes:
        with st.expander(f"📝 Solicitud #{solicitud['id_prestamo']} - {solicitud['nombre']} {solicitud['apellido']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Socio:** {solicitud['nombre']} {solicitud['apellido']}")
                st.write(f"**Monto Solicitado:** ${solicitud['monto_solicitado']:,.2f}")
                st.write(f"**Plazo:** {solicitud['plazo_meses']} meses")
                st.write(f"**Fecha Solicitud:** {solicitud['fecha_solicitud'].strftime('%d/%m/%Y')}")
            
            with col2:
                st.write(f"**Propósito:** {solicitud['proposito']}")
                st.write(f"**Saldo Ahorro:** ${solicitud['saldo_ahorro']:,.2f}")
                st.write(f"**Préstamos Activos:** {solicitud['prestamos_activos']}")
                
                # Información de capacidad de pago
                capacidad = validar_capacidad_pago(
                    solicitud['id_socio'],
                    solicitud['monto_solicitado'],
                    solicitud['plazo_meses'],
                    st.session_state.id_grupo
                )
                
                if capacidad['aprobado']:
                    st.success("✅ Capacidad de pago adecuada")
                else:
                    st.error(f"❌ {capacidad['mensaje']}")
            
            # Botones de aprobación/rechazo
            col_aprov, col_rech, col_info = st.columns([1, 1, 2])
            
            with col_aprov:
                if st.button("✅ Aprobar", key=f"aprobar_{solicitud['id_prestamo']}"):
                    if aprobar_prestamo(solicitud['id_prestamo']):
                        st.success("Préstamo aprobado exitosamente")
                        st.rerun()
            
            with col_rech:
                if st.button("❌ Rechazar", key=f"rechazar_{solicitud['id_prestamo']}"):
                    motivo = st.text_input("Motivo del rechazo", key=f"motivo_{solicitud['id_prestamo']}")
                    if st.button("Confirmar Rechazo", key=f"confirm_rech_{solicitud['id_prestamo']}"):
                        if rechazar_prestamo(solicitud['id_prestamo'], motivo):
                            st.success("Solicitud rechazada")
                            st.rerun()
            
            with col_info:
                # Verificar disponibilidad de caja
                disponible_caja = obtener_disponibilidad_caja(st.session_state.id_grupo)
                if disponible_caja < solicitud['monto_solicitado']:
                    st.warning(f"⚠️ Fondos insuficientes. Disponible: ${disponible_caja:,.2f}")

def prestamos_activos():
    """Mostrar préstamos activos del grupo"""
    
    st.subheader("Préstamos Activos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver préstamos activos")
        return
    
    prestamos = obtener_prestamos_activos_grupo(st.session_state.id_grupo)
    
    if prestamos:
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_activos = len(prestamos)
            st.metric("🏦 Préstamos Activos", total_activos)
        
        with col2:
            total_desembolsado = sum(p['monto_desembolsado'] for p in prestamos)
            st.metric("💰 Total Desembolsado", f"${total_desembolsado:,.2f}")
        
        with col3:
            total_saldo = sum(p['saldo_actual'] for p in prestamos)
            st.metric("📊 Saldo Pendiente", f"${total_saldo:,.2f}")
        
        with col4:
            en_mora = sum(1 for p in prestamos if p['dias_mora'] > 0)
            st.metric("⚠️ En Mora", en_mora)
        
        # Lista detallada
        st.markdown("### Detalle de Préstamos Activos")
        
        for prestamo in prestamos:
            color_borde = "red" if prestamo['dias_mora'] > 0 else "green"
            
            st.markdown(f"""
            <div style="border-left: 4px solid {color_borde}; padding-left: 15px; margin: 10px 0;">
                <h4>{prestamo['nombre']} {prestamo['apellido']} - ${prestamo['monto_desembolsado']:,.2f}</h4>
                <p><strong>Fecha desembolso:</strong> {prestamo['fecha_desembolso'].strftime('%d/%m/%Y')} | 
                   <strong>Vencimiento:</strong> {prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')}</p>
                <p><strong>Saldo actual:</strong> ${prestamo['saldo_actual']:,.2f} | 
                   <strong>Cuota mensual:</strong> ${prestamo['cuota_mensual']:,.2f}</p>
                <p><strong>Próximo pago:</strong> {prestamo['proximo_pago'].strftime('%d/%m/%Y')} | 
                   <strong>Días en mora:</strong> {prestamo['dias_mora']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💵 Registrar Pago", key=f"pago_{prestamo['id_prestamo']}"):
                    st.session_state.prestamo_seleccionado = prestamo['id_prestamo']
                    st.switch_page("pages/pagos.py")
            with col2:
                if st.button("📋 Ver Detalle", key=f"detalle_{prestamo['id_prestamo']}"):
                    mostrar_detalle_prestamo(prestamo['id_prestamo'])
            with col3:
                if st.button("🔄 Refinanciar", key=f"refin_{prestamo['id_prestamo']}"):
                    st.info("Funcionalidad en desarrollo")
    else:
        st.info("ℹ️ No hay préstamos activos en este grupo")

def historial_prestamos():
    """Historial completo de préstamos del grupo"""
    
    st.subheader("Historial de Préstamos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver el historial")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estado = st.selectbox("Filtrar por estado", ["Todos", "Activos", "Pagados", "En Mora"])
    
    with col2:
        fecha_inicio = st.date_input("Desde", datetime.now().replace(day=1))
    
    with col3:
        fecha_fin = st.date_input("Hasta", datetime.now())
    
    # Obtener historial
    historial = obtener_historial_prestamos(
        st.session_state.id_grupo, 
        estado, 
        fecha_inicio, 
        fecha_fin
    )
    
    if historial:
        st.dataframe(historial, use_container_width=True)
        
        # Exportar a CSV
        csv = historial.to_csv(index=False)
        st.download_button(
            label="📤 Exportar a CSV",
            data=csv,
            file_name=f"historial_prestamos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ No hay préstamos que coincidan con los filtros")

# =============================================================================
# FUNCIONES AUXILIARES - PRÉSTAMOS
# =============================================================================

def obtener_socios_grupo(id_grupo):
    """Obtener socios del grupo"""
    query = "SELECT id_socio, nombre, apellido FROM socios WHERE id_grupo = %s"
    return ejecutar_consulta(query, (id_grupo,))

def obtener_info_socio(id_socio):
    """Obtener información financiera del socio"""
    query = """
        SELECT 
            s.nombre,
            s.apellido,
            COALESCE((
                SELECT saldo_final 
                FROM ahorro_detalle ad 
                JOIN ahorro a ON ad.id_ahorro = a.id_ahorro 
                JOIN sesion se ON a.id_sesion = se.id_sesion 
                WHERE ad.id_socio = s.id_socio 
                ORDER BY se.fecha_sesion DESC 
                LIMIT 1
            ), 0) as saldo_ahorro,
            (
                SELECT COUNT(*) 
                FROM prestamo 
                WHERE id_socio = s.id_socio 
                AND id_estado_prestamo IN (2, 5)  -- Aprobado o En Mora
            ) as prestamos_activos
        FROM socios s
        WHERE s.id_socio = %s
    """
    resultado = ejecutar_consulta(query, (id_socio,))
    return resultado[0] if resultado else None

def obtener_tasa_interes_grupo(id_grupo):
    """Obtener tasa de interés del grupo"""
    query = "SELECT interes FROM reglas_del_grupo WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['interes'] / 100 if resultado else 0.05  # 5% por defecto

def obtener_limite_prestamo_grupo(id_grupo):
    """Obtener límite máximo de préstamo del grupo"""
    query = "SELECT montomax_prestamo FROM reglas_del_grupo WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['montomax_prestamo'] if resultado else 5000.0

def crear_solicitud_prestamo(id_socio, monto, plazo, proposito, id_grupo):
    """Crear nueva solicitud de préstamo"""
    
    # Obtener próxima sesión para aprobación
    proxima_sesion = obtener_proxima_sesion(id_grupo)
    
    query = """
        INSERT INTO prestamo (
            id_socio, fecha_solicitud, monto_solicitado, plazo_meses,
            proposito, id_estado_prestamo, id_sesion_aprobacion
        ) VALUES (%s, %s, %s, %s, %s, 1, %s)
    """
    
    return ejecutar_comando(
        query, 
        (id_socio, datetime.now(), monto, plazo, proposito, proxima_sesion)
    )

def obtener_solicitudes_pendientes(id_grupo):
    """Obtener solicitudes de préstamo pendientes"""
    query = """
        SELECT 
            p.id_prestamo,
            p.id_socio,
            s.nombre,
            s.apellido,
            p.monto_solicitado,
            p.plazo_meses,
            p.proposito,
            p.fecha_solicitud,
            COALESCE((
                SELECT saldo_final 
                FROM ahorro_detalle ad 
                JOIN ahorro a ON ad.id_ahorro = a.id_ahorro 
                JOIN sesion se ON a.id_sesion = se.id_sesion 
                WHERE ad.id_socio = s.id_socio 
                ORDER BY se.fecha_sesion DESC 
                LIMIT 1
            ), 0) as saldo_ahorro,
            (
                SELECT COUNT(*) 
                FROM prestamo 
                WHERE id_socio = s.id_socio 
                AND id_estado_prestamo IN (2, 5)
            ) as prestamos_activos
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 1  -- Pendiente
        ORDER BY p.fecha_solicitud DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def aprobar_prestamo(id_prestamo):
    """Aprobar un préstamo"""
    query = """
        UPDATE prestamo 
        SET id_estado_prestamo = 2,  -- Aprobado
            fecha_aprobacion = %s,
            fecha_desembolso = %s,
            fecha_vencimiento = %s
        WHERE id_prestamo = %s
    """
    
    fecha_aprobacion = datetime.now()
    fecha_desembolso = fecha_aprobacion
    fecha_vencimiento = fecha_aprobacion + timedelta(days=30)  # Aproximado
    
    return ejecutar_comando(
        query, 
        (fecha_aprobacion, fecha_desembolso, fecha_vencimiento, id_prestamo)
    )

def rechazar_prestamo(id_prestamo, motivo):
    """Rechazar un préstamo"""
    query = "UPDATE prestamo SET id_estado_prestamo = 3, motivo_rechazo = %s WHERE id_prestamo = %s"
    return ejecutar_comando(query, (motivo, id_prestamo))

def obtener_prestamos_activos_grupo(id_grupo):
    """Obtener préstamos activos del grupo"""
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            p.monto_solicitado as monto_desembolsado,
            p.fecha_desembolso,
            p.fecha_vencimiento,
            p.plazo_meses,
            COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0) as capital_pagado,
            (p.monto_solicitado - COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0)) as saldo_actual,
            COALESCE((
                SELECT cuota_mensual 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo 
                ORDER BY fecha_programada DESC 
                LIMIT 1
            ), p.monto_solicitado / p.plazo_meses) as cuota_mensual,
            COALESCE((
                SELECT MIN(fecha_programada) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NULL
            ), p.fecha_desembolso + INTERVAL 1 MONTH) as proximo_pago,
            GREATEST(0, DATEDIFF(CURDATE(), COALESCE((
                SELECT MIN(fecha_programada) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NULL
            ), p.fecha_desembolso + INTERVAL 1 MONTH))) as dias_mora
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo IN (2, 5)  -- Aprobado o En Mora
        ORDER BY p.fecha_desembolso DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_disponibilidad_caja(id_grupo):
    """Obtener disponibilidad de caja para préstamos"""
    query = """
        SELECT saldo_cierre 
        FROM caja c
        JOIN sesion s ON c.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['saldo_cierre'] if resultado else 0

def obtener_proxima_sesion(id_grupo):
    """Obtener la próxima sesión del grupo"""
    query = """
        SELECT id_sesion 
        FROM sesion 
        WHERE id_grupo = %s AND fecha_sesion >= CURDATE()
        ORDER BY fecha_sesion ASC
        LIMIT 1
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['id_sesion'] if resultado else None

def obtener_historial_prestamos(id_grupo, estado, fecha_inicio, fecha_fin):
    """Obtener historial de préstamos con filtros"""
    import pandas as pd
    
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            p.monto_solicitado,
            p.fecha_solicitud,
            p.fecha_aprobacion,
            p.fecha_desembolso,
            p.fecha_vencimiento,
            ep.estados as estado,
            p.plazo_meses,
            COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0) as capital_pagado,
            (p.monto_solicitado - COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0)) as saldo_pendiente
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        JOIN estado_del_prestamo ep ON p.id_estado_prestamo = ep.id_estadoprestamo
        WHERE s.id_grupo = %s
        AND p.fecha_solicitud BETWEEN %s AND %s
    """
    
    params = [id_grupo, fecha_inicio, fecha_fin]
    
    if estado != "Todos":
        if estado == "Activos":
            query += " AND p.id_estado_prestamo IN (2, 5)"
        elif estado == "Pagados":
            query += " AND p.id_estado_prestamo = 4"
        elif estado == "En Mora":
            query += " AND p.id_estado_prestamo = 5"
    
    query += " ORDER BY p.fecha_solicitud DESC"
    
    resultado = ejecutar_consulta(query, params)
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def mostrar_detalle_prestamo(id_prestamo):
    """Mostrar detalle completo de un préstamo"""
    st.info(f"🔧 Funcionalidad en desarrollo - Detalle préstamo #{id_prestamo}")