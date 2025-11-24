import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime

def modulo_afiliacion_socios():
    """Módulo principal para la gestión de socios"""
    
    st.header("👥 Gestión de Socios")
    
    tab1, tab2 = st.tabs(["➕ Registrar Socio", "📋 Lista de Socios"])
    
    with tab1:
        registrar_socio()
    
    with tab2:
        listar_socios()

def registrar_socio():
    """Formulario para registrar nuevo socio"""
    
    st.subheader("Registrar Nuevo Socio")
    
    with st.form("form_nuevo_socio"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("👤 Nombre", placeholder="Ej: María")
            apellido = st.text_input("👤 Apellido", placeholder="Ej: García")
            telefono = st.text_input("📞 Teléfono", placeholder="Ej: 9999-9999")
        
        with col2:
            direccion = st.text_input("🏠 Dirección", placeholder="Ej: Colonia Los Pinos, Calle Principal")
            id_grupo = st.selectbox("🏢 Grupo", obtener_grupos_con_nombres())
            id_distrito = st.selectbox("🗺️ Distrito", obtener_distritos())
        
        submitted = st.form_submit_button("💾 Registrar Socio")
        
        if submitted:
            if validar_socio(nombre, apellido, telefono):
                id_socio = crear_socio(nombre, apellido, telefono, direccion, id_grupo, id_distrito)
                if id_socio:
                    st.success(f"✅ Socio '{nombre} {apellido}' registrado exitosamente")
                    
                    # Opción para crear usuario de acceso
                    if st.checkbox("🎯 Crear usuario de acceso para este socio"):
                        crear_usuario_socio(id_socio, nombre, apellido)

def validar_socio(nombre, apellido, telefono):
    """Validar datos del socio"""
    if not nombre.strip():
        st.error("❌ El nombre es obligatorio")
        return False
    if not apellido.strip():
        st.error("❌ El apellido es obligatorio")
        return False
    if not telefono.strip():
        st.error("❌ El teléfono es obligatorio")
        return False
    return True

def crear_socio(nombre, apellido, telefono, direccion, id_grupo, id_distrito):
    """Crear nuevo socio en la base de datos"""
    
    query = """
        INSERT INTO socios (nombre, apellido, telefono, direccion, id_grupo, id_distrito)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    params = (nombre, apellido, telefono, direccion, id_grupo, id_distrito)
    
    return ejecutar_comando(query, params)

def crear_usuario_socio(id_socio, nombre, apellido):
    """Crear usuario de acceso para el socio"""
    
    with st.form("form_usuario_socio"):
        username = st.text_input("👤 Nombre de usuario", 
                               value=f"{nombre.lower()}.{apellido.lower()}")
        password = st.text_input("🔒 Contraseña temporal", type="password", value="temp123")
        rol = st.selectbox("🎯 Rol", ["DIRECTIVA", "SOCIO"], disabled=True, 
                          help="Los socios regulares tienen rol SOCIO")
        
        if st.form_submit_button("👤 Crear Usuario"):
            # En una implementación real, aquí se hashearía la contraseña
            query = """
                INSERT INTO usuarios (username, passwordhash, rol_sistema, id_socio, activo)
                VALUES (%s, %s, 'DIRECTIVA', %s, 1)
            """
            
            if ejecutar_comando(query, (username, password, id_socio)):
                st.success(f"✅ Usuario '{username}' creado exitosamente")
            else:
                st.error("❌ Error creando el usuario")

def listar_socios():
    """Mostrar lista de socios existentes"""
    
    st.subheader("Socios Registrados")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_grupo = st.selectbox("Filtrar por Grupo", 
                                  ["Todos"] + [grupo[1] for grupo in obtener_grupos_con_nombres()])
    
    # Obtener socios
    if filtro_grupo == "Todos":
        socios = ejecutar_consulta("""
            SELECT s.*, g.nombre_grupo, d.nombre_distrito
            FROM socios s
            JOIN grupos g ON s.id_grupo = g.id_grupo
            JOIN distrito d ON s.id_distrito = d.id_distrito
            ORDER BY g.nombre_grupo, s.apellido, s.nombre
        """)
    else:
        socios = ejecutar_consulta("""
            SELECT s.*, g.nombre_grupo, d.nombre_distrito
            FROM socios s
            JOIN grupos g ON s.id_grupo = g.id_grupo
            JOIN distrito d ON s.id_distrito = d.id_distrito
            WHERE g.nombre_grupo = %s
            ORDER BY s.apellido, s.nombre
        """, (filtro_grupo,))
    
    if socios:
        # Mostrar estadísticas
        total_socios = len(socios)
        st.metric("📊 Total de Socios", total_socios)
        
        # Tabla de socios
        st.markdown("### Lista de Socios")
        
        for socio in socios:
            with st.expander(f"👤 {socio['nombre']} {socio['apellido']} - {socio['nombre_grupo']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**📞 Teléfono:** {socio['telefono']}")
                    st.write(f"**🏠 Dirección:** {socio['direccion']}")
                
                with col2:
                    st.write(f"**🏢 Grupo:** {socio['nombre_grupo']}")
                    st.write(f"**🗺️ Distrito:** {socio['nombre_distrito']}")
                
                with col3:
                    # Acciones
                    if st.button("✏️ Editar", key=f"editar_{socio['id_socio']}"):
                        st.info("Funcionalidad de edición en desarrollo")
                    
                    if st.button("👁️ Ver Detalles", key=f"detalles_{socio['id_socio']}"):
                        st.info("Funcionalidad de detalles en desarrollo")
    else:
        st.info("ℹ️ No hay socios registrados")

# =============================================================================
# FUNCIONES AUXILIARES (reutilizables)
# =============================================================================

def obtener_grupos_con_nombres():
    """Obtener grupos con formato para selectbox"""
    resultado = ejecutar_consulta("SELECT id_grupo, nombre_grupo FROM grupos")
    if resultado:
        return [(row['id_grupo'], row['nombre_grupo']) for row in resultado]
    return []

def obtener_distritos():
    """Obtener lista de distritos"""
    resultado = ejecutar_consulta("SELECT id_distrito, nombre_distrito FROM distrito")
    if resultado:
        return [(row['id_distrito'], row['nombre_distrito']) for row in resultado]
    return []