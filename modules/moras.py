import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta

def modulo_moras():
    """Módulo principal para control de moras y alertas"""
    
    st.header("⚠️ Control de Moras y Alertas")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Detección de Moras", "📋 Préstamos en Mora", "🚨 Alertas Activas", "📊 Reportes de Mora"])
    
    with tab1:
        deteccion_moras()
    
    with tab2:
        prestamos_en_mora()
    
    with tab3:
        alertas_activas()
    
    with tab4:
        reportes_mora()

def deteccion_moras():
    """Detección automática de moras"""
    
    st.subheader("Detección Automática de Moras")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ejecutar detección de moras")
        return
    
    st.info("""
    El sistema revisa automáticamente los préstamos con pagos vencidos y los marca como en mora.
    También genera multas automáticas según las reglas del grupo.
    """)
    
    # Ejecutar detección
    if st.button("🔄 Ejecutar Detección de Moras"):
        with st.spinner("Buscando préstamos en mora..."):
            resultado = ejecutar_deteccion_moras(st.session_state.id_grupo)
            
            if resultado:
                st.success(f"✅ Detección completada: {resultado['prestamos_mora']} préstamos en mora, {resultado['multas_generadas']} multas aplicadas")
                
                # Mostrar detalles
                if resultado['prestamos_afectados']:
                    st.markdown("### Préstamos Marcados en Mora")
                    for prestamo in resultado['prestamos_afectados']:
                        st.write(f"• {prestamo['socio']} - {prestamo['dias_mora']} días de mora")
                
                if resultado['multas_aplicadas']:
                    st.markdown("### Multas Aplicadas")
                    for multa in resultado['multas_aplicadas']:
                        st.write(f"• {multa['socio']} - ${multa['monto_multa']:,.2f}")
            else:
                st.info("ℹ️ No se encontraron préstamos en mora")

def prestamos_en_mora():
    """Gestión de préstamos en mora"""
    
    st.subheader("Préstamos en Mora")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver préstamos en mora")
        return
    
    # Obtener préstamos en mora
    prestamos_mora = obtener_prestamos_en_mora(st.session_state.id_grupo)
    
    if prestamos_mora:
        st.markdown(f"### 📋 Préstamos en Mora ({len(prestamos_mora)})")
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_mora = sum(p['saldo_mora'] for p in prestamos_mora)
            st.metric("💰 Total en Mora", f"${total_mora:,.2f}")
        
        with col2:
            promedio_dias = sum(p['dias_mora'] for p in prestamos_mora) / len(prestamos_mora)
            st.metric("📅 Promedio Días Mora", f"{promedio_dias:.1f}")
        
        with col3:
            max_dias = max(p['dias_mora'] for p in prestamos_mora)
            st.metric("⏰ Máximo Días Mora", max_dias)
        
        # Lista de préstamos
        for prestamo in prestamos_mora:
            with st.expander(f"⚠️ {prestamo['nombre']} {prestamo['apellido']} - {prestamo['dias_mora']} días en mora"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Préstamo #:** {prestamo['id_prestamo']}")
                    st.write(f"**Monto original:** ${prestamo['monto_original']:,.2f}")
                    st.write(f"**Saldo actual:** ${prestamo['saldo_actual']:,.2f}")
                    st.write(f"**Saldo en mora:** ${prestamo['saldo_mora']:,.2f}")
                
                with col2:
                    st.write(f"**Fecha vencimiento:** {prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')}")
                    st.write(f"**Días en mora:** {prestamo['dias_mora']}")
                    st.write(f"**Multas acumuladas:** ${prestamo['multas_acumuladas']:,.2f}")
                    st.write(f"**Último pago:** {prestamo['ultimo_pago'] or 'Sin pagos'}")
                
                # Acciones
                col_act1, col_act2, col_act3 = st.columns(3)
                
                with col_act1:
                    if st.button("💳 Registrar Pago", key=f"pago_mora_{prestamo['id_prestamo']}"):
                        st.session_state.prestamo_seleccionado = prestamo['id_prestamo']
                        st.switch_page("pages/pagos.py")
                
                with col_act2:
                    if st.button("📞 Contactar Socio", key=f"contactar_{prestamo['id_prestamo']}"):
                        registrar_contacto_mora(prestamo['id_prestamo'])
                
                with col_act3:
                    if st.button("🔄 Plan de Pago", key=f"plan_{prestamo['id_prestamo']}"):
                        crear_plan_pago_mora(prestamo['id_prestamo'])
    else:
        st.success("🎉 No hay préstamos en mora en este grupo")

def alertas_activas():
    """Sistema de alertas activas"""
    
    st.subheader("Alertas Activas")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver alertas")
        return
    
    # Obtener alertas activas
    alertas = obtener_alertas_activas(st.session_state.id_grupo)
    
    if alertas:
        st.markdown(f"### 🚨 Alertas Activas ({len(alertas)})")
        
        for alerta in alertas:
            if alerta['nivel'] == 'ALTO':
                st.error(f"🔴 **{alerta['titulo']}** - {alerta['descripcion']}")
            elif alerta['nivel'] == 'MEDIO':
                st.warning(f"🟡 **{alerta['titulo']}** - {alerta['descripcion']}")
            else:
                st.info(f"🔵 **{alerta['titulo']}** - {alerta['descripcion']}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Fecha:** {alerta['fecha_alerta'].strftime('%d/%m/%Y %H:%M')}")
            with col2:
                if st.button("✅ Resolver", key=f"resolver_{alerta['id_alerta']}"):
                    resolver_alerta(alerta['id_alerta'])
        
        # Botón para limpiar alertas resueltas
        if st.button("🗑️ Limpiar Alertas Resueltas"):
            limpiar_alertas_resueltas()
            st.rerun()
    else:
        st.success("✅ No hay alertas activas")

def reportes_mora():
    """Reportes y estadísticas de mora"""
    
    st.subheader("Reportes de Mora")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver reportes de mora")
        return
    
    # Obtener estadísticas de mora
    stats = obtener_estadisticas_mora(st.session_state.id_grupo)
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Tasa de Mora", f"{stats['tasa_mora']:.1f}%")
        
        with col2:
            st.metric("💰 Monto en Mora", f"${stats['monto_total_mora']:,.2f}")
        
        with col3:
            st.metric("👥 Socios en Mora", stats['socios_en_mora'])
        
        with col4:
            st.metric("📈 Tendencia", stats['tendencia_mora'])
        
        # Gráficos (simplificado)
        st.markdown("### Evolución de la Mora")
        st.info("🔧 Funcionalidad de gráficos en desarrollo")
        
        # Lista de socios con mayor mora
        st.markdown("### Socios con Mayor Mora")
        for socio in stats['socios_mayor_mora']:
            st.write(f"• {socio['nombre']} {socio['apellido']} - {socio['dias_mora']} días - ${socio['monto_mora']:,.2f}")
    else:
        st.info("ℹ️ No hay datos de mora para mostrar")

# =============================================================================
# FUNCIONES AUXILIARES - MORAS
# =============================================================================

def ejecutar_deteccion_moras(id_grupo):
    """Ejecutar detección automática de moras"""
    
    # Obtener préstamos con pagos vencidos
    prestamos_vencidos = obtener_prestamos_vencidos(id_grupo)
    
    if not prestamos_vencidos:
        return None
    
    prestamos_afectados = []
    multas_aplicadas = []
    
    for prestamo in prestamos_vencidos:
        # Marcar préstamo como en mora
        if marcar_prestamo_mora(prestamo['id_prestamo']):
            prestamos_afectados.append({
                'socio': f"{prestamo['nombre']} {prestamo['apellido']}",
                'dias_mora': prestamo['dias_vencido']
            })
        
        # Aplicar multa por mora
        monto_multa = calcular_multa_mora(prestamo['id_prestamo'], id_grupo)
        if monto_multa > 0:
            if aplicar_multa_mora(prestamo['id_prestamo'], monto_multa):
                multas_aplicadas.append({
                    'socio': f"{prestamo['nombre']} {prestamo['apellido']}",
                    'monto_multa': monto_multa
                })
        
        # Generar alerta
        generar_alerta_mora(prestamo['id_prestamo'], prestamo['dias_vencido'])
    
    return {
        'prestamos_mora': len(prestamos_afectados),
        'multas_generadas': len(multas_aplicadas),
        'prestamos_afectados': prestamos_afectados,
        'multas_aplicadas': multas_aplicadas
    }

def obtener_prestamos_vencidos(id_grupo):
    """Obtener préstamos con pagos vencidos"""
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            p.fecha_vencimiento,
            DATEDIFF(CURDATE(), p.fecha_vencimiento) as dias_vencido,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_pendiente
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s
        AND p.id_estado_prestamo = 2  -- Aprobado (no en mora aún)
        AND p.fecha_vencimiento < CURDATE()
        AND (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) > 0
        GROUP BY p.id_prestamo
        HAVING dias_vencido > 0
    """
    return ejecutar_consulta(query, (id_grupo,))

def marcar_prestamo_mora(id_prestamo):
    """Marcar préstamo como en mora"""
    query = "UPDATE prestamo SET id_estado_prestamo = 5 WHERE id_prestamo = %s"
    return ejecutar_comando(query, (id_prestamo,))

def calcular_multa_mora(id_prestamo, id_grupo):
    """Calcular monto de multa por mora"""
    # Obtener reglas del grupo
    reglas = ejecutar_consulta(
        "SELECT cantidad_multa FROM reglas_del_grupo WHERE id_grupo = %s",
        (id_grupo,)
    )
    
    if reglas:
        return reglas[0]['cantidad_multa']
    
    return 0  # Sin multa por defecto

def aplicar_multa_mora(id_prestamo, monto_multa):
    """Aplicar multa por mora a un préstamo"""
    # Obtener información del préstamo
    prestamo_info = ejecutar_consulta(
        "SELECT id_socio FROM prestamo WHERE id_prestamo = %s",
        (id_prestamo,)
    )
    
    if not prestamo_info:
        return False
    
    id_socio = prestamo_info[0]['id_socio']
    
    # Obtener última sesión
    ultima_sesion = ejecutar_consulta("""
        SELECT id_sesion 
        FROM sesion 
        WHERE id_grupo = (SELECT id_grupo FROM socios WHERE id_socio = %s)
        ORDER BY fecha_sesion DESC 
        LIMIT 1
    """, (id_socio,))
    
    if not ultima_sesion:
        return False
    
    id_sesion = ultima_sesion[0]['id_sesion']
    
    # Crear registro de multa
    query = """
        INSERT INTO multa (
            id_sesion, id_socio, monto_a_pagar, monto_pagado,
            fecha_pago_real, fecha_vencimiento, motivo
        ) VALUES (%s, %s, %s, 0, NULL, %s, 'Mora por préstamo vencido')
    """
    
    fecha_vencimiento = datetime.now() + timedelta(days=15)  # 15 días para pagar multa
    
    return ejecutar_comando(
        query,
        (id_sesion, id_socio, monto_multa, fecha_vencimiento)
    )

def generar_alerta_mora(id_prestamo, dias_vencido):
    """Generar alerta por préstamo en mora"""
    query = """
        INSERT INTO alertas (
            id_grupo, titulo, descripcion, nivel, fecha_alerta, resuelta
        ) VALUES (
            (SELECT id_grupo FROM socios WHERE id_socio = (SELECT id_socio FROM prestamo WHERE id_prestamo = %s)),
            %s, %s, %s, %s, 0
        )
    """
    
    titulo = f"Préstamo en Mora - {dias_vencido} días"
    descripcion = f"Préstamo #{id_prestamo} lleva {dias_vencido} días en mora"
    nivel = "ALTO" if dias_vencido > 30 else "MEDIO"
    
    return ejecutar_comando(
        query,
        (id_prestamo, titulo, descripcion, nivel, datetime.now())
    )

def obtener_prestamos_en_mora(id_grupo):
    """Obtener préstamos actualmente en mora"""
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            p.monto_solicitado as monto_original,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_actual,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_mora,
            p.fecha_vencimiento,
            DATEDIFF(CURDATE(), p.fecha_vencimiento) as dias_mora,
            COALESCE((
                SELECT SUM(monto_a_pagar) 
                FROM multa 
                WHERE id_socio = s.id_socio AND monto_pagado = 0
            ), 0) as multas_acumuladas,
            (
                SELECT MAX(fecha_pago) 
                FROM `detalle de pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NOT NULL
            ) as ultimo_pago
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s
        AND p.id_estado_prestamo = 5  -- En mora
        GROUP BY p.id_prestamo
        HAVING saldo_actual > 0
        ORDER BY dias_mora DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def registrar_contacto_mora(id_prestamo):
    """Registrar contacto con socio en mora"""
    st.info(f"🔧 Funcionalidad en desarrollo - Contactar socio préstamo #{id_prestamo}")

def crear_plan_pago_mora(id_prestamo):
    """Crear plan de pago para préstamo en mora"""
    st.info(f"🔧 Funcionalidad en desarrollo - Plan de pago préstamo #{id_prestamo}")

def obtener_alertas_activas(id_grupo):
    """Obtener alertas activas del grupo"""
    query = """
        SELECT id_alerta, titulo, descripcion, nivel, fecha_alerta
        FROM alertas
        WHERE id_grupo = %s AND resuelta = 0
        ORDER BY 
            CASE nivel 
                WHEN 'ALTO' THEN 1
                WHEN 'MEDIO' THEN 2
                WHEN 'BAJO' THEN 3
            END,
            fecha_alerta DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def resolver_alerta(id_alerta):
    """Marcar alerta como resuelta"""
    query = "UPDATE alertas SET resuelta = 1, fecha_resolucion = %s WHERE id_alerta = %s"
    return ejecutar_comando(query, (datetime.now(), id_alerta))

def limpiar_alertas_resueltas():
    """Eliminar alertas resueltas antiguas"""
    query = "DELETE FROM alertas WHERE resuelta = 1 AND fecha_alerta < %s"
    fecha_limite = datetime.now() - timedelta(days=30)  # 30 días
    return ejecutar_comando(query, (fecha_limite,))

def obtener_estadisticas_mora(id_grupo):
    """Obtener estadísticas de mora del grupo"""
    
    # Obtener datos básicos
    total_prestamos = ejecutar_consulta("""
        SELECT COUNT(*) as total
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo IN (2, 5)
    """, (id_grupo,))[0]['total']
    
    prestamos_mora = ejecutar_consulta("""
        SELECT COUNT(*) as total
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
    """, (id_grupo,))[0]['total']
    
    # Calcular tasa de mora
    tasa_mora = (prestamos_mora / total_prestamos * 100) if total_prestamos > 0 else 0
    
    # Monto total en mora
    monto_mora = ejecutar_consulta("""
        SELECT COALESCE(SUM(p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)), 0) as total
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
        GROUP BY p.id_prestamo
    """, (id_grupo,))
    
    monto_total_mora = sum(item['total'] for item in monto_mora) if monto_mora else 0
    
    # Socios en mora
    socios_en_mora = ejecutar_consulta("""
        SELECT COUNT(DISTINCT p.id_socio) as total
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
    """, (id_grupo,))[0]['total']
    
    # Socios con mayor mora
    socios_mayor_mora = ejecutar_consulta("""
        SELECT 
            s.nombre,
            s.apellido,
            MAX(DATEDIFF(CURDATE(), p.fecha_vencimiento)) as dias_mora,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as monto_mora
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
        GROUP BY p.id_prestamo, s.id_socio
        ORDER BY dias_mora DESC
        LIMIT 5
    """, (id_grupo,))
    
    # Tendencia (simplificada)
    tendencia = "ESTABLE"
    if tasa_mora > 10:
        tendencia = "ALTA"
    elif tasa_mora < 5:
        tendencia = "BAJA"
    
    return {
        'tasa_mora': tasa_mora,
        'monto_total_mora': monto_total_mora,
        'socios_en_mora': socios_en_mora,
        'tendencia_mora': tendencia,
        'socios_mayor_mora': socios_mayor_mora
    }