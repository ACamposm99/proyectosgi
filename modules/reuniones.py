import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta

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
    """Crear una nueva reunión/sesión"""
    
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
                value=datetime.strptime(grupo_info['hora_reunion'], '%H:%M:%S').time() if grupo_info else datetime.now().time()
            )
        
        notas_adicionales = st.text_area("📝 Notas adicionales (opcional)", placeholder="Temas tratados, observaciones...")
        
        submitted = st.form_submit_button("💾 Crear Reunión")
        
        if submitted:
            id_sesion = crear_sesion(st.session_state.id_grupo, fecha_sesion, notas_adicionales)
            if id_sesion:
                st.success(f"✅ Reunión creada exitosamente (Sesión #{id_sesion})")
                
                # Inicializar registros de asistencia automáticamente
                if inicializar_asistencia(id_sesion, st.session_state.id_grupo):
                    st.info("📋 Registros de asistencia inicializados para todos los socios")
                
                st.rerun()

def crear_sesion(id_grupo, fecha_sesion, notas=""):
    """Crear nueva sesión/reunión en la base de datos"""
    
    query = """
        INSERT INTO sesion (id_grupo, fecha_sesion, total_presentes)
        VALUES (%s, %s, 0)
    """
    
    id_sesion = ejecutar_comando(query, (id_grupo, fecha_sesion))
    
    if id_sesion and notas:
        # Guardar notas en una tabla auxiliar (si existe) o en grupos
        pass
    
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
    """Registro de asistencia para una reunión existente"""
    
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
        
        st.markdown(f"### Asistencia - Reunión del {fecha_sesion.strftime('%d/%m/%Y')}")
        
        # Obtener lista de socios con su estado de asistencia
        asistencia_actual = obtener_asistencia_sesion(id_sesion)
        
        if asistencia_actual:
            total_presentes = 0
            
            # Mostrar formulario de asistencia
            st.markdown("#### Marcar Asistencia")
            st.caption("✅ Marque los socios presentes en la reunión")
            
            for asistencia in asistencia_actual:
                col1, col2, col3 = st.columns([3, 1, 2])
                
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
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👥 Total de Socios", len(asistencia_actual))
            with col2:
                st.metric("✅ Presentes", total_presentes)
            with col3:
                st.metric("❌ Ausentes", len(asistencia_actual) - total_presentes)
            
            # Actualizar total en la sesión
            actualizar_total_presentes(id_sesion, total_presentes)
            
            # Aplicar multas automáticas por inasistencia
            if st.button("⚡ Aplicar Multas por Inasistencia"):
                aplicar_multas_automaticas(id_sesion, st.session_state.id_grupo)
                st.success("Multas aplicadas automáticamente a los ausentes")
                st.rerun()

def historial_reuniones():
    """Mostrar historial de reuniones del grupo"""
    
    st.subheader("Historial de Reuniones")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede ver el historial")
        return
    
    reuniones = obtener_reuniones_grupo(st.session_state.id_grupo)
    
    if reuniones:
        # Métricas resumen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📅 Total de Reuniones", len(reuniones))
        
        with col2:
            promedio_asistencia = sum(r['total_presentes'] for r in reuniones) / len(reuniones)
            st.metric("👥 Promedio de Asistencia", f"{promedio_asistencia:.1f}")
        
        with col3:
            ultima_reunion = reuniones[0]['fecha_sesion'].strftime('%d/%m/%Y')
            st.metric("🕐 Última Reunión", ultima_reunion)
        
        # Lista detallada
        st.markdown("### Detalle de Reuniones")
        
        for reunion in reuniones:
            with st.expander(f"📅 Reunión del {reunion['fecha_sesion'].strftime('%d/%m/%Y')} - {reunion['total_presentes']} presentes"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Fecha:** {reunion['fecha_sesion'].strftime('%d/%m/%Y')}")
                    st.write(f"**Asistentes:** {reunion['total_presentes']}")
                    
                    # Calcular porcentaje de asistencia
                    total_socios = obtener_total_socios_grupo(st.session_state.id_grupo)
                    if total_socios > 0:
                        porcentaje = (reunion['total_presentes'] / total_socios) * 100
                        st.write(f"**Porcentaje de asistencia:** {porcentaje:.1f}%")
                
                with col2:
                    # Botones de acción
                    if st.button("👁️ Ver Detalle", key=f"detalle_{reunion['id_sesion']}"):
                        ver_detalle_reunion(reunion['id_sesion'])
                    
                    if st.button("📊 Reporte Asistencia", key=f"reporte_{reunion['id_sesion']}"):
                        generar_reporte_asistencia(reunion['id_sesion'])
    else:
        st.info("ℹ️ No hay reuniones registradas para este grupo")

# =============================================================================
# FUNCIONES AUXILIARES - REUNIONES
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
        SELECT id_sesion, fecha_sesion, total_presentes 
        FROM sesion 
        WHERE id_grupo = %s 
        ORDER BY fecha_sesion DESC 
        LIMIT %s
    """
    return ejecutar_consulta(query, (id_grupo, limite))

def obtener_asistencia_sesion(id_sesion):
    """Obtener la asistencia de una sesión específica"""
    query = """
        SELECT a.id_asistencia, a.presencial, s.id_socio, s.nombre, s.apellido
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

def actualizar_total_presentes(id_sesion, total):
    """Actualizar el total de presentes en la sesión"""
    query = "UPDATE sesion SET total_presentes = %s WHERE id_sesion = %s"
    return ejecutar_comando(query, (total, id_sesion))

def obtener_reuniones_grupo(id_grupo):
    """Obtener todas las reuniones de un grupo"""
    query = """
        SELECT id_sesion, fecha_sesion, total_presentes 
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
        SELECT a.id_socio 
        FROM asistencia a 
        WHERE a.id_sesion = %s AND a.presencial = 0
    """, (id_sesion,))
    
    # Obtener monto de multa del grupo
    reglas = ejecutar_consulta("SELECT cantidad_multa FROM reglas_del_grupo WHERE id_grupo = %s", (id_grupo,))
    
    if reglas and ausentes:
        monto_multa = reglas[0]['cantidad_multa']
        
        for ausente in ausentes:
            # Crear registro de multa
            query = """
                INSERT INTO multa (id_sesion, id_socio, monto_a_pagar, monto_pagado, fecha_pago_real, fecha_vencimiento)
                VALUES (%s, %s, %s, 0, NULL, %s)
            """
            fecha_vencimiento = datetime.now().date() + timedelta(days=7)  # 7 días para pagar
            ejecutar_comando(query, (id_sesion, ausente['id_socio'], monto_multa, fecha_vencimiento))
    
    return len(ausentes)

def ver_detalle_reunion(id_sesion):
    """Ver detalle de una reunión específica"""
    st.info(f"🔧 Funcionalidad en desarrollo - Detalle de reunión #{id_sesion}")

def generar_reporte_asistencia(id_sesion):
    """Generar reporte de asistencia para una reunión"""
    st.info(f"🔧 Funcionalidad en desarrollo - Reporte de asistencia #{id_sesion}")