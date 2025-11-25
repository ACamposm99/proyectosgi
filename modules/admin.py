import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime

def modulo_gestion_promotores():
    """Módulo para gestión de promotores (solo ADMIN)"""
    
    st.header("👩‍💼 Gestión de Promotores")
    
    if st.session_state.rol != "ADMIN":
        st.warning("⚠️ Solo los administradores pueden gestionar promotores")
        return
    
    tab1, tab2 = st.tabs(["➕ Nuevo Promotor", "📋 Lista de Promotores"])
    
    with tab1:
        crear_promotor()
    
    with tab2:
        listar_promotores()

def crear_promotor():
    """Formulario para crear nuevo promotor"""
    
    st.subheader("Crear Nuevo Promotor")
    
    with st.form("form_nuevo_promotor"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre", placeholder="Ej: Ana")
            apellido = st.text_input("Apellido", placeholder="Ej: García")
            telefono = st.text_input("Teléfono", placeholder="Ej: 9999-9999")
        
        with col2:
            direccion = st.text_input("Dirección", placeholder="Ej: Colonia Los Pinos")
            id_distrito = st.selectbox("Distrito", obtener_distritos())
            activo = st.checkbox("Activo", value=True)
        
        submitted = st.form_submit_button("💾 Guardar Promotor")
        
        if submitted:
            if validar_promotor(nombre, apellido, telefono):
                # Extraer solo el ID (no la tupla completa)
                id_distrito_val = id_distrito[0] if isinstance(id_distrito, tuple) else id_distrito
                
                id_promotor = guardar_promotor(nombre, apellido, telefono, direccion, id_distrito_val, activo)
                if id_promotor:
                    st.success(f"✅ Promotor '{nombre} {apellido}' creado exitosamente")
                else:
                    st.error("❌ Error al crear el promotor")

def validar_promotor(nombre, apellido, telefono):
    """Validar datos del promotor"""
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

def guardar_promotor(nombre, apellido, telefono, direccion, id_distrito, activo):
    """Guardar promotor en la base de datos"""
    
    query = """
        INSERT INTO promotores (nombre, apellido, tele, direccion, id_distrito, activo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    # Asegurar que todos los parámetros tengan el tipo correcto
    params = (
        str(nombre),
        str(apellido), 
        str(telefono),
        str(direccion),
        int(id_distrito),
        bool(activo)
    )
    
    try:
        return ejecutar_comando(query, params)
    except Exception as e:
        st.error(f"❌ Error al guardar promotor: {e}")
        return None

def listar_promotores():
    """Mostrar lista de promotores existentes"""
    
    st.subheader("Promotores Registrados")
    
    promotores = obtener_promotores()
    
    if promotores:
        st.metric("📊 Total de Promotores", len(promotores))
        
        for promotor in promotores:
            with st.expander(f"👤 {promotor['nombre']} {promotor['apellido']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**📞 Teléfono:** {promotor['tele']}")
                    st.write(f"**🏠 Dirección:** {promotor['direccion']}")
                
                with col2:
                    st.write(f"**🗺️ Distrito:** {promotor['nombre_distrito']}")
                    st.write(f"**📊 Estado:** {'✅ Activo' if promotor['activo'] else '❌ Inactivo'}")
                
                with col3:
                    # Acciones
                    if st.button("✏️ Editar", key=f"editar_{promotor['id_promotor']}"):
                        editar_promotor(promotor['id_promotor'])
                    
                    if st.button("🗑️ Eliminar", key=f"eliminar_{promotor['id_promotor']}"):
                        eliminar_promotor(promotor['id_promotor'])
    else:
        st.info("ℹ️ No hay promotores registrados")

def obtener_promotores():
    """Obtener lista de todos los promotores"""
    query = """
        SELECT p.*, d.nombre_distrito 
        FROM promotores p
        LEFT JOIN distrito d ON p.id_distrito = d.id_distrito
        ORDER BY p.nombre, p.apellido
    """
    return ejecutar_consulta(query)

def obtener_distritos():
    """Obtener lista de distritos"""
    resultado = ejecutar_consulta("SELECT id_distrito, nombre_distrito FROM distrito")
    if resultado:
        return [(row['id_distrito'], row['nombre_distrito']) for row in resultado]
    return []

def editar_promotor(id_promotor):
    """Editar promotor existente"""
    st.info(f"🔧 Funcionalidad en desarrollo - Editar promotor #{id_promotor}")

def eliminar_promotor(id_promotor):
    """Eliminar promotor (lógico)"""
    st.info(f"🔧 Funcionalidad en desarrollo - Eliminar promotor #{id_promotor}")

def modulo_gestion_distritos():
    """Módulo para gestión de distritos (solo ADMIN)"""
    
    st.header("🗺️ Gestión de Distritos")
    
    if st.session_state.rol != "ADMIN":
        st.warning("⚠️ Solo los administradores pueden gestionar distritos")
        return
    
    tab1, tab2 = st.tabs(["➕ Nuevo Distrito", "📋 Lista de Distritos"])
    
    with tab1:
        crear_distrito()
    
    with tab2:
        listar_distritos()

def crear_distrito():
    """Formulario para crear nuevo distrito"""
    
    st.subheader("Crear Nuevo Distrito")
    
    with st.form("form_nuevo_distrito"):
        nombre_distrito = st.text_input("Nombre del Distrito", placeholder="Ej: Distrito Este")
        municipio = st.text_input("Municipio", placeholder="Ej: Comayagüela")
        
        submitted = st.form_submit_button("💾 Guardar Distrito")
        
        if submitted:
            if nombre_distrito and municipio:
                if guardar_distrito(nombre_distrito, municipio):
                    st.success("✅ Distrito creado exitosamente")
                    st.rerun()
            else:
                st.error("❌ Complete todos los campos")

def guardar_distrito(nombre, municipio):
    """Guardar distrito en la base de datos"""
    query = "INSERT INTO distrito (nombre_distrito, municipio) VALUES (%s, %s)"
    params = (str(nombre), str(municipio))
    return ejecutar_comando(query, params)

def listar_distritos():
    """Mostrar lista de distritos existentes"""
    
    st.subheader("Distritos Registrados")
    
    distritos = obtener_todos_distritos()
    
    if distritos:
        st.metric("📊 Total de Distritos", len(distritos))
        
        for distrito in distritos:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{distrito['nombre_distrito']}**")
            with col2:
                st.write(f"Municipio: {distrito['municipio']}")
            with col3:
                if st.button("🗑️", key=f"eliminar_distrito_{distrito['id_distrito']}"):
                    st.warning("Funcionalidad en desarrollo")
    else:
        st.info("ℹ️ No hay distritos registrados")

def obtener_todos_distritos():
    """Obtener todos los distritos"""
    return ejecutar_consulta("SELECT * FROM distrito ORDER BY nombre_distrito")