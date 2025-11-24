import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando

def modulo_configuracion():
    """Módulo de configuración del sistema"""
    
    st.header("⚙️ Configuración del Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🌐 Distritos", "👩‍💼 Promotores", "🔧 Sistema"])
    
    with tab1:
        gestion_distritos()
    
    with tab2:
        gestion_promotores()
    
    with tab3:
        configuracion_sistema()

def gestion_distritos():
    """Gestión de distritos"""
    st.subheader("Gestión de Distritos")
    
    # Formulario para nuevo distrito
    with st.form("form_distrito"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_distrito = st.text_input("Nombre del Distrito")
        with col2:
            municipio = st.text_input("Municipio")
        
        if st.form_submit_button("➕ Agregar Distrito"):
            if nombre_distrito and municipio:
                if crear_distrito(nombre_distrito, municipio):
                    st.success("✅ Distrito agregado exitosamente")
                    st.rerun()
            else:
                st.error("❌ Complete todos los campos")
    
    # Lista de distritos existentes
    st.markdown("### Distritos Registrados")
    distritos = ejecutar_consulta("SELECT * FROM distrito ORDER BY nombre_distrito")
    
    if distritos:
        for distrito in distritos:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{distrito['nombre_distrito']}**")
            with col2:
                st.write(f"Municipio: {distrito['municipio']}")
            with col3:
                if st.button("🗑️", key=f"eliminar_{distrito['id_distrito']}"):
                    st.warning("Funcionalidad en desarrollo")

def gestion_promotores():
    """Gestión de promotores"""
    st.subheader("Gestión de Promotores")
    st.info("🔧 Módulo en desarrollo - Próximamente")

def configuracion_sistema():
    """Configuración general del sistema"""
    st.subheader("Configuración General")
    st.info("🔧 Módulo en desarrollo - Próximamente")

def crear_distrito(nombre, municipio):
    """Crear nuevo distrito"""
    query = "INSERT INTO distrito (nombre_distrito, municipio) VALUES (%s, %s)"
    return ejecutar_comando(query, (nombre, municipio))