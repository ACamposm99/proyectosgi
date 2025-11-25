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
        total_grupos = obtener_metricas("SELECT COUNT(*) as total FROM grupos")
        st.metric("🏢 Grupos Totales", total_grupos[0]['total'] if total_grupos else 0)
    
    with col2:
        total_socios = obtener_metricas("SELECT COUNT(*) as total FROM socios")
        st.metric("👥 Total Socios", total_socios[0]['total'] if total_socios else 0)
    
    with col3:
        total_distritos = obtener_metricas("SELECT COUNT(*) as total FROM distrito")
        st.metric("🗺️ Distritos", total_distritos[0]['total'] if total_distritos else 0)
    
    with col4:
        total_promotores = obtener_metricas("SELECT COUNT(*) as total FROM promotores")
        st.metric("👩‍💼 Promotores", total_promotores[0]['total'] if total_promotores else 0)
    
    # Grupos recientes
    st.subheader("🎯 Grupos Recientes")
    grupos_recientes = ejecutar_consulta("""
        SELECT nombre_grupo, fecha_creacion, lugar_reunion 
        FROM grupos 
        ORDER BY fecha_creacion DESC 
        LIMIT 5
    """)
    
    if grupos_recientes:
        for grupo in grupos_recientes:
            st.write(f"• **{grupo['nombre_grupo']}** - Creado: {grupo['fecha_creacion'].strftime('%d/%m/%Y')}")
    else:
        st.info("ℹ️ No hay grupos registrados")
    
    # Información sobre datos financieros
    st.subheader("💡 Información del Sistema")
    st.info("""
    **Estado de los módulos:**
    - ✅ Grupos, Socios y Distritos funcionando
    - 📊 Datos financieros disponibles cuando se registren reuniones
    - 🔄 Los saldos se calcularán automáticamente
    """)

def mostrar_dashboard_directiva():
    """Dashboard para directiva de grupo"""
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ No tiene un grupo asignado")
        return
    
    # Métricas básicas del grupo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_socios = obtener_metricas(
            "SELECT COUNT(*) as total FROM socios WHERE id_grupo = %s",
            (st.session_state.id_grupo,)
        )
        st.metric("👥 Socios del Grupo", total_socios[0]['total'] if total_socios else 0)
    
    with col2:
        # Contar reuniones realizadas
        reuniones_realizadas = obtener_metricas(
            "SELECT COUNT(*) as total FROM sesion WHERE id_grupo = %s",
            (st.session_state.id_grupo,)
        )
        st.metric("📅 Reuniones Realizadas", reuniones_realizadas[0]['total'] if reuniones_realizadas else 0)
    
    with col3:
        # Contar préstamos si existen
        try:
            prestamos_totales = obtener_metricas(
                "SELECT COUNT(*) as total FROM prestamo WHERE id_socio IN (SELECT id_socio FROM socios WHERE id_grupo = %s)",
                (st.session_state.id_grupo,)
            )
            st.metric("🏦 Préstamos Totales", prestamos_totales[0]['total'] if prestamos_totales else 0)
        except:
            st.metric("🏦 Préstamos Totales", 0)
    
    # Información financiera del grupo
    st.subheader("💰 Estado Financiero del Grupo")
    
    # Intentar obtener información de ahorros si existe
    try:
        # Último registro de ahorro del grupo
        ultimo_ahorro = obtener_metricas("""
            SELECT a.saldo_cierre 
            FROM ahorro a 
            JOIN sesion s ON a.id_sesion = s.id_sesion 
            WHERE s.id_grupo = %s 
            ORDER BY a.id_ahorro DESC 
            LIMIT 1
        """, (st.session_state.id_grupo,))
        
        if ultimo_ahorro and ultimo_ahorro[0]['saldo_cierre']:
            st.metric("💵 Ahorro del Grupo", f"${ultimo_ahorro[0]['saldo_cierre']:,.2f}")
        else:
            st.metric("💵 Ahorro del Grupo", "$0.00")
    except:
        st.metric("💵 Ahorro del Grupo", "$0.00")
    
    # Intentar obtener información de caja si existe
    try:
        # Último registro de caja del grupo
        ultima_caja = obtener_metricas("""
            SELECT saldo_cierre 
            FROM caja c 
            JOIN sesion s ON c.id_sesion = s.id_sesion 
            WHERE s.id_grupo = %s 
            ORDER BY c.id_caja DESC 
            LIMIT 1
        """, (st.session_state.id_grupo,))
        
        if ultima_caja and ultima_caja[0]['saldo_cierre']:
            st.metric("💳 Caja del Grupo", f"${ultima_caja[0]['saldo_cierre']:,.2f}")
        else:
            st.metric("💳 Caja del Grupo", "$0.00")
    except:
        st.metric("💳 Caja del Grupo", "$0.00")
    
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
    """Dashboard para promotoras - Versión mejorada"""
    
    # Obtener ID de la promotora
    id_promotora = obtener_id_promotora()
    if not id_promotora:
        st.error("❌ No se pudo identificar a la promotora")
        return
    
    # Métricas generales
    st.subheader("📈 Mis Métricas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        grupos_asignados = obtener_metricas(
            "SELECT COUNT(*) as total FROM grupos WHERE id_promotor = %s AND estado = 'ACTIVO'",
            (id_promotora,)
        )
        st.metric("🏢 Grupos Activos", grupos_asignados[0]['total'] if grupos_asignados else 0)
    
    with col2:
        total_socios = obtener_metricas(
            "SELECT COUNT(*) as total FROM socios s JOIN grupos g ON s.id_grupo = g.id_grupo WHERE g.id_promotor = %s AND s.estado = 'ACTIVO'",
            (id_promotora,)
        )
        st.metric("👥 Total Socios", total_socios[0]['total'] if total_socios else 0)
    
    with col3:
        reuniones_pendientes = obtener_metricas(
            """SELECT COUNT(*) as total FROM grupos 
               WHERE id_promotor = %s AND estado = 'ACTIVO' 
               AND id_grupo NOT IN (
                   SELECT DISTINCT id_grupo FROM sesion 
                   WHERE fecha_sesion >= %s
               )""",
            (id_promotora, datetime.now().date() - timedelta(days=7))
        )
        st.metric("📅 Reuniones Pendientes", reuniones_pendientes[0]['total'] if reuniones_pendientes else 0)
        
    # Grupos recientemente activos
    st.subheader("🎯 Mis Grupos")
    
    grupos = obtener_metricas(
        """SELECT g.id_grupo, g.nombre_grupo, g.estado, 
                  COUNT(s.id_socio) as socios_activos
           FROM grupos g 
           LEFT JOIN socios s ON g.id_grupo = s.id_grupo AND s.estado = 'ACTIVO'
           WHERE g.id_promotor = %s
           GROUP BY g.id_grupo, g.nombre_grupo, g.estado
           ORDER BY g.fecha_creacion DESC 
           LIMIT 5""",
        (id_promotora,)
    )
    
    if grupos:
        for grupo in grupos:
            estado_color = "🟢" if grupo['estado'] == 'ACTIVO' else "🔴"
            st.write(f"{estado_color} **{grupo['nombre_grupo']}** - {grupo['socios_activos']} socios")
    else:
        st.info("ℹ️ No tienes grupos asignados")

def obtener_id_promotora():
    """Obtener ID de promotora desde la sesión o BD"""
    if 'id_promotora' in st.session_state:
        return st.session_state.id_promotora
    
    try:
        resultado = obtener_metricas(
            "SELECT id_promotor FROM promotores WHERE nombre = %s OR id_promotor IN (SELECT id_promotor FROM usuarios WHERE username = %s)",
            (st.session_state.usuario, st.session_state.usuario)
        )
        if resultado:
            st.session_state.id_promotora = resultado[0]['id_promotor']
            return st.session_state.id_promotora
    except:
        pass
    
    return None

def obtener_metricas(query, params=None):
    """Obtener métricas desde la base de datos"""
    try:
        resultado = ejecutar_consulta(query, params)
        return resultado
    except Exception as e:
        # No mostrar el error en el dashboard para no confundir al usuario
        # Solo retornar None para que se muestre 0 o valor por defecto
        return None

def obtener_proxima_reunion(id_grupo):
    """Obtener información de reuniones del grupo"""
    try:
        # Obtener la configuración de reuniones del grupo
        grupo_config = ejecutar_consulta(
            "SELECT dia_reunion, hora_reunion FROM grupos WHERE id_grupo = %s",
            (id_grupo,)
        )
        
        if grupo_config and grupo_config[0]['dia_reunion'] and grupo_config[0]['hora_reunion']:
            return f"{grupo_config[0]['dia_reunion']} {grupo_config[0]['hora_reunion']}"
        return "No programada"
    except Exception:
        return "No programada"