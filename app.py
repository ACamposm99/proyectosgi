import streamlit as st
from modules.auth import autenticar_usuario, mostrar_login
from modules.database import inicializar_bd
from modules.grupos import modulo_conformacion_grupo
from modules.socios import modulo_afiliacion_socios
from utils.helpers import mostrar_dashboard_principal

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
        st.session_state.id_grupo = None  # Para directiva
    
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
            "⚙️ Configuración"
        ]
    elif st.session_state.rol == "PROMOTORA":
        menu_options = [
            "📊 Dashboard", 
            "👁️ Supervisión Grupos", 
            "📋 Validaciones",
            "📈 Reportes Distrito"
        ]
    else:  # ADMIN
        menu_options = [
            "📊 Dashboard", 
            "🏢 Conformación de Grupos", 
            "👥 Gestión de Socios",
            "🌐 Gestión de Distritos",
            "👤 Gestión de Promotores",
            "⚙️ Configuración del Sistema"
        ]
    
    seleccion = st.sidebar.selectbox("Navegación", menu_options)
    
    # Logout button
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.session_state.usuario = None
        st.rerun()
    
    # Routing según selección
    if seleccion == "📊 Dashboard":
        mostrar_dashboard_principal()
    elif "Conformación" in seleccion:
        modulo_conformacion_grupo()
    elif "Socios" in seleccion:
        modulo_afiliacion_socios()
    elif "Configuración" in seleccion:
        st.info("Módulo de configuración - En desarrollo")

if __name__ == "__main__":
    main()