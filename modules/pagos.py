import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime
import pandas as pd

def modulo_pagos():
    """Módulo principal para registro de pagos"""
    
    st.header("💵 Registro de Pagos de Préstamos")
    
    tab1, tab2, tab3 = st.tabs(["📥 Registrar Pago", "📋 Historial de Pagos", "📊 Estado de Cuenta"])
    
    with tab1:
        registrar_pago()
    
    with tab2:
        historial_pagos()
    
    with tab3:
        estado_cuenta()

def registrar_pago():
    """Registrar pago de préstamo"""
    
    st.subheader("Registrar Pago de Préstamo")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede registrar pagos")
        return
    
    # Obtener préstamos activos del grupo
    prestamos = obtener_prestamos_activos_grupo(st.session_state.id_grupo)
    
    if not prestamos:
        st.info("ℹ️ No hay préstamos activos para registrar pagos")
        return
    
    # Seleccionar préstamo
    prestamo_seleccionado = st.selectbox(
        "Seleccionar Préstamo",
        options=[(p['id_prestamo'], f"{p['nombre']} {p['apellido']} - ${p['saldo_actual']:,.2f}") for p in prestamos],
        format_func=lambda x: x[1],
        key="select_prestamo_pago"
    )
    
    if not prestamo_seleccionado:
        return
    
    id_prestamo = prestamo_seleccionado[0]
    
    # Obtener información del préstamo
    info_prestamo = obtener_info_prestamo(id_prestamo)
    
    if info_prestamo:
        # Mostrar información del préstamo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Saldo Pendiente", f"${info_prestamo['saldo_pendiente']:,.2f}")
        
        with col2:
            st.metric("📅 Próximo Pago", info_prestamo['proximo_pago'].strftime('%d/%m/%Y'))
        
        with col3:
            st.metric("💵 Cuota Programada", f"${info_prestamo['cuota_programada']:,.2f}")
        
        # Obtener cuotas pendientes
        cuotas_pendientes = obtener_cuotas_pendientes(id_prestamo)
        
        if cuotas_pendientes:
            st.markdown("### 📋 Cuotas Pendientes")
            
            for cuota in cuotas_pendientes:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**Cuota #{cuota['numero_cuota']}** - Vence: {cuota['fecha_programada'].strftime('%d/%m/%Y')}")
                
                with col2:
                    st.write(f"Capital: ${cuota['capital']:,.2f}")
                
                with col3:
                    st.write(f"Interés: ${cuota['interes']:,.2f}")
                
                with col4:
                    if st.button("💳 Pagar", key=f"pagar_{cuota['id_pago']}"):
                        procesar_pago_cuota(cuota['id_pago'], info_prestamo)
        else:
            st.info("ℹ️ No hay cuotas pendientes para este préstamo")
        
        # Pago parcial o adelantado
        st.markdown("### 💰 Pago Parcial o Adelantado")
        
        with st.form("form_pago_parcial"):
            monto_pago = st.number_input(
                "Monto del Pago",
                min_value=0.0,
                value=info_prestamo['cuota_programada'],
                step=10.0
            )
            
            tipo_pago = st.selectbox(
                "Tipo de Pago",
                ["Pago Normal", "Pago Parcial", "Pago Adelantado"]
            )
            
            fecha_pago = st.date_input("Fecha de Pago", datetime.now())
            
            observaciones = st.text_area("Observaciones (opcional)")
            
            if st.form_submit_button("💾 Registrar Pago"):
                if monto_pago > 0:
                    if registrar_pago_manual(
                        id_prestamo, 
                        monto_pago, 
                        tipo_pago, 
                        fecha_pago, 
                        observaciones
                    ):
                        st.success("✅ Pago registrado exitosamente")
                        st.rerun()
                else:
                    st.error("❌ El monto del pago debe ser mayor a 0")

def historial_pagos():
    """Historial de pagos del grupo"""
    
    st.subheader("Historial de Pagos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver el historial")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Desde", datetime.now().replace(day=1), key="pagos_desde")
    
    with col2:
        fecha_fin = st.date_input("Hasta", datetime.now(), key="pagos_hasta")
    
    # Obtener historial de pagos
    pagos = obtener_historial_pagos_grupo(st.session_state.id_grupo, fecha_inicio, fecha_fin)
    
    if pagos:
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_pagos = len(pagos)
            st.metric("📥 Total de Pagos", total_pagos)
        
        with col2:
            monto_total = sum(p['total_pagado'] for p in pagos)
            st.metric("💰 Monto Total", f"${monto_total:,.2f}")
        
        with col3:
            pagos_hoy = sum(1 for p in pagos if p['fecha_pago'].date() == datetime.now().date())
            st.metric("📊 Pagos Hoy", pagos_hoy)
        
        # Tabla de pagos
        st.dataframe(pagos, use_container_width=True)
        
        # Exportar
        csv = pagos.to_csv(index=False)
        st.download_button(
            label="📤 Exportar a CSV",
            data=csv,
            file_name=f"historial_pagos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ No hay pagos registrados en el período seleccionado")

def estado_cuenta():
    """Estado de cuenta por socio"""
    
    st.subheader("Estado de Cuenta por Socio")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver estados de cuenta")
        return
    
    # Seleccionar socio
    socios = obtener_socios_con_prestamos(st.session_state.id_grupo)
    
    if not socios:
        st.info("ℹ️ No hay socios con préstamos en este grupo")
        return
    
    socio_seleccionado = st.selectbox(
        "Seleccionar Socio",
        options=[(s['id_socio'], f"{s['nombre']} {s['apellido']}") for s in socios],
        format_func=lambda x: x[1]
    )
    
    if socio_seleccionado:
        id_socio = socio_seleccionado[0]
        
        # Obtener estado de cuenta
        estado_cuenta = obtener_estado_cuenta_socio(id_socio)
        
        if estado_cuenta:
            # Resumen
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏦 Préstamos Activos", estado_cuenta['total_prestamos_activos'])
            
            with col2:
                st.metric("💰 Saldo Total", f"${estado_cuenta['saldo_total']:,.2f}")
            
            with col3:
                st.metric("📊 Cuota Mensual", f"${estado_cuenta['cuota_mensual_total']:,.2f}")
            
            with col4:
                st.metric("⚠️ En Mora", estado_cuenta['prestamos_mora'])
            
            # Detalle por préstamo
            st.markdown("### 📋 Detalle por Préstamo")
            
            for prestamo in estado_cuenta['detalle_prestamos']:
                with st.expander(f"Préstamo #{prestamo['id_prestamo']} - ${prestamo['monto_original']:,.2f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Fecha desembolso:** {prestamo['fecha_desembolso'].strftime('%d/%m/%Y')}")
                        st.write(f"**Fecha vencimiento:** {prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')}")
                        st.write(f"**Saldo actual:** ${prestamo['saldo_actual']:,.2f}")
                    
                    with col2:
                        st.write(f"**Cuota mensual:** ${prestamo['cuota_mensual']:,.2f}")
                        st.write(f"**Próximo pago:** {prestamo['proximo_pago'].strftime('%d/%m/%Y')}")
                        st.write(f"**Días en mora:** {prestamo['dias_mora']}")
                    
                    # Últimos pagos
                    st.markdown("#### Últimos Pagos")
                    if prestamo['ultimos_pagos']:
                        for pago in prestamo['ultimos_pagos']:
                            st.write(f"{pago['fecha_pago'].strftime('%d/%m/%Y')} - ${pago['total_pagado']:,.2f}")
                    else:
                        st.info("No hay pagos registrados")
        else:
            st.info("ℹ️ No se pudo generar el estado de cuenta")

# =============================================================================
# FUNCIONES AUXILIARES - PAGOS
# =============================================================================

def obtener_prestamos_activos_grupo(id_grupo):
    """Obtener préstamos activos del grupo"""
    from modules.prestamos import obtener_prestamos_activos_grupo
    return obtener_prestamos_activos_grupo(id_grupo)

def obtener_info_prestamo(id_prestamo):
    """Obtener información detallada de un préstamo"""
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            p.monto_solicitado,
            p.plazo_meses,
            (p.monto_solicitado - COALESCE((
                SELECT SUM(capital_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo
            ), 0)) as saldo_pendiente,
            COALESCE((
                SELECT MIN(fecha_programada) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NULL
            ), p.fecha_desembolso + INTERVAL 1 MONTH) as proximo_pago,
            COALESCE((
                SELECT (capital_pagado + interes_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo 
                ORDER BY fecha_programada ASC 
                LIMIT 1
            ), p.monto_solicitado / p.plazo_meses) as cuota_programada
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE p.id_prestamo = %s
    """
    resultado = ejecutar_consulta(query, (id_prestamo,))
    return resultado[0] if resultado else None

def obtener_cuotas_pendientes(id_prestamo):
    """Obtener cuotas pendientes de un préstamo"""
    query = """
        SELECT 
            id_pago,
            fecha_programada,
            capital_pagado as capital,
            interes_pagado as interes,
            (capital_pagado + interes_pagado) as total,
            ROW_NUMBER() OVER (ORDER BY fecha_programada) as numero_cuota
        FROM `detalle de pagos`
        WHERE id_prestamo = %s AND fecha_pago IS NULL
        ORDER BY fecha_programada ASC
    """
    return ejecutar_consulta(query, (id_prestamo,))

def procesar_pago_cuota(id_pago, info_prestamo):
    """Procesar pago de una cuota específica"""
    query = """
        UPDATE `detalle de pagos` 
        SET fecha_pago = %s, total_pagado = (capital_pagado + interes_pagado)
        WHERE id_pago = %s
    """
    
    if ejecutar_comando(query, (datetime.now(), id_pago)):
        st.success("✅ Cuota pagada exitosamente")
        
        # Registrar movimiento en caja
        registrar_movimiento_caja_pago(info_prestamo['id_prestamo'])
        
        # Verificar si el préstamo está completamente pagado
        verificar_prestamo_pagado(info_prestamo['id_prestamo'])
        
        st.rerun()

def registrar_pago_manual(id_prestamo, monto_pago, tipo_pago, fecha_pago, observaciones):
    """Registrar pago manual (parcial o adelantado)"""
    
    # Obtener información del préstamo para calcular distribución
    info_prestamo = obtener_info_prestamo(id_prestamo)
    
    if not info_prestamo:
        return False
    
    # Calcular distribución entre capital e interés
    # (Simplificado - en una implementación real se usaría el sistema de amortización)
    interes_mensual = info_prestamo['cuota_programada'] * 0.2  # 20% de la cuota como interés
    capital_pagado = monto_pago - interes_mensual
    
    if capital_pagado < 0:
        capital_pagado = monto_pago * 0.8  # Ajuste si el monto es menor
    
    query = """
        INSERT INTO `detalle de pagos` (
            id_socio, fecha_programada, capital_pagado, interes_pagado,
            id_prestamo, interes, fecha_pago, total_pagado, observaciones
        ) VALUES (
            (SELECT id_socio FROM prestamo WHERE id_prestamo = %s),
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    return ejecutar_comando(
        query,
        (
            id_prestamo,
            fecha_pago,
            capital_pagado,
            interes_mensual,
            id_prestamo,
            interes_mensual,
            fecha_pago,
            monto_pago,
            f"{tipo_pago} - {observaciones}"
        )
    )

def registrar_movimiento_caja_pago(id_prestamo):
    """Registrar movimiento en caja por pago de préstamo"""
    from modules.caja import obtener_o_crear_caja, registrar_movimiento_caja
    
    # Obtener información del pago
    pago_info = ejecutar_consulta("""
        SELECT SUM(total_pagado) as total 
        FROM `detalle de pagos` 
        WHERE id_prestamo = %s AND fecha_pago = CURDATE()
    """, (id_prestamo,))
    
    if pago_info and pago_info[0]['total']:
        total_pagado = pago_info[0]['total']
        
        # Obtener o crear caja para hoy
        id_caja = obtener_o_crear_caja(
            st.session_state.id_grupo,
            datetime.now().date()
        )
        
        if id_caja:
            registrar_movimiento_caja(
                id_caja,
                'INGRESO',
                None,  # No específico de socio (ya se registra en detalle pagos)
                total_pagado,
                f"Pago de préstamo #{id_prestamo}"
            )

def verificar_prestamo_pagado(id_prestamo):
    """Verificar si un préstamo está completamente pagado"""
    saldo_pendiente = ejecutar_consulta("""
        SELECT (monto_solicitado - COALESCE(SUM(capital_pagado), 0)) as saldo
        FROM prestamo p
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE p.id_prestamo = %s
    """, (id_prestamo,))[0]['saldo']
    
    if saldo_pendiente <= 0:
        # Marcar préstamo como pagado
        ejecutar_comando(
            "UPDATE prestamo SET id_estado_prestamo = 4 WHERE id_prestamo = %s",
            (id_prestamo,)
        )

def obtener_historial_pagos_grupo(id_grupo, fecha_inicio, fecha_fin):
    """Obtener historial de pagos del grupo"""
    import pandas as pd
    
    query = """
        SELECT 
            s.nombre,
            s.apellido,
            p.id_prestamo,
            dp.fecha_pago,
            dp.capital_pagado,
            dp.interes_pagado,
            dp.total_pagado,
            dp.observaciones
        FROM `detalle de pagos` dp
        JOIN prestamo p ON dp.id_prestamo = p.id_prestamo
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND dp.fecha_pago BETWEEN %s AND %s
        AND dp.fecha_pago IS NOT NULL
        ORDER BY dp.fecha_pago DESC
    """
    
    resultado = ejecutar_consulta(query, (id_grupo, fecha_inicio, fecha_fin))
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def obtener_socios_con_prestamos(id_grupo):
    """Obtener socios que tienen préstamos"""
    query = """
        SELECT DISTINCT 
            s.id_socio,
            s.nombre,
            s.apellido
        FROM socios s
        JOIN prestamo p ON s.id_socio = p.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo IN (2, 5)  -- Activos o en mora
        ORDER BY s.apellido, s.nombre
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_estado_cuenta_socio(id_socio):
    """Obtener estado de cuenta completo de un socio"""
    
    # Obtener préstamos del socio
    prestamos = ejecutar_consulta("""
        SELECT 
            id_prestamo,
            monto_solicitado as monto_original,
            fecha_desembolso,
            fecha_vencimiento,
            plazo_meses,
            (monto_solicitado - COALESCE(SUM(capital_pagado), 0)) as saldo_actual,
            COALESCE((
                SELECT (capital_pagado + interes_pagado) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo 
                ORDER BY fecha_programada ASC 
                LIMIT 1
            ), monto_solicitado / plazo_meses) as cuota_mensual,
            COALESCE((
                SELECT MIN(fecha_programada) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NULL
            ), fecha_desembolso + INTERVAL 1 MONTH) as proximo_pago,
            GREATEST(0, DATEDIFF(CURDATE(), COALESCE((
                SELECT MIN(fecha_programada) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NULL
            ), fecha_desembolso + INTERVAL 1 MONTH))) as dias_mora
        FROM prestamo p
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE p.id_socio = %s AND p.id_estado_prestamo IN (2, 5)
        GROUP BY p.id_prestamo
    """, (id_socio,))
    
    if not prestamos:
        return None
    
    # Obtener últimos pagos para cada préstamo
    for prestamo in prestamos:
        ultimos_pagos = ejecutar_consulta("""
            SELECT fecha_pago, total_pagado
            FROM `detalle de pagos`
            WHERE id_prestamo = %s AND fecha_pago IS NOT NULL
            ORDER BY fecha_pago DESC
            LIMIT 5
        """, (prestamo['id_prestamo'],))
        
        prestamo['ultimos_pagos'] = ultimos_pagos
    
    # Calcular totales
    saldo_total = sum(p['saldo_actual'] for p in prestamos)
    cuota_mensual_total = sum(p['cuota_mensual'] for p in prestamos)
    prestamos_mora = sum(1 for p in prestamos if p['dias_mora'] > 0)
    
    return {
        'total_prestamos_activos': len(prestamos),
        'saldo_total': saldo_total,
        'cuota_mensual_total': cuota_mensual_total,
        'prestamos_mora': prestamos_mora,
        'detalle_prestamos': prestamos
    }