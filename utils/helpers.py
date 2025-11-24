import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime

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
        st.metric("🏢 Grupos Activos", total_grupos[0]['total'] if total_grupos else 0)
    
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

def mostrar_dashboard_directiva():
    """Dashboard para directiva de grupo"""
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ No tiene un grupo asignado")
        return
    
    # Métricas del grupo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_socios = obtener_metricas(
            "SELECT COUNT(*) as total FROM socios WHERE id_grupo = %s",
            (st.session_state.id_grupo,)
        )
        st.metric("👥 Socios en Grupo", total_socios[0]['total'] if total_socios else 0)
    
    with col2:
        proxima_reunion = obtener_proxima_reunion(st.session_state.id_grupo)
        st.metric("📅 Próxima Reunión", 
                 proxima_reunion.strftime('%d/%m') if proxima_reunion else "No programada")
    
    with col3:
        ahorro_total = obtener_metricas(
            "SELECT COALESCE(SUM(saldo_cierre), 0) as total FROM ahorro WHERE id_sesion IN (SELECT id_sesion FROM sesion WHERE id_grupo = %s)",
            (st.session_state.id_grupo,)
        )
        st.metric("💰 Ahorro Total", f"${ahorro_total[0]['total']:,.2f}" if ahorro_total else "$0.00")
    
    # Acciones rápidas
    st.subheader("🚀 Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Registrar Nueva Reunión", use_container_width=True):
            st.info("🔧 Funcionalidad en desarrollo")
    
    with col2:
        if st.button("👥 Gestionar Socios", use_container_width=True):
            st.switch_page("pages/2_👥_Gestión_de_Socios.py")
    
    with col3:
        if st.button("💰 Registrar Aportes", use_container_width=True):
            st.info("🔧 Funcionalidad en desarrollo")

def mostrar_dashboard_promotora():
    """Dashboard para promotoras"""
    st.info("👷 Dashboard para promotoras - En desarrollo")

def obtener_metricas(query, params=None):
    """Obtener métricas desde la base de datos"""
    try:
        return ejecutar_consulta(query, params)
    except Exception:
        return None

def obtener_proxima_reunion(id_grupo):
    """Obtener la próxima reunión programada para el grupo"""
    # Esta es una implementación simplificada
    # En una versión real, se calcularía basado en la frecuencia
    return datetime.now()