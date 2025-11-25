import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando

def modulo_gestion_promotores():
    """Módulo para gestión de promotores (para administradores)"""
    
    st.header("👩‍💼 Gestión de Promotores")
    
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Promotores", "➕ Nuevo Promotor", "📊 Asignación Grupos"])
    
    with tab1:
        listar_promotores()
    
    with tab2:
        crear_promotor()
    
    with tab3:
        asignacion_grupos()

def listar_promotores():
    """Listar todos los promotores"""
    
    st.subheader("📋 Lista de Promotores")
    
    promotores = obtener_promotores_completos()
    
    if promotores:
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Promotores", len(promotores))
        
        with col2:
            activos = sum(1 for p in promotores if p['activo'])
            st.metric("Promotores Activos", activos)
        
        with col3:
            grupos_por_promotor = sum(p['total_grupos'] for p in promotores) / len(promotores)
            st.metric("Promedio Grupos", f"{grupos_por_promotor:.1f}")
        
        # Tabla de promotores
        st.markdown("### Detalle de Promotores")
        
        for promotor in promotores:
            with st.expander(f"👤 {promotor['nombre_completo']} - {promotor['total_grupos']} grupos"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Teléfono:** {promotor['tele']}")
                    st.write(f"**Dirección:** {promotor['direccion']}")
                    st.write(f"**Distrito:** {promotor['nombre_distrito']}")
                
                with col2:
                    st.write(f"**Grupos asignados:** {promotor['total_grupos']}")
                    st.write(f"**Estado:** {'🟢 Activo' if promotor['activo'] else '🔴 Inactivo'}")
                
                with col3:
                    # Botones de acción
                    if st.button("✏️ Editar", key=f"editar_{promotor['id_promotor']}"):
                        editar_promotor(promotor['id_promotor'])
                    
                    if st.button("👁️ Ver Grupos", key=f"grupos_{promotor['id_promotor']}"):
                        ver_grupos_promotor(promotor['id_promotor'])
    else:
        st.info("ℹ️ No hay promotores registrados")

def crear_promotor():
    """Formulario para crear nuevo promotor"""
    
    st.subheader("➕ Registrar Nuevo Promotor")
    
    with st.form("form_nuevo_promotor"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("👤 Nombre", placeholder="Ej: María")
            apellido = st.text_input("👤 Apellido", placeholder="Ej: García")
            telefono = st.text_input("📞 Teléfono", placeholder="Ej: 9999-9999")
        
        with col2:
            direccion = st.text_input("🏠 Dirección", placeholder="Ej: Colonia Los Pinos")
            id_distrito = st.selectbox("🗺️ Distrito", obtener_distritos())
            activo = st.checkbox("✅ Activo", value=True)
        
        submitted = st.form_submit_button("💾 Registrar Promotor")
        
        if submitted:
            if validar_promotor(nombre, apellido, telefono):
                id_promotor = guardar_promotor(nombre, apellido, telefono, direccion, id_distrito, activo)
                if id_promotor:
                    st.success(f"✅ Promotor '{nombre} {apellido}' registrado exitosamente")
                    st.rerun()
            else:
                st.error("❌ Complete los campos obligatorios")

def validar_promotor(nombre, apellido, telefono):
    """Validar datos del promotor"""
    if not nombre.strip():
        return False
    if not apellido.strip():
        return False
    if not telefono.strip():
        return False
    return True

def guardar_promotor(nombre, apellido, telefono, direccion, id_distrito, activo):
    """Guardar promotor en la base de datos"""
    
    # Obtener próximo ID disponible
    proximo_id = obtener_proximo_id_promotor()
    
    query = """
        INSERT INTO promotores (id_promotor, nombre, apellido, tele, direccion, id_distrito, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (
        proximo_id,
        str(nombre),
        str(apellido),
        str(telefono),
        str(direccion),
        int(id_distrito),
        int(activo)
    )
    
    return ejecutar_comando(query, params)

def asignacion_grupos():
    """Asignación de grupos a promotores"""
    
    st.subheader("📊 Asignación de Grupos a Promotores")
    
    # Obtener grupos sin promotor asignado
    grupos_sin_promotor = obtener_grupos_sin_promotor()
    
    if grupos_sin_promotor:
        st.info(f"ℹ️ Hay {len(grupos_sin_promotor)} grupos sin promotor asignado")
        
        for grupo in grupos_sin_promotor:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.write(f"**{grupo['nombre_grupo']}**")
                    st.write(f"Distrito: {grupo['nombre_distrito']}")
                
                with col2:
                    promotores = obtener_promotores_activos()
                    promotor_seleccionado = st.selectbox(
                        "Asignar promotor:",
                        promotores,
                        key=f"promotor_{grupo['id_grupo']}"
                    )
                
                with col3:
                    if st.button("💾 Asignar", key=f"asignar_{grupo['id_grupo']}"):
                        if asignar_promotor_grupo(grupo['id_grupo'], promotor_seleccionado[0]):
                            st.success("✅ Promotor asignado exitosamente")
                            st.rerun()
    else:
        st.success("🎉 Todos los grupos tienen promotor asignado")

# =============================================================================
# FUNCIONES AUXILIARES - PROMOTORES
# =============================================================================

def obtener_promotores_completos():
    """Obtener información completa de promotores"""
    query = """
        SELECT 
            p.id_promotor,
            CONCAT(p.nombre, ' ', p.apellido) as nombre_completo,
            p.tele,
            p.direccion,
            p.activo,
            d.nombre_distrito,
            COUNT(g.id_grupo) as total_grupos
        FROM promotores p
        LEFT JOIN distrito d ON p.id_distrito = d.id_distrito
        LEFT JOIN grupos g ON p.id_promotor = g.id_promotor
        GROUP BY p.id_promotor
        ORDER BY p.nombre, p.apellido
    """
    return ejecutar_consulta(query)

def obtener_distritos():
    """Obtener lista de distritos"""
    resultado = ejecutar_consulta("SELECT id_distrito, nombre_distrito FROM distrito")
    if resultado:
        return [(row['id_distrito'], row['nombre_distrito']) for row in resultado]
    return []

def obtener_proximo_id_promotor():
    """Obtener próximo ID disponible para promotor"""
    resultado = ejecutar_consulta("SELECT COALESCE(MAX(id_promotor), 0) + 1 as proximo_id FROM promotores")
    return resultado[0]['proximo_id'] if resultado else 1

def obtener_grupos_sin_promotor():
    """Obtener grupos sin promotor asignado"""
    query = """
        SELECT 
            g.id_grupo,
            g.nombre_grupo,
            d.nombre_distrito
        FROM grupos g
        JOIN distrito d ON g.id_distrito = d.id_distrito
        WHERE g.id_promotor IS NULL OR g.id_promotor = 0
    """
    return ejecutar_consulta(query)

def obtener_promotores_activos():
    """Obtener promotores activos"""
    resultado = ejecutar_consulta("""
        SELECT id_promotor, CONCAT(nombre, ' ', apellido) as nombre 
        FROM promotores 
        WHERE activo = 1
    """)
    if resultado:
        return [(row['id_promotor'], row['nombre']) for row in resultado]
    return []

def asignar_promotor_grupo(id_grupo, id_promotor):
    """Asignar promotor a un grupo"""
    query = "UPDATE grupos SET id_promotor = %s WHERE id_grupo = %s"
    return ejecutar_comando(query, (id_promotor, id_grupo))

def editar_promotor(id_promotor):
    """Editar información de promotor"""
    st.info(f"🔧 Funcionalidad en desarrollo - Editar promotor #{id_promotor}")

def ver_grupos_promotor(id_promotor):
    """Ver grupos asignados a un promotor"""
    st.info(f"🔧 Funcionalidad en desarrollo - Grupos del promotor #{id_promotor}")