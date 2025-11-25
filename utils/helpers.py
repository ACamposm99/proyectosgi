import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime, timedelta

def mostrar_dashboard_principal():
    """Dashboard principal con métricas del sistema"""
    
    st.title("📊 Dashboard Principal")
    
    # Obtener métricas según el rol
    if st.session_state.rol == "ADMIN":
        mostrar_dashboard_admin()
    elif st.session_state.rol == "PROMOTORA":
        mostrar_dashboard_promotora()
    else:  # DIRECTIVA
        mostrar_dashboard_directiva()

def mostrar_dashboard_admin():
    """Dashboard para administradores"""
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_grupos = obtener_metricas("SELECT COUNT(*) as total FROM grupos WHERE estado = 'ACTIVO'")
        st.metric("🏢 Grupos Activos", total_grupos[0]['total'] if total_grupos else 0)
    
    with col2:
        total_socios = obtener_metricas("SELECT COUNT(*) as total FROM socios WHERE estado = 'ACTIVO'")
        st.metric("👥 Total Socios", total_socios[0]['total'] if total_socios else 0)
    
    with col3:
        total_distritos = obtener_metricas("SELECT COUNT(*) as total FROM distritos")
        st.metric("🗺️ Distritos", total_distritos[0]['total'] if total_distritos else 0)
    
    with col4:
        total_promotores = obtener_metricas("SELECT COUNT(*) as total FROM promotores WHERE estado = 'ACTIVO'")
        st.metric("👩‍💼 Promotores", total_promotores[0]['total'] if total_promotores else 0)
    
    # Métricas financieras
    st.subheader("💰 Métricas Financieras")
    col1, col2, col3 = st.columns(3)  # Reducido a 3 columnas
    
    with col1:
        total_ahorro = obtener_metricas("SELECT COALESCE(SUM(saldo_actual), 0) as total FROM ahorros")
        st.metric("💵 Ahorro Total", f"${total_ahorro[0]['total']:,.2f}" if total_ahorro else "$0.00")
    
    with col2:
        total_prestamos = obtener_metricas("SELECT COALESCE(SUM(saldo_pendiente), 0) as total FROM prestamos WHERE estado = 'VIGENTE'")
        st.metric("🏦 Préstamos Vigentes", f"${total_prestamos[0]['total']:,.2f}" if total_prestamos else "$0.00")
    
    with col3:
        caja_total = obtener_metricas("SELECT COALESCE(SUM(saldo), 0) as total FROM caja")
        st.metric("💳 Caja Total", f"${caja_total[0]['total']:,.2f}" if caja_total else "$0.00")
    
    # Grupos recientes
    st.subheader("🎯 Grupos Recientes")
    grupos_recientes = ejecutar_consulta("""
        SELECT nombre_grupo, fecha_creacion, lugar_reunion, nombre_distrito 
        FROM grupos g 
        LEFT JOIN distritos d ON g.id_distrito = d.id_distrito
        WHERE g.estado = 'ACTIVO'
        ORDER BY fecha_creacion DESC 
        LIMIT 5
    """)
    
    if grupos_recientes:
        for grupo in grupos_recientes:
            distrito = grupo['nombre_distrito'] or "Sin distrito"
            st.write(f"• **{grupo['nombre_grupo']}** - {distrito} - Creado: {grupo['fecha_creacion'].strftime('%d/%m/%Y')}")
    else:
        st.info("ℹ️ No hay grupos registrados")

def mostrar_dashboard_directiva():
    """Dashboard para directiva de grupo"""
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ No tiene un grupo asignado")
        return
    
    # Métricas del grupo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_socios = obtener_metricas(
            "SELECT COUNT(*) as total FROM socios WHERE id_grupo = %s AND estado = 'ACTIVO'",
            (st.session_state.id_grupo,)
        )
        st.metric("👥 Socios Activos", total_socios[0]['total'] if total_socios else 0)
    
    with col2:
        proxima_reunion = obtener_proxima_reunion(st.session_state.id_grupo)
        if proxima_reunion:
            st.metric("📅 Próxima Reunión", proxima_reunion.strftime('%d/%m'))
        else:
            st.metric("📅 Próxima Reunión", "No programada")
    
    with col3:
        ahorro_total = obtener_metricas(
            "SELECT COALESCE(SUM(saldo_actual), 0) as total FROM ahorros WHERE id_grupo = %s",
            (st.session_state.id_grupo,)
        )
        st.metric("💰 Ahorro Total", f"${ahorro_total[0]['total']:,.2f}" if ahorro_total else "$0.00")
    
    with col4:
        prestamos_vigentes = obtener_metricas(
            "SELECT COUNT(*) as total FROM prestamos WHERE id_grupo = %s AND estado = 'VIGENTE'",
            (st.session_state.id_grupo,)
        )
        st.metric("🏦 Préstamos Activos", prestamos_vigentes[0]['total'] if prestamos_vigentes else 0)
    
    # Métricas financieras del grupo
    st.subheader("📊 Estado Financiero del Grupo")
    col1, col2 = st.columns(2)  # Reducido a 2 columnas
    
    with col1:
        total_prestamos = obtener_metricas(
            "SELECT COALESCE(SUM(saldo_pendiente), 0) as total FROM prestamos WHERE id_grupo = %s AND estado = 'VIGENTE'",
            (st.session_state.id_grupo,)
        )
        st.metric("📈 Préstamos Vigentes", f"${total_prestamos[0]['total']:,.2f}" if total_prestamos else "$0.00")
    
    with col2:
        caja_grupo = obtener_metricas(
            "SELECT COALESCE(SUM(saldo), 0) as total FROM caja WHERE id_grupo = %s",
            (st.session_state.id_grupo,)
        )
        st.metric("💳 Caja del Grupo", f"${caja_grupo[0]['total']:,.2f}" if caja_grupo else "$0.00")
    
    # Acciones rápidas
    st.subheader("🚀 Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Registrar Reunión", use_container_width=True):
            st.session_state.current_page = "📅 Reuniones y Asistencia"
            st.rerun()
    
    with col2:
        if st.button("👥 Gestionar Socios", use_container_width=True):
            st.session_state.current_page = "👥 Gestión de Socios"
            st.rerun()
    
    with col3:
        if st.button("💰 Registrar Aportes", use_container_width=True):
            st.session_state.current_page = "💰 Aportes de Ahorro"
            st.rerun()

def mostrar_dashboard_promotora():
    """Dashboard para promotoras"""
    
    # Obtener ID de la promotora desde la sesión
    if 'id_promotora' not in st.session_state:
        # Buscar el ID de la promotora basado en el usuario
        promotora_data = ejecutar_consulta(
            "SELECT id_promotora FROM promotores WHERE usuario = %s",
            (st.session_state.usuario,)
        )
        if promotora_data:
            st.session_state.id_promotora = promotora_data[0]['id_promotora']
        else:
            st.error("❌ No se pudo identificar a la promotora")
            return
    
    id_promotora = st.session_state.id_promotora
    
    # Métricas generales de la promotora
    st.subheader("📈 Métricas de Supervisión")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        grupos_asignados = obtener_metricas(
            "SELECT COUNT(*) as total FROM grupos WHERE id_promotora = %s AND estado = 'ACTIVO'",
            (id_promotora,)
        )
        st.metric("🏢 Grupos Asignados", grupos_asignados[0]['total'] if grupos_asignados else 0)
    
    with col2:
        total_socios = obtener_metricas(
            "SELECT COUNT(*) as total FROM socios s JOIN grupos g ON s.id_grupo = g.id_grupo WHERE g.id_promotora = %s AND s.estado = 'ACTIVO'",
            (id_promotora,)
        )
        st.metric("👥 Total Socios", total_socios[0]['total'] if total_socios else 0)
    
    with col3:
        reuniones_semana = obtener_metricas(
            """SELECT COUNT(*) as total FROM reuniones r 
               JOIN grupos g ON r.id_grupo = g.id_grupo 
               WHERE g.id_promotora = %s AND r.fecha >= %s""",
            (id_promotora, datetime.now().date() - timedelta(days=7))
        )
        st.metric("📅 Reuniones (7d)", reuniones_semana[0]['total'] if reuniones_semana else 0)
    
    with col4:
        aprobaciones_pendientes = obtener_metricas(
            """SELECT COUNT(*) as total FROM prestamos p 
               JOIN grupos g ON p.id_grupo = g.id_grupo 
               WHERE g.id_promotora = %s AND p.estado = 'PENDIENTE'""",
            (id_promotora,)
        )
        st.metric("⏳ Préstamos por Validar", aprobaciones_pendientes[0]['total'] if aprobaciones_pendientes else 0)
    
    # Métricas financieras
    st.subheader("💰 Estado Financiero de Grupos")
    
    col1, col2 = st.columns(2)  # Reducido a 2 columnas
    
    with col1:
        ahorro_total = obtener_metricas(
            "SELECT COALESCE(SUM(a.saldo_actual), 0) as total FROM ahorros a JOIN grupos g ON a.id_grupo = g.id_grupo WHERE g.id_promotora = %s",
            (id_promotora,)
        )
        st.metric("💵 Ahorro Total", f"${ahorro_total[0]['total']:,.2f}" if ahorro_total else "$0.00")
    
    with col2:
        prestamos_vigentes = obtener_metricas(
            "SELECT COALESCE(SUM(p.saldo_pendiente), 0) as total FROM prestamos p JOIN grupos g ON p.id_grupo = g.id_grupo WHERE g.id_promotora = %s AND p.estado = 'VIGENTE'",
            (id_promotora,)
        )
        st.metric("🏦 Préstamos Vigentes", f"${prestamos_vigentes[0]['total']:,.2f}" if prestamos_vigentes else "$0.00")
    
    # Grupos asignados con detalles
    st.subheader("🎯 Grupos Asignados")
    
    grupos = ejecutar_consulta(
        """SELECT g.id_grupo, g.nombre_grupo, g.lugar_reunion, g.fecha_creacion, 
                  COUNT(s.id_socio) as socios_activos,
                  COALESCE(SUM(a.saldo_actual), 0) as total_ahorro
           FROM grupos g 
           LEFT JOIN socios s ON g.id_grupo = s.id_grupo AND s.estado = 'ACTIVO'
           LEFT JOIN ahorros a ON g.id_grupo = a.id_grupo
           WHERE g.id_promotora = %s AND g.estado = 'ACTIVO'
           GROUP BY g.id_grupo, g.nombre_grupo, g.lugar_reunion, g.fecha_creacion
           ORDER BY g.fecha_creacion DESC""",
        (id_promotora,)
    )
    
    if grupos:
        for grupo in grupos:
            with st.expander(f"🏢 {grupo['nombre_grupo']} - {grupo['socios_activos']} socios - Ahorro: ${grupo['total_ahorro']:,.2f}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Lugar reunión:** {grupo['lugar_reunion']}")
                    st.write(f"**Fecha creación:** {grupo['fecha_creacion'].strftime('%d/%m/%Y')}")
                
                with col2:
                    # Próxima reunión del grupo
                    prox_reunion = obtener_proxima_reunion(grupo['id_grupo'])
                    if prox_reunion:
                        st.write(f"**Próxima reunión:** {prox_reunion.strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.write("**Próxima reunión:** No programada")
                    
                    # Acciones rápidas por grupo
                    if st.button(f"👁️ Supervisar", key=f"supervisar_{grupo['id_grupo']}"):
                        st.session_state.grupo_seleccionado = grupo['id_grupo']
                        st.session_state.current_page = "👁️ Supervisión Grupos"
                        st.rerun()
    else:
        st.info("ℹ️ No hay grupos asignados para supervisión")

def obtener_metricas(query, params=None):
    """Obtener métricas desde la base de datos"""
    try:
        return ejecutar_consulta(query, params)
    except Exception as e:
        st.error(f"Error al obtener métricas: {str(e)}")
        return None

def obtener_proxima_reunion(id_grupo):
    """Obtener la próxima reunión programada para el grupo"""
    try:
        reuniones = ejecutar_consulta(
            """SELECT fecha, hora, lugar 
               FROM reuniones 
               WHERE id_grupo = %s AND fecha >= %s 
               ORDER BY fecha, hora ASC 
               LIMIT 1""",
            (id_grupo, datetime.now().date())
        )
        
        if reuniones and reuniones[0]['fecha']:
            # Combinar fecha y hora si están separadas
            fecha = reuniones[0]['fecha']
            hora = reuniones[0]['hora'] or datetime.now().time()
            return datetime.combine(fecha, hora)
        return None
    except Exception as e:
        st.error(f"Error al obtener próxima reunión: {str(e)}")
        return None