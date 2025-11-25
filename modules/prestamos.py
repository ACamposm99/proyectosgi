import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta
from utils.calculos_financieros import calcular_cuotas_prestamo, validar_capacidad_pago
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
    """Mostrar préstamos activos del grupo - FUNCIÓN MEJORADA"""
    
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
                    # En una implementación real, redirigiría al módulo de pagos
                    st.info("🔗 Esta función redirigiría al módulo de pagos")
            with col2:
                if st.button("📋 Ver Detalle", key=f"detalle_{prestamo['id_prestamo']}"):
                    mostrar_detalle_prestamo(prestamo['id_prestamo'])
            with col3:
                if st.button("🔄 Refinanciar", key=f"refin_{prestamo['id_prestamo']}"):
                    refinanciar_prestamo(prestamo['id_prestamo'])
    else:
        st.info("ℹ️ No hay préstamos activos en este grupo")

def historial_prestamos():
    """Historial completo de préstamos del grupo - FUNCIÓN MEJORADA"""
    
    st.subheader("Historial de Préstamos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver el historial")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estado = st.selectbox("Filtrar por estado", ["Todos", "Activos", "Pagados", "En Mora", "Rechazados"])
    
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
    
    if not historial.empty:
        # Mostrar estadísticas
        st.markdown("### 📊 Estadísticas del Período")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_prestamos = len(historial)
            st.metric("📝 Total Préstamos", total_prestamos)
        
        with col2:
            monto_total = historial['monto_solicitado'].sum()
            st.metric("💰 Monto Total", f"${monto_total:,.2f}")
        
        with col3:
            promedio_prestamo = historial['monto_solicitado'].mean()
            st.metric("📊 Promedio", f"${promedio_prestamo:,.2f}")
        
        with col4:
            tasa_aprobacion = (historial[historial['estado'].isin(['Aprobado', 'Pagado'])].shape[0] / total_prestamos * 100) if total_prestamos > 0 else 0
            st.metric("✅ Tasa Aprobación", f"{tasa_aprobacion:.1f}%")
        
        # Mostrar tabla
        st.markdown("### 📋 Detalle de Préstamos")
        st.dataframe(historial, use_container_width=True)
        
        # Gráfico de distribución por estado
        st.markdown("### 📈 Distribución por Estado")
        
        distribucion_estado = historial['estado'].value_counts()
        fig_estado = px.pie(
            values=distribucion_estado.values,
            names=distribucion_estado.index,
            title="Distribución de Préstamos por Estado"
        )
        st.plotly_chart(fig_estado, use_container_width=True)
        
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
# FUNCIONES AUXILIARES - PRÉSTAMOS (TODAS IMPLEMENTADAS)
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
    """Aprobar un préstamo - FUNCIÓN MEJORADA"""
    
    # Obtener información del préstamo para calcular fechas
    prestamo_info = ejecutar_consulta("""
        SELECT plazo_meses FROM prestamo WHERE id_prestamo = %s
    """, (id_prestamo,))
    
    if not prestamo_info:
        return False
    
    plazo_meses = prestamo_info[0]['plazo_meses']
    
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
    fecha_vencimiento = fecha_aprobacion + timedelta(days=30 * plazo_meses)
    
    # Crear el plan de pagos
    if ejecutar_comando(query, (fecha_aprobacion, fecha_desembolso, fecha_vencimiento, id_prestamo)):
        return crear_plan_pagos(id_prestamo)
    
    return False

def crear_plan_pagos(id_prestamo):
    """Crear plan de pagos para un préstamo aprobado"""
    
    # Obtener información del préstamo
    prestamo_info = ejecutar_consulta("""
        SELECT p.monto_solicitado, p.plazo_meses, p.fecha_desembolso,
               r.interes, s.id_grupo
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        JOIN reglas_del_grupo r ON s.id_grupo = r.id_grupo
        WHERE p.id_prestamo = %s
    """, (id_prestamo,))
    
    if not prestamo_info:
        return False
    
    prestamo = prestamo_info[0]
    monto = prestamo['monto_solicitado']
    plazo = prestamo['plazo_meses']
    tasa_interes = prestamo['interes'] / 100
    fecha_inicio = prestamo['fecha_desembolso']
    
    # Calcular cuotas
    cuotas_info = calcular_cuotas_prestamo(monto, tasa_interes, plazo)
    cuota_mensual = cuotas_info['cuota_mensual']
    
    # Crear registros de pagos programados
    for i in range(plazo):
        fecha_pago = fecha_inicio + timedelta(days=30 * (i + 1))
        
        query = """
            INSERT INTO `detalle de pagos` (
                id_prestamo, fecha_programada, capital_programado,
                interes_programado, total_programado, cuota_mensual
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        capital_cuota = cuotas_info['amortizacion'][i]['capital']
        interes_cuota = cuotas_info['amortizacion'][i]['interes']
        total_cuota = capital_cuota + interes_cuota
        
        if not ejecutar_comando(
            query, 
            (id_prestamo, fecha_pago, capital_cuota, interes_cuota, total_cuota, cuota_mensual)
        ):
            return False
    
    return True

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
    """Obtener historial de préstamos con filtros - FUNCIÓN MEJORADA"""
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
            p.proposito,
            COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0) as capital_pagado,
            (p.monto_solicitado - COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0)) as saldo_pendiente,
            COALESCE((
                SELECT COUNT(*) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NOT NULL
            ), 0) as pagos_realizados
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
        elif estado == "Rechazados":
            query += " AND p.id_estado_prestamo = 3"
    
    query += " ORDER BY p.fecha_solicitud DESC"
    
    resultado = ejecutar_consulta(query, params)
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def mostrar_detalle_prestamo(id_prestamo):
    """Mostrar detalle completo de un préstamo - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener información básica del préstamo
    prestamo_info = ejecutar_consulta("""
        SELECT 
            p.*,
            s.nombre,
            s.apellido,
            s.telefono,
            ep.estados as estado_prestamo,
            r.interes as tasa_interes
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        JOIN estado_del_prestamo ep ON p.id_estado_prestamo = ep.id_estadoprestamo
        JOIN reglas_del_grupo r ON s.id_grupo = r.id_grupo
        WHERE p.id_prestamo = %s
    """, (id_prestamo,))
    
    if not prestamo_info:
        st.error("❌ No se encontró información del préstamo")
        return
    
    prestamo = prestamo_info[0]
    
    st.subheader(f"📋 Detalle del Préstamo #{id_prestamo}")
    
    # Información básica
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 Información del Socio")
        st.write(f"**Nombre:** {prestamo['nombre']} {prestamo['apellido']}")
        st.write(f"**Teléfono:** {prestamo['telefono']}")
        st.write(f"**Estado:** {prestamo['estado_prestamo']}")
        
        st.markdown("### 💰 Información del Préstamo")
        st.write(f"**Monto Solicitado:** ${prestamo['monto_solicitado']:,.2f}")
        st.write(f"**Plazo:** {prestamo['plazo_meses']} meses")
        st.write(f"**Tasa de Interés:** {prestamo['tasa_interes']}%")
    
    with col2:
        st.markdown("### 📅 Fechas Importantes")
        st.write(f"**Solicitud:** {prestamo['fecha_solicitud'].strftime('%d/%m/%Y')}")
        
        if prestamo['fecha_aprobacion']:
            st.write(f"**Aprobación:** {prestamo['fecha_aprobacion'].strftime('%d/%m/%Y')}")
        
        if prestamo['fecha_desembolso']:
            st.write(f"**Desembolso:** {prestamo['fecha_desembolso'].strftime('%d/%m/%Y')}")
        
        if prestamo['fecha_vencimiento']:
            st.write(f"**Vencimiento:** {prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')}")
            
            # Calcular días restantes/hasta vencimiento
            hoy = datetime.now().date()
            dias_restantes = (prestamo['fecha_vencimiento'].date() - hoy).days
            if dias_restantes > 0:
                st.write(f"**Días hasta vencimiento:** {dias_restantes}")
            else:
                st.write(f"**Días de mora:** {abs(dias_restantes)}")
        
        if prestamo['proposito']:
            st.markdown("### 🎯 Propósito")
            st.write(prestamo['proposito'])
    
    # Historial de pagos
    st.markdown("### 💵 Historial de Pagos")
    
    pagos = ejecutar_consulta("""
        SELECT 
            fecha_programada,
            fecha_pago,
            capital_pagado,
            interes_pagado,
            mora_pagada,
            total_pagado,
            CASE 
                WHEN fecha_pago IS NULL THEN 'Pendiente'
                WHEN fecha_pago > fecha_programada THEN 'En mora'
                ELSE 'Al día'
            END as estado_pago
        FROM `detalle de pagos`
        WHERE id_prestamo = %s
        ORDER BY fecha_programada
    """, (id_prestamo,))
    
    if pagos:
        df_pagos = pd.DataFrame(pagos)
        
        # Métricas de pagos
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_pagado = df_pagos['total_pagado'].sum()
            st.metric("💰 Total Pagado", f"${total_pagado:,.2f}")
        
        with col2:
            pagos_realizados = df_pagos[df_pagos['fecha_pago'].notnull()].shape[0]
            st.metric("✅ Pagos Realizados", pagos_realizados)
        
        with col3:
            pagos_pendientes = df_pagos[df_pagos['fecha_pago'].isnull()].shape[0]
            st.metric("📋 Pagos Pendientes", pagos_pendientes)
        
        with col4:
            saldo_pendiente = prestamo['monto_solicitado'] - df_pagos['capital_pagado'].sum()
            st.metric("📊 Saldo Pendiente", f"${saldo_pendiente:,.2f}")
        
        # Tabla de pagos
        st.dataframe(df_pagos, use_container_width=True)
        
        # Gráfico de progreso de pago
        st.markdown("### 📈 Progreso del Préstamo")
        
        # Calcular porcentaje pagado
        porcentaje_pagado = (df_pagos['capital_pagado'].sum() / prestamo['monto_solicitado']) * 100
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = porcentaje_pagado,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Porcentaje Pagado"},
            delta = {'reference': 100},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("ℹ️ No se han registrado pagos para este préstamo")

def refinanciar_prestamo(id_prestamo):
    """Refinanciar un préstamo activo - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener información actual del préstamo
    prestamo_info = ejecutar_consulta("""
        SELECT 
            p.id_prestamo,
            p.monto_solicitado,
            p.plazo_meses,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_pendiente,
            s.nombre,
            s.apellido,
            r.interes as tasa_interes_actual
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        JOIN reglas_del_grupo r ON s.id_grupo = r.id_grupo
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE p.id_prestamo = %s
        GROUP BY p.id_prestamo
    """, (id_prestamo,))
    
    if not prestamo_info:
        st.error("❌ No se encontró información del préstamo")
        return
    
    prestamo = prestamo_info[0]
    saldo_actual = prestamo['saldo_pendiente']
    
    st.subheader(f"🔄 Refinanciar Préstamo #{id_prestamo}")
    st.write(f"**Socio:** {prestamo['nombre']} {prestamo['apellido']}")
    st.write(f"**Saldo Actual:** ${saldo_actual:,.2f}")
    st.write(f"**Plazo Actual:** {prestamo['plazo_meses']} meses")
    st.write(f"**Tasa de Interés Actual:** {prestamo['tasa_interes_actual']}%")
    
    with st.form(f"form_refinanciar_{id_prestamo}"):
        st.markdown("### Configurar Nuevos Términos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_plazo = st.slider(
                "⏱️ Nuevo Plazo (meses)",
                min_value=1,
                max_value=36,
                value=min(24, prestamo['plazo_meses'] + 6),
                help="Seleccione el nuevo plazo para el préstamo"
            )
            
            nueva_tasa_interes = st.number_input(
                "📈 Nueva Tasa de Interés (%)",
                min_value=0.0,
                max_value=50.0,
                value=float(prestamo['tasa_interes_actual']),
                step=0.5,
                help="Tasa de interés para la refinanciación"
            )
        
        with col2:
            # Calcular nueva cuota
            nueva_cuota_info = calcular_cuotas_prestamo(
                saldo_actual, 
                nueva_tasa_interes / 100, 
                nuevo_plazo
            )
            
            st.metric("💵 Nueva Cuota Mensual", f"${nueva_cuota_info['cuota_mensual']:,.2f}")
            st.metric("📈 Total a Pagar", f"${nueva_cuota_info['total_pagar']:,.2f}")
            
            fecha_refinanciacion = st.date_input(
                "📅 Fecha de Refinanciación",
                datetime.now()
            )
        
        motivo_refinanciacion = st.text_area(
            "📝 Motivo de la Refinanciación",
            placeholder="Describa el motivo de la refinanciación...",
            help="Explique por qué se solicita la refinanciación del préstamo"
        )
        
        condiciones_especiales = st.text_area(
            "⚙️ Condiciones Especiales",
            placeholder="Especifique cualquier condición especial del nuevo acuerdo...",
            help="Condiciones adicionales acordadas para la refinanciación"
        )
        
        if st.form_submit_button("💾 Refinanciar Préstamo"):
            # Validar que el socio tenga capacidad de pago con la nueva cuota
            capacidad = validar_capacidad_pago(
                prestamo_info[0]['id_socio'],
                saldo_actual,
                nuevo_plazo,
                st.session_state.id_grupo
            )
            
            if not capacidad['aprobado']:
                st.error(f"❌ No se puede refinanciar: {capacidad['mensaje']}")
                return
            
            # Actualizar el préstamo en la base de datos
            if actualizar_terminos_prestamo(
                id_prestamo, 
                nuevo_plazo, 
                nueva_tasa_interes, 
                nueva_cuota_info['cuota_mensual'],
                motivo_refinanciacion,
                condiciones_especiales,
                fecha_refinanciacion
            ):
                st.success("✅ Préstamo refinanciado exitosamente")
                st.info("🔄 El plan de pagos ha sido actualizado con los nuevos términos")
            else:
                st.error("❌ Error al refinanciar el préstamo")

def actualizar_terminos_prestamo(id_prestamo, nuevo_plazo, nueva_tasa, nueva_cuota, motivo, condiciones, fecha_refinanciacion):
    """Actualizar los términos del préstamo en la base de datos"""
    
    # Primero, crear un registro de refinanciación
    query_refin = """
        INSERT INTO refinanciaciones (
            id_prestamo, fecha_refinanciacion, nuevo_plazo, 
            nueva_tasa_interes, nueva_cuota_mensual, motivo, condiciones
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    if not ejecutar_comando(
        query_refin,
        (id_prestamo, fecha_refinanciacion, nuevo_plazo, nueva_tasa, nueva_cuota, motivo, condiciones)
    ):
        return False
    
    # Actualizar el préstamo principal
    query_update = """
        UPDATE prestamo 
        SET plazo_meses = %s,
            fecha_vencimiento = %s,
            id_estado_prestamo = 7  -- Refinanciado
        WHERE id_prestamo = %s
    """
    
    nueva_fecha_vencimiento = fecha_refinanciacion + timedelta(days=30 * nuevo_plazo)
    
    return ejecutar_comando(
        query_update,
        (nuevo_plazo, nueva_fecha_vencimiento, id_prestamo)
    )