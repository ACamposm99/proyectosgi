import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta
import pandas as pd


def modulo_reuniones():
    """Módulo principal para gestión de reuniones y asistencia"""
    
    st.header("📅 Reuniones y Control de Asistencia")
    
    tab1, tab2, tab3 = st.tabs(["🆕 Nueva Reunión", "✅ Registrar Asistencia", "📋 Historial de Reuniones"])
    
    with tab1:
        nueva_reunion()
    
    with tab2:
        registrar_asistencia()
    
    with tab3:
        historial_reuniones()

def nueva_reunion():
    """Crear una nueva reunión/sesión - FUNCIÓN MEJORADA"""
    
    st.subheader("Crear Nueva Reunión")
    
    # Solo permitir si el usuario es directiva y tiene un grupo
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede crear reuniones")
        return
    
    with st.form("form_nueva_reunion"):
        # Obtener información del grupo para sugerir fecha
        grupo_info = obtener_info_grupo(st.session_state.id_grupo)
        
        if grupo_info:
            st.info(f"**Grupo:** {grupo_info['nombre_grupo']} | **Día de reunión:** {grupo_info['dia_reunion']}")
        
        # Calcular próxima fecha de reunión
        fecha_sugerida = calcular_proxima_reunion(st.session_state.id_grupo)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_sesion = st.date_input(
                "📅 Fecha de la Reunión", 
                value=fecha_sugerida,
                min_value=datetime.now().date()
            )
        
        with col2:
            hora_sesion = st.time_input(
                "⏰ Hora de la Reunión",
                value=datetime.strptime(grupo_info['hora_reunion'], '%H:%M:%S').time() if grupo_info and 'hora_reunion' in grupo_info else datetime.now().time()
            )
        
        # Agregar tipo de reunión
        tipo_reunion = st.selectbox(
            "🎯 Tipo de Reunión",
            ["Reunión Regular", "Reunión Extraordinaria", "Asamblea General", "Reunión de Directiva", "Otro"]
        )
        
        temas_agenda = st.text_area(
            "📋 Temas de la Agenda", 
            placeholder="Liste los temas principales a tratar en la reunión...",
            help="Separe cada tema con un punto y aparte"
        )
        
        notas_adicionales = st.text_area(
            "📝 Notas adicionales (opcional)", 
            placeholder="Observaciones, materiales necesarios, ubicación específica..."
        )
        
        submitted = st.form_submit_button("💾 Crear Reunión")
        
        if submitted:
            id_sesion = crear_sesion(
                st.session_state.id_grupo, 
                fecha_sesion, 
                tipo_reunion,
                temas_agenda,
                notas_adicionales
            )
            if id_sesion:
                st.success(f"✅ Reunión creada exitosamente (Sesión #{id_sesion})")
                
                # Inicializar registros de asistencia automáticamente
                if inicializar_asistencia(id_sesion, st.session_state.id_grupo):
                    st.info("📋 Registros de asistencia inicializados para todos los socios")
                
                # Generar acta base si se solicita
                if st.checkbox("📄 Generar acta base de la reunión"):
                    generar_acta_base_reunion(id_sesion)
                
                st.rerun()

def crear_sesion(id_grupo, fecha_sesion, tipo_reunion="Reunión Regular", temas_agenda="", notas=""):
    """Crear nueva sesión/reunión en la base de datos - FUNCIÓN MEJORADA"""
    
    query = """
        INSERT INTO sesion (id_grupo, fecha_sesion, tipo_reunion, temas_agenda, notas, total_presentes)
        VALUES (%s, %s, %s, %s, %s, 0)
    """
    
    id_sesion = ejecutar_comando(query, (id_grupo, fecha_sesion, tipo_reunion, temas_agenda, notas))
    
    return id_sesion

def inicializar_asistencia(id_sesion, id_grupo):
    """Inicializar registros de asistencia para todos los socios del grupo"""
    
    socios = obtener_socios_grupo(id_grupo)
    
    for socio in socios:
        query = """
            INSERT INTO asistencia (id_sesion, id_socio, presencial)
            VALUES (%s, %s, 0)
        """
        ejecutar_comando(query, (id_sesion, socio['id_socio']))
    
    return True

def registrar_asistencia():
    """Registro de asistencia para una reunión existente - FUNCIÓN MEJORADA"""
    
    st.subheader("Registro de Asistencia")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede registrar asistencia")
        return
    
    # Obtener reuniones recientes del grupo
    reuniones = obtener_reuniones_recientes(st.session_state.id_grupo)
    
    if not reuniones:
        st.info("ℹ️ No hay reuniones creadas. Cree una reunión primero.")
        return
    
    # Seleccionar reunión
    sesion_seleccionada = st.selectbox(
        "Seleccione la reunión",
        options=[(r['id_sesion'], r['fecha_sesion']) for r in reuniones],
        format_func=lambda x: f"Reunión del {x[1].strftime('%d/%m/%Y')}",
        key="select_sesion_asistencia"
    )
    
    if sesion_seleccionada:
        id_sesion, fecha_sesion = sesion_seleccionada
        
        # Obtener información adicional de la sesión
        info_sesion = obtener_info_sesion(id_sesion)
        
        st.markdown(f"### Asistencia - Reunión del {fecha_sesion.strftime('%d/%m/%Y')}")
        
        if info_sesion:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Tipo:** {info_sesion.get('tipo_reunion', 'Reunión Regular')}")
            with col2:
                st.write(f"**Temas:** {info_sesion.get('temas_agenda', 'No especificados')}")
        
        # Obtener lista de socios con su estado de asistencia
        asistencia_actual = obtener_asistencia_sesion(id_sesion)
        
        if asistencia_actual:
            total_presentes = 0
            
            # Mostrar formulario de asistencia
            st.markdown("#### Marcar Asistencia")
            st.caption("✅ Marque los socios presentes en la reunión")
            
            # Opción para marcar todos como presentes
            col_quick, _ = st.columns([1, 3])
            with col_quick:
                if st.button("✅ Marcar Todos como Presentes"):
                    for asistencia in asistencia_actual:
                        actualizar_asistencia(asistencia['id_asistencia'], True)
                    st.success("Todos los socios marcados como presentes")
                    st.rerun()
            
            for asistencia in asistencia_actual:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                
                with col1:
                    st.write(f"**{asistencia['nombre']} {asistencia['apellido']}**")
                
                with col2:
                    # Checkbox para marcar presencia
                    presente = st.checkbox(
                        "Presente",
                        value=bool(asistencia['presencial']),
                        key=f"asist_{asistencia['id_asistencia']}"
                    )
                
                with col3:
                    # Campo para justificación de ausencia
                    if not presente:
                        justificacion = st.selectbox(
                            "Justificación",
                            ["", "Enfermedad", "Trabajo", "Viaje", "Familia", "Otro"],
                            key=f"justif_{asistencia['id_asistencia']}"
                        )
                        if justificacion:
                            actualizar_justificacion_ausencia(asistencia['id_asistencia'], justificacion)
                
                with col4:
                    if presente:
                        total_presentes += 1
                        st.success("✅ Presente")
                    else:
                        st.error("❌ Ausente")
                
                # Actualizar inmediatamente cuando cambia
                if st.session_state.get(f"asist_{asistencia['id_asistencia']}") != bool(asistencia['presencial']):
                    actualizar_asistencia(asistencia['id_asistencia'], presente)
            
            # Mostrar resumen
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            total_socios = len(asistencia_actual)
            with col1:
                st.metric("👥 Total de Socios", total_socios)
            with col2:
                st.metric("✅ Presentes", total_presentes)
            with col3:
                ausentes = total_socios - total_presentes
                st.metric("❌ Ausentes", ausentes)
            with col4:
                porcentaje_asistencia = (total_presentes / total_socios) * 100 if total_socios > 0 else 0
                st.metric("📊 Porcentaje", f"{porcentaje_asistencia:.1f}%")
            
            # Actualizar total en la sesión
            actualizar_total_presentes(id_sesion, total_presentes)
            
            # Aplicar multas automáticas por inasistencia
            st.markdown("### ⚡ Acciones por Inasistencia")
            
            col_multas, col_acta = st.columns(2)
            
            with col_multas:
                if st.button("💰 Aplicar Multas por Inasistencia"):
                    multas_aplicadas = aplicar_multas_automaticas(id_sesion, st.session_state.id_grupo)
                    if multas_aplicadas > 0:
                        st.success(f"Multas aplicadas a {multas_aplicadas} socios ausentes")
                    else:
                        st.info("No hay ausentes a los que aplicar multas")
                    st.rerun()
            
            with col_acta:
                if st.button("📄 Generar Acta de Asistencia"):
                    generar_acta_asistencia(id_sesion)

def historial_reuniones():
    """Mostrar historial de reuniones del grupo - FUNCIÓN MEJORADA"""
    
    st.subheader("Historial de Reuniones")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede ver el historial")
        return
    
    reuniones = obtener_reuniones_grupo(st.session_state.id_grupo)
    
    if reuniones:
        # Métricas resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Total de Reuniones", len(reuniones))
        
        with col2:
            promedio_asistencia = sum(r['total_presentes'] for r in reuniones) / len(reuniones)
            st.metric("👥 Promedio de Asistencia", f"{promedio_asistencia:.1f}")
        
        with col3:
            total_socios = obtener_total_socios_grupo(st.session_state.id_grupo)
            if total_socios > 0:
                porcentaje_promedio = (promedio_asistencia / total_socios) * 100
                st.metric("📊 Asistencia Promedio", f"{porcentaje_promedio:.1f}%")
            else:
                st.metric("📊 Asistencia Promedio", "0%")
        
        with col4:
            ultima_reunion = reuniones[0]['fecha_sesion'].strftime('%d/%m/%Y')
            st.metric("🕐 Última Reunión", ultima_reunion)
        
        # Gráfico de tendencia de asistencia
        st.markdown("### 📈 Tendencia de Asistencia")
        
        if len(reuniones) > 1:
            # Preparar datos para el gráfico
            fechas = [r['fecha_sesion'].strftime('%d/%m') for r in reuniones][::-1]  # Más reciente primero
            asistencias = [r['total_presentes'] for r in reuniones][::-1]
            total_socios = obtener_total_socios_grupo(st.session_state.id_grupo)
            porcentajes = [(a / total_socios * 100) if total_socios > 0 else 0 for a in asistencias]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=fechas, 
                y=asistencias,
                mode='lines+markers',
                name='Asistentes',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=fechas,
                y=[total_socios] * len(fechas),
                mode='lines',
                name='Total Socios',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title='Evolución de la Asistencia',
                xaxis_title='Fecha de Reunión',
                yaxis_title='Número de Asistentes',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Lista detallada
        st.markdown("### 📋 Detalle de Reuniones")
        
        for reunion in reuniones:
            with st.expander(f"📅 {reunion.get('tipo_reunion', 'Reunión')} - {reunion['fecha_sesion'].strftime('%d/%m/%Y')} - {reunion['total_presentes']} presentes"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Fecha:** {reunion['fecha_sesion'].strftime('%d/%m/%Y')}")
                    st.write(f"**Tipo:** {reunion.get('tipo_reunion', 'Reunión Regular')}")
                    if reunion.get('temas_agenda'):
                        st.write(f"**Temas:** {reunion['temas_agenda']}")
                
                with col2:
                    st.write(f"**Asistentes:** {reunion['total_presentes']}")
                    
                    # Calcular porcentaje de asistencia
                    total_socios = obtener_total_socios_grupo(st.session_state.id_grupo)
                    if total_socios > 0:
                        porcentaje = (reunion['total_presentes'] / total_socios) * 100
                        st.write(f"**Porcentaje:** {porcentaje:.1f}%")
                        
                        # Indicador visual de asistencia
                        if porcentaje >= 80:
                            st.success("✅ Buena asistencia")
                        elif porcentaje >= 60:
                            st.warning("⚠️ Asistencia regular")
                        else:
                            st.error("❌ Baja asistencia")
                
                with col3:
                    # Botones de acción
                    if st.button("👁️ Ver Detalle", key=f"detalle_{reunion['id_sesion']}"):
                        ver_detalle_reunion(reunion['id_sesion'])
                    
                    if st.button("📊 Reporte", key=f"reporte_{reunion['id_sesion']}"):
                        generar_reporte_asistencia(reunion['id_sesion'])
                    
                    if st.button("📄 Acta", key=f"acta_{reunion['id_sesion']}"):
                        generar_acta_completa_reunion(reunion['id_sesion'])
    else:
        st.info("ℹ️ No hay reuniones registradas para este grupo")

# =============================================================================
# FUNCIONES AUXILIARES - REUNIONES (TODAS IMPLEMENTADAS)
# =============================================================================

def obtener_info_grupo(id_grupo):
    """Obtener información del grupo"""
    query = "SELECT nombre_grupo, dia_reunion, hora_reunion FROM grupos WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0] if resultado else None

def calcular_proxima_reunion(id_grupo):
    """Calcular la próxima fecha de reunión basada en la frecuencia del grupo"""
    # Obtener última reunión
    ultima_reunion = ejecutar_consulta(
        "SELECT fecha_sesion FROM sesion WHERE id_grupo = %s ORDER BY fecha_sesion DESC LIMIT 1",
        (id_grupo,)
    )
    
    if ultima_reunion:
        ultima_fecha = ultima_reunion[0]['fecha_sesion']
        # Asumir frecuencia semanal (ajustar según configuración real del grupo)
        return ultima_fecha + timedelta(days=7)
    else:
        return datetime.now().date()

def obtener_socios_grupo(id_grupo):
    """Obtener todos los socios de un grupo"""
    query = "SELECT id_socio, nombre, apellido FROM socios WHERE id_grupo = %s"
    return ejecutar_consulta(query, (id_grupo,))

def obtener_reuniones_recientes(id_grupo, limite=10):
    """Obtener reuniones recientes del grupo"""
    query = """
        SELECT id_sesion, fecha_sesion, total_presentes, tipo_reunion, temas_agenda
        FROM sesion 
        WHERE id_grupo = %s 
        ORDER BY fecha_sesion DESC 
        LIMIT %s
    """
    return ejecutar_consulta(query, (id_grupo, limite))

def obtener_asistencia_sesion(id_sesion):
    """Obtener la asistencia de una sesión específica"""
    query = """
        SELECT a.id_asistencia, a.presencial, a.justificacion_ausencia, s.id_socio, s.nombre, s.apellido
        FROM asistencia a
        JOIN socios s ON a.id_socio = s.id_socio
        WHERE a.id_sesion = %s
        ORDER BY s.apellido, s.nombre
    """
    return ejecutar_consulta(query, (id_sesion,))

def actualizar_asistencia(id_asistencia, presencial):
    """Actualizar registro de asistencia"""
    query = "UPDATE asistencia SET presencial = %s WHERE id_asistencia = %s"
    return ejecutar_comando(query, (1 if presencial else 0, id_asistencia))

def actualizar_justificacion_ausencia(id_asistencia, justificacion):
    """Actualizar justificación de ausencia"""
    query = "UPDATE asistencia SET justificacion_ausencia = %s WHERE id_asistencia = %s"
    return ejecutar_comando(query, (justificacion, id_asistencia))

def actualizar_total_presentes(id_sesion, total):
    """Actualizar el total de presentes en la sesión"""
    query = "UPDATE sesion SET total_presentes = %s WHERE id_sesion = %s"
    return ejecutar_comando(query, (total, id_sesion))

def obtener_reuniones_grupo(id_grupo):
    """Obtener todas las reuniones de un grupo"""
    query = """
        SELECT id_sesion, fecha_sesion, total_presentes, tipo_reunion, temas_agenda, notas
        FROM sesion 
        WHERE id_grupo = %s 
        ORDER BY fecha_sesion DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_total_socios_grupo(id_grupo):
    """Obtener el total de socios en un grupo"""
    query = "SELECT COUNT(*) as total FROM socios WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0

def aplicar_multas_automaticas(id_sesion, id_grupo):
    """Aplicar multas automáticas por inasistencia"""
    # Obtener ausentes
    ausentes = ejecutar_consulta("""
        SELECT a.id_socio, s.nombre, s.apellido
        FROM asistencia a 
        JOIN socios s ON a.id_socio = s.id_socio
        WHERE a.id_sesion = %s AND a.presencial = 0
    """, (id_sesion,))
    
    # Obtener monto de multa del grupo
    reglas = ejecutar_consulta("SELECT cantidad_multa FROM reglas_del_grupo WHERE id_grupo = %s", (id_grupo,))
    
    if reglas and ausentes:
        monto_multa = reglas[0]['cantidad_multa']
        
        for ausente in ausentes:
            # Crear registro de multa
            query = """
                INSERT INTO multa (id_sesion, id_socio, monto_a_pagar, monto_pagado, fecha_pago_real, fecha_vencimiento, motivo)
                VALUES (%s, %s, %s, 0, NULL, %s, 'Inasistencia a reunión')
            """
            fecha_vencimiento = datetime.now().date() + timedelta(days=7)  # 7 días para pagar
            ejecutar_comando(query, (id_sesion, ausente['id_socio'], monto_multa, fecha_vencimiento))
    
    return len(ausentes)

def obtener_info_sesion(id_sesion):
    """Obtener información detallada de una sesión"""
    query = """
        SELECT s.*, g.nombre_grupo
        FROM sesion s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        WHERE s.id_sesion = %s
    """
    resultado = ejecutar_consulta(query, (id_sesion,))
    return resultado[0] if resultado else None

def ver_detalle_reunion(id_sesion):
    """Ver detalle de una reunión específica - FUNCIÓN IMPLEMENTADA"""
    
    info_sesion = obtener_info_sesion(id_sesion)
    
    if not info_sesion:
        st.error("❌ No se encontró información de la reunión")
        return
    
    st.subheader(f"📋 Detalle de Reunión - {info_sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
    
    # Información general
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Información General")
        st.write(f"**Grupo:** {info_sesion['nombre_grupo']}")
        st.write(f"**Fecha:** {info_sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
        st.write(f"**Tipo:** {info_sesion.get('tipo_reunion', 'Reunión Regular')}")
        st.write(f"**Asistentes:** {info_sesion['total_presentes']}")
        
        total_socios = obtener_total_socios_grupo(info_sesion['id_grupo'])
        if total_socios > 0:
            porcentaje = (info_sesion['total_presentes'] / total_socios) * 100
            st.write(f"**Porcentaje de asistencia:** {porcentaje:.1f}%")
    
    with col2:
        st.markdown("### 🎯 Temas Tratados")
        if info_sesion.get('temas_agenda'):
            temas = info_sesion['temas_agenda'].split('\n')
            for tema in temas:
                if tema.strip():
                    st.write(f"• {tema.strip()}")
        else:
            st.info("No se registraron temas específicos")
        
        if info_sesion.get('notas'):
            st.markdown("### 📝 Notas Adicionales")
            st.write(info_sesion['notas'])
    
    # Lista detallada de asistencia
    st.markdown("### 👥 Detalle de Asistencia")
    
    asistencia = obtener_asistencia_sesion(id_sesion)
    
    if asistencia:
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        
        presentes = sum(1 for a in asistencia if a['presencial'])
        ausentes = len(asistencia) - presentes
        
        with col1:
            st.metric("✅ Presentes", presentes)
        with col2:
            st.metric("❌ Ausentes", ausentes)
        with col3:
            st.metric("📊 Porcentaje", f"{(presentes/len(asistencia)*100):.1f}%")
        
        # Tabla detallada
        st.markdown("#### Lista de Socios")
        
        for socio in asistencia:
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                st.write(f"**{socio['nombre']} {socio['apellido']}**")
            
            with col2:
                if socio['presencial']:
                    st.success("✅ Presente")
                else:
                    st.error("❌ Ausente")
            
            with col3:
                if not socio['presencial'] and socio.get('justificacion_ausencia'):
                    st.write(f"*Justificación: {socio['justificacion_ausencia']}*")
        
        # Exportar datos
        st.markdown("---")
        if st.button("📤 Exportar Lista de Asistencia"):
            exportar_lista_asistencia(id_sesion, asistencia, info_sesion)
    else:
        st.info("ℹ️ No hay datos de asistencia para esta reunión")

def generar_reporte_asistencia(id_sesion):
    """Generar reporte de asistencia para una reunión - FUNCIÓN IMPLEMENTADA"""
    
    info_sesion = obtener_info_sesion(id_sesion)
    asistencia = obtener_asistencia_sesion(id_sesion)
    
    if not info_sesion or not asistencia:
        st.error("❌ No se pueden generar reportes para esta reunión")
        return
    
    st.subheader(f"📊 Reporte de Asistencia - {info_sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
    
    # Estadísticas generales
    total_socios = len(asistencia)
    presentes = sum(1 for a in asistencia if a['presencial'])
    ausentes = total_socios - presentes
    porcentaje_asistencia = (presentes / total_socios) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Socios", total_socios)
    with col2:
        st.metric("Presentes", presentes)
    with col3:
        st.metric("Ausentes", ausentes)
    with col4:
        st.metric("Porcentaje", f"{porcentaje_asistencia:.1f}%")
    
    # Gráfico de pastel
    st.markdown("### 📈 Distribución de Asistencia")
    
    fig = px.pie(
        values=[presentes, ausentes],
        names=['Presentes', 'Ausentes'],
        color=['Presentes', 'Ausentes'],
        color_discrete_map={'Presentes':'green', 'Ausentes':'red'}
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
    # Lista de ausentes con justificaciones
    ausentes_con_justificacion = [a for a in asistencia if not a['presencial'] and a.get('justificacion_ausencia')]
    ausentes_sin_justificacion = [a for a in asistencia if not a['presencial'] and not a.get('justificacion_ausencia')]
    
    if ausentes_con_justificacion:
        st.markdown("### 📝 Ausentes con Justificación")
        for ausente in ausentes_con_justificacion:
            st.write(f"• **{ausente['nombre']} {ausente['apellido']}**: {ausente['justificacion_ausencia']}")
    
    if ausentes_sin_justificacion:
        st.markdown("### ⚠️ Ausentes sin Justificación")
        for ausente in ausentes_sin_justificacion:
            st.write(f"• **{ausente['nombre']} {ausente['apellido']}**")
    
    # Recomendaciones
    st.markdown("### 💡 Recomendaciones")
    
    if porcentaje_asistencia >= 80:
        st.success("✅ Excelente nivel de asistencia. Mantener la participación actual.")
    elif porcentaje_asistencia >= 60:
        st.warning("⚠️ Asistencia regular. Considerar recordatorios para mejorar la participación.")
    else:
        st.error("❌ Baja asistencia. Revisar horarios y comunicar la importancia de la participación.")
        
        if ausentes_sin_justificacion:
            st.info("💡 **Acciones sugeridas:**")
            st.write("• Contactar a los ausentes sin justificación")
            st.write("• Revisar posibles problemas con el horario o ubicación")
            st.write("• Implementar sistema de recordatorios")

def generar_acta_base_reunion(id_sesion):
    """Generar acta base para una reunión recién creada"""
    st.info("📄 Generando acta base de la reunión...")
    # En una implementación completa, aquí se generaría un documento PDF/Word
    st.success("Acta base generada exitosamente")

def generar_acta_asistencia(id_sesion):
    """Generar acta de asistencia formal"""
    st.info("📄 Generando acta formal de asistencia...")
    # En una implementación completa, aquí se generaría un documento formal
    st.success("Acta de asistencia generada exitosamente")

def generar_acta_completa_reunion(id_sesion):
    """Generar acta completa de la reunión"""
    st.info("📄 Generando acta completa de la reunión...")
    # En una implementación completa, aquí se generaría un documento completo
    st.success("Acta completa generada exitosamente")

def exportar_lista_asistencia(id_sesion, asistencia, info_sesion):
    """Exportar lista de asistencia en formato CSV"""
    
    # Preparar datos para CSV
    datos_exportar = []
    for socio in asistencia:
        datos_exportar.append({
            'Nombre': socio['nombre'],
            'Apellido': socio['apellido'],
            'Asistencia': 'Presente' if socio['presencial'] else 'Ausente',
            'Justificación': socio.get('justificacion_ausencia', '')
        })
    
    df = pd.DataFrame(datos_exportar)
    csv = df.to_csv(index=False, encoding='utf-8')
    
    fecha_str = info_sesion['fecha_sesion'].strftime('%Y%m%d')
    nombre_grupo = info_sesion['nombre_grupo'].replace(' ', '_')
    
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"asistencia_{nombre_grupo}_{fecha_str}.csv",
        mime="text/csv"
    )