import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
                        # En una implementación real, redirigiría al módulo de pagos
                        st.info("🔗 Esta función redirigiría al módulo de pagos")
                
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
    """Reportes y estadísticas de mora - FUNCIÓN COMPLETAMENTE IMPLEMENTADA"""
    
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
        
        # Gráficos de evolución
        st.markdown("### 📈 Evolución de la Mora")
        
        # Gráfico de distribución de días en mora
        if stats['distribucion_dias_mora']:
            df_dias = pd.DataFrame(stats['distribucion_dias_mora'])
            fig_dias = px.bar(df_dias, x='rango', y='cantidad', 
                             title='Distribución de Días en Mora',
                             labels={'rango': 'Rango de Días', 'cantidad': 'Cantidad de Préstamos'})
            st.plotly_chart(fig_dias, use_container_width=True)
        
        # Gráfico de torta de estado de préstamos
        if stats['estado_prestamos']:
            df_estado = pd.DataFrame(stats['estado_prestamos'])
            fig_torta = px.pie(df_estado, values='cantidad', names='estado',
                              title='Distribución de Préstamos por Estado')
            st.plotly_chart(fig_torta, use_container_width=True)
        
        # Lista de socios con mayor mora
        st.markdown("### 👥 Socios con Mayor Mora")
        if stats['socios_mayor_mora']:
            for i, socio in enumerate(stats['socios_mayor_mora'], 1):
                st.write(f"{i}. **{socio['nombre']} {socio['apellido']}** - {socio['dias_mora']} días - ${socio['monto_mora']:,.2f}")
        else:
            st.info("ℹ️ No hay socios con mora significativa")
        
        # Exportar reporte
        st.markdown("---")
        if st.button("📤 Exportar Reporte Completo"):
            exportar_reporte_mora(stats, st.session_state.id_grupo)
    else:
        st.info("ℹ️ No hay datos de mora para mostrar")

# =============================================================================
# FUNCIONES AUXILIARES - MORAS (TODAS IMPLEMENTADAS)
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
        LEFT JOIN `detalles_pagos` dp ON p.id_prestamo = dp.id_prestamo
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
        "SELECT cantidad_multa FROM reglas_grupo WHERE id_grupo = %s",
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
                FROM `detalles_pagos` 
                WHERE id_prestamo = p.id_prestamo AND fecha_pago IS NOT NULL
            ) as ultimo_pago
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalles_pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s
        AND p.id_estado_prestamo = 5  -- En mora
        GROUP BY p.id_prestamo
        HAVING saldo_actual > 0
        ORDER BY dias_mora DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def registrar_contacto_mora(id_prestamo):
    """Registrar contacto con socio en mora - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener información del préstamo y socio
    prestamo_info = ejecutar_consulta("""
        SELECT p.id_prestamo, s.nombre, s.apellido, s.telefono
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE p.id_prestamo = %s
    """, (id_prestamo,))
    
    if not prestamo_info:
        st.error("❌ No se encontró información del préstamo")
        return
    
    prestamo = prestamo_info[0]
    
    st.subheader(f"📞 Contactar Socio: {prestamo['nombre']} {prestamo['apellido']}")
    st.write(f"**Teléfono:** {prestamo['telefono']}")
    st.write(f"**Préstamo #:** {id_prestamo}")
    
    with st.form(f"form_contacto_{id_prestamo}"):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_contacto = st.date_input("📅 Fecha de Contacto", datetime.now())
            metodo_contacto = st.selectbox(
                "📱 Método de Contacto",
                ["Llamada telefónica", "Mensaje de texto", "Visita personal", "Correo electrónico", "Otro"]
            )
        
        with col2:
            resultado_contacto = st.selectbox(
                "🎯 Resultado del Contacto",
                ["Contactado exitosamente", "No contesta", "Número no existe", "Prometió pago", "Rechazó contacto", "Otro"]
            )
            proximo_seguimiento = st.date_input("📅 Próximo Seguimiento", datetime.now() + timedelta(days=3))
        
        detalles_contacto = st.text_area(
            "📝 Detalles del Contacto",
            placeholder="Describa la conversación, compromisos adquiridos, observaciones..."
        )
        
        if st.form_submit_button("💾 Guardar Registro de Contacto"):
            if guardar_registro_contacto(id_prestamo, fecha_contacto, metodo_contacto, resultado_contacto, detalles_contacto, proximo_seguimiento):
                st.success("✅ Registro de contacto guardado exitosamente")
                
                # Generar alerta para próximo seguimiento si es necesario
                if resultado_contacto in ["No contesta", "Prometió pago"]:
                    generar_alerta_seguimiento(id_prestamo, proximo_seguimiento, resultado_contacto)

def guardar_registro_contacto(id_prestamo, fecha_contacto, metodo_contacto, resultado_contacto, detalles_contacto, proximo_seguimiento):
    """Guardar registro de contacto en base de datos"""
    
    # Primero, necesitamos el ID del socio
    socio_info = ejecutar_consulta(
        "SELECT id_socio FROM prestamo WHERE id_prestamo = %s",
        (id_prestamo,)
    )
    
    if not socio_info:
        return False
    
    id_socio = socio_info[0]['id_socio']
    
    query = """
        INSERT INTO seguimiento_moras (
            id_socio, id_prestamo, fecha_contacto, metodo_contacto, 
            resultado_contacto, detalles_contacto, proximo_seguimiento
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    return ejecutar_comando(
        query,
        (id_socio, id_prestamo, fecha_contacto, metodo_contacto, resultado_contacto, detalles_contacto, proximo_seguimiento)
    )

def generar_alerta_seguimiento(id_prestamo, fecha_seguimiento, motivo):
    """Generar alerta para próximo seguimiento"""
    query = """
        INSERT INTO alertas (
            id_grupo, titulo, descripcion, nivel, fecha_alerta, fecha_recordatorio, resuelta
        ) VALUES (
            (SELECT id_grupo FROM socios WHERE id_socio = (SELECT id_socio FROM prestamo WHERE id_prestamo = %s)),
            %s, %s, 'MEDIO', %s, %s, 0
        )
    """
    
    titulo = f"Seguimiento de Mora - Préstamo #{id_prestamo}"
    descripcion = f"Recordatorio para seguimiento: {motivo}"
    
    return ejecutar_comando(
        query,
        (id_prestamo, titulo, descripcion, datetime.now(), fecha_seguimiento)
    )

def crear_plan_pago_mora(id_prestamo):
    """Crear plan de pago para préstamo en mora - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener información del préstamo
    prestamo_info = ejecutar_consulta("""
        SELECT 
            p.id_prestamo, p.monto_solicitado, p.fecha_vencimiento,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_pendiente,
            s.nombre, s.apellido
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalles_pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE p.id_prestamo = %s
        GROUP BY p.id_prestamo
    """, (id_prestamo,))
    
    if not prestamo_info:
        st.error("❌ No se encontró información del préstamo")
        return
    
    prestamo = prestamo_info[0]
    
    st.subheader(f"🔄 Plan de Pago - {prestamo['nombre']} {prestamo['apellido']}")
    st.write(f"**Saldo Pendiente:** ${prestamo['saldo_pendiente']:,.2f}")
    st.write(f"**Fecha Vencimiento Original:** {prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')}")
    
    with st.form(f"form_plan_pago_{id_prestamo}"):
        st.markdown("### Configurar Nuevo Plan de Pago")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_plazo_meses = st.slider(
                "⏱️ Nuevo Plazo (meses)",
                min_value=1,
                max_value=24,
                value=6,
                help="Número de meses para el nuevo plan de pago"
            )
            
            fecha_inicio_plan = st.date_input(
                "📅 Fecha de Inicio del Plan",
                datetime.now()
            )
        
        with col2:
            # Calcular nueva cuota mensual
            saldo_pendiente = float(prestamo['saldo_pendiente'])
            nueva_cuota_mensual = saldo_pendiente / nuevo_plazo_meses
            
            st.metric("💵 Nueva Cuota Mensual", f"${nueva_cuota_mensual:,.2f}")
            
            incluir_multas = st.checkbox(
                "💰 Incluir multas pendientes en el plan",
                value=True,
                help="Incluye las multas acumuladas en el nuevo plan de pago"
            )
        
        # Mostrar resumen del plan
        st.markdown("### 📋 Resumen del Nuevo Plan")
        
        fecha_actual = fecha_inicio_plan
        st.write("**Calendario de Pagos:**")
        
        for i in range(1, nuevo_plazo_meses + 1):
            fecha_pago = fecha_actual.replace(month=fecha_actual.month + i)
            st.write(f"Cuota {i}: ${nueva_cuota_mensual:,.2f} - Vence: {fecha_pago.strftime('%d/%m/%Y')}")
        
        condiciones_plan = st.text_area(
            "📝 Condiciones Especiales del Plan",
            placeholder="Especifique cualquier condición especial, acuerdo, o observación sobre este plan de pago..."
        )
        
        if st.form_submit_button("💾 Crear Plan de Pago"):
            if crear_plan_pago_bd(id_prestamo, nuevo_plazo_meses, nueva_cuota_mensual, fecha_inicio_plan, condiciones_plan, incluir_multas):
                st.success("✅ Plan de pago creado exitosamente")
                
                # Actualizar estado del préstamo
                ejecutar_comando(
                    "UPDATE prestamo SET id_estado_prestamo = 6 WHERE id_prestamo = %s",
                    (id_prestamo,)
                )  # 6 = En plan de pago especial
                
                st.info("📝 El préstamo ha sido marcado como 'En plan de pago especial'")

def crear_plan_pago_bd(id_prestamo, plazo_meses, cuota_mensual, fecha_inicio, condiciones, incluir_multas):
    """Guardar plan de pago en base de datos"""
    
    query = """
        INSERT INTO planes_pago_mora (
            id_prestamo, plazo_meses, cuota_mensual, fecha_inicio_plan,
            condiciones, incluye_multas, fecha_creacion
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    return ejecutar_comando(
        query,
        (id_prestamo, plazo_meses, cuota_mensual, fecha_inicio, condiciones, incluir_multas, datetime.now())
    )

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
    """Obtener estadísticas de mora del grupo - FUNCIÓN MEJORADA"""
    
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
        LEFT JOIN `detalles_pagos` dp ON p.id_prestamo = dp.id_prestamo
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
        LEFT JOIN `detalles_pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
        GROUP BY p.id_prestamo, s.id_socio
        ORDER BY dias_mora DESC
        LIMIT 5
    """, (id_grupo,))
    
    # Distribución de días en mora
    distribucion_dias_mora = ejecutar_consulta("""
        SELECT 
            CASE 
                WHEN dias_mora <= 15 THEN '1-15 días'
                WHEN dias_mora <= 30 THEN '16-30 días'
                WHEN dias_mora <= 60 THEN '31-60 días'
                ELSE 'Más de 60 días'
            END as rango,
            COUNT(*) as cantidad
        FROM (
            SELECT DATEDIFF(CURDATE(), p.fecha_vencimiento) as dias_mora
            FROM prestamo p
            JOIN socios s ON p.id_socio = s.id_socio
            WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
        ) as moras
        GROUP BY rango
        ORDER BY 
            CASE rango
                WHEN '1-15 días' THEN 1
                WHEN '16-30 días' THEN 2
                WHEN '31-60 días' THEN 3
                ELSE 4
            END
    """, (id_grupo,))
    
    # Estado de préstamos
    estado_prestamos = ejecutar_consulta("""
        SELECT 
            CASE 
                WHEN p.id_estado_prestamo = 2 THEN 'Al día'
                WHEN p.id_estado_prestamo = 5 THEN 'En mora'
                WHEN p.id_estado_prestamo = 6 THEN 'Plan de pago'
                ELSE 'Otro'
            END as estado,
            COUNT(*) as cantidad
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo IN (2, 5, 6)
        GROUP BY estado
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
        'socios_mayor_mora': socios_mayor_mora,
        'distribucion_dias_mora': distribucion_dias_mora,
        'estado_prestamos': estado_prestamos
    }

def exportar_reporte_mora(stats, id_grupo):
    """Exportar reporte completo de moras - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener información del grupo
    grupo_info = ejecutar_consulta(
        "SELECT nombre_grupo FROM grupos WHERE id_grupo = %s",
        (id_grupo,)
    )
    
    nombre_grupo = grupo_info[0]['nombre_grupo'] if grupo_info else "Grupo Desconocido"
    
    # Crear contenido del reporte
    contenido = f"""
    REPORTE DE MORAS - {nombre_grupo.upper()}
    ===========================================
    
    Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    RESUMEN EJECUTIVO:
    ------------------
    Tasa de Mora: {stats['tasa_mora']:.1f}%
    Monto Total en Mora: ${stats['monto_total_mora']:,.2f}
    Socios en Mora: {stats['socios_en_mora']}
    Tendencia: {stats['tendencia_mora']}
    
    DISTRIBUCIÓN DE DÍAS EN MORA:
    -----------------------------
    """
    
    for distribucion in stats['distribucion_dias_mora']:
        contenido += f"    {distribucion['rango']}: {distribucion['cantidad']} préstamos\n"
    
    contenido += f"""
    ESTADO DE PRÉSTAMOS:
    --------------------
    """
    
    for estado in stats['estado_prestamos']:
        contenido += f"    {estado['estado']}: {estado['cantidad']} préstamos\n"
    
    contenido += f"""
    SOCIOS CON MAYOR MORA:
    ----------------------
    """
    
    for i, socio in enumerate(stats['socios_mayor_mora'], 1):
        contenido += f"    {i}. {socio['nombre']} {socio['apellido']}: {socio['dias_mora']} días - ${socio['monto_mora']:,.2f}\n"
    
    contenido += f"""
    RECOMENDACIONES:
    ----------------
    """
    
    if stats['tasa_mora'] > 10:
        contenido += "    • Implementar estrategia agresiva de cobranza\n"
        contenido += "    • Revisar políticas de otorgamiento de préstamos\n"
        contenido += "    • Considerar aumentar las multas por mora\n"
    elif stats['tasa_mora'] > 5:
        contenido += "    • Mantener seguimiento regular a préstamos en mora\n"
        contenido += "    • Ofrecer planes de pago a socios con dificultades\n"
    else:
        contenido += "    • Mantener las buenas prácticas actuales\n"
        contenido += "    • Continuar con el monitoreo preventivo\n"
    
    # Ofrecer descarga
    st.download_button(
        label="📥 Descargar Reporte Completo",
        data=contenido,
        file_name=f"reporte_moras_{nombre_grupo}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )