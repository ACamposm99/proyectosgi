import streamlit as st
from modules.auth import autenticar_usuario, mostrar_login
from modules.database import inicializar_bd
from modules.grupos import modulo_conformacion_grupo
from modules.socios import modulo_afiliacion_socios
from modules.reuniones import modulo_reuniones
from modules.ahorros import modulo_ahorros
from modules.caja import modulo_caja
from modules.prestamos import modulo_prestamos
from modules.pagos import modulo_pagos
from modules.cierre_ciclo import modulo_cierre_ciclo
from modules.reportes import modulo_reportes
from modules.actas import modulo_actas
from utils.helpers import mostrar_dashboard_principal
from modules.admin import modulo_gestion_promotores, modulo_gestion_distritos, modulo_gestion_directiva  # NUEVA IMPORTACIÓN

def main():
    # Configuración de la página
    st.set_page_config(
        page_title="Sistema GAPC - Grupos de Ahorro y Préstamo",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inicializar base de datos
    inicializar_bd()
    
    # Sistema de autenticación
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.session_state.usuario = None
        st.session_state.id_grupo = None
    
    # Mostrar login o aplicación principal
    if not st.session_state.autenticado:
        mostrar_login()
    else:
        mostrar_aplicacion_principal()

def mostrar_aplicacion_principal():
    """Aplicación principal después del login"""
    
    # Sidebar con información del usuario
    st.sidebar.title(f"🏦 Sistema GAPC")
    st.sidebar.write(f"👤 Usuario: {st.session_state.usuario}")
    st.sidebar.write(f"🎯 Rol: {st.session_state.rol}")
    
    if st.session_state.id_grupo:
        st.sidebar.write(f"👥 Grupo: {st.session_state.nombre_grupo}")
    
    st.sidebar.markdown("---")
    
    # Menú de navegación según el rol
    if st.session_state.rol == "DIRECTIVA":
        menu_options = [
            "📊 Dashboard", 
            "🏢 Conformación del Grupo", 
            "👥 Gestión de Socios",
            "📅 Reuniones y Asistencia",
            "💰 Aportes de Ahorro",
            "💳 Gestión de Caja",
            "🏦 Solicitud de Préstamos",
            "💵 Registro de Pagos",
            "🔚 Cierre de Ciclo",
            "📈 Reportes Ejecutivos",
            "📄 Actas y Documentos",
            "⚙️ Configuración"
        ]
    elif st.session_state.rol == "PROMOTORA":
        menu_options = [
            "📊 Dashboard", 
            "👁️ Supervisión Grupos", 
            "📋 Validaciones",
            "📈 Reportes Distrito",
            "📊 Consolidados"
        ]
    else:  # ADMIN
        menu_options = [
            "📊 Dashboard", 
            "🏢 Conformación de Grupos", 
            "👥 Gestión de Socios",
            "🌐 Gestión de Distritos",
            "👤 Gestión de Promotores",
            "👨‍💼 Gestión de Directiva",  # NUEVA OPCIÓN
            "📊 Reportes Generales",
            "📈 Analytics",
            "⚙️ Configuración del Sistema"
        ]
    
    seleccion = st.sidebar.selectbox("Navegación", menu_options)
    
    # Logout button
    if st.sidebar.button("🚪 Cerrar Sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Routing según selección
    if seleccion == "📊 Dashboard":
        mostrar_dashboard_principal()
    elif "Conformación" in seleccion:
        modulo_conformacion_grupo()
    elif "Socios" in seleccion:
        modulo_afiliacion_socios()
    elif seleccion == "📅 Reuniones y Asistencia":
        modulo_reuniones()
    elif seleccion == "💰 Aportes de Ahorro":
        modulo_ahorros()
    elif seleccion == "💳 Gestión de Caja":
        modulo_caja()
    elif seleccion == "🏦 Solicitud de Préstamos":
        modulo_prestamos()
    elif seleccion == "💵 Registro de Pagos":
        modulo_pagos()
    elif seleccion == "👤 Gestión de Promotores":
        modulo_gestion_promotores()
    elif seleccion == "🌐 Gestión de Distritos":
        modulo_gestion_distritos()
    elif seleccion == "👨‍💼 Gestión de Directiva":  # NUEVO ROUTING
        modulo_gestion_directiva()
    elif seleccion == "🔚 Cierre de Ciclo":
        modulo_cierre_ciclo()
    elif "Reportes" in seleccion or "Analytics" in seleccion or "Consolidados" in seleccion:
        modulo_reportes()
    elif "Actas" in seleccion:
        modulo_actas()
    elif "Configuración" in seleccion:
        st.info("Módulo de configuración - En desarrollo")

if __name__ == "__main__":
    main()