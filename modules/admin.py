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
        
        # Opción para crear usuario
        crear_usuario = st.checkbox("🔐 Crear usuario de acceso para este promotor", value=True)
        
        submitted = st.form_submit_button("💾 Guardar Promotor")
        
        if submitted:
            if validar_promotor(nombre, apellido, telefono):
                # Extraer solo el ID (no la tupla completa)
                id_distrito_val = id_distrito[0] if isinstance(id_distrito, tuple) else id_distrito
                
                id_promotor = guardar_promotor(nombre, apellido, telefono, direccion, id_distrito_val, activo)
                if id_promotor:
                    st.success(f"✅ Promotor '{nombre} {apellido}' creado exitosamente")
                    
                    # Crear usuario si está marcado
                    if crear_usuario:
                        crear_usuario_promotor(id_promotor, nombre, apellido)
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

def crear_usuario_promotor(id_promotor, nombre, apellido):
    """Crear usuario de acceso para el promotor"""
    
    # Convertir id_promotor a entero si es necesario
    try:
        id_promotor = int(id_promotor)
    except (ValueError, TypeError):
        st.error("❌ ID de promotor inválido")
        return False
    
    with st.form("form_usuario_promotor"):
        st.markdown("### 🔐 Crear Usuario de Acceso")
        
        username = st.text_input("👤 Nombre de usuario", 
                               value=f"{nombre.lower()}.{apellido.lower()}",
                               help="Nombre de usuario para que el promotor acceda al sistema")
        
        password = st.text_input("🔒 Contraseña temporal", type="password", value="temp123",
                               help="Contraseña temporal que el promotor deberá cambiar en su primer acceso")
        
        # El rol para promotores debe ser "PROMOTORA"
        rol = st.selectbox("🎯 Rol", ["PROMOTORA"], 
                          disabled=True,
                          help="Los promotores tienen rol PROMOTORA por defecto")
        
        submitted = st.form_submit_button("👤 Crear Usuario para Promotor")
        
        if submitted:
            # Validaciones
            if not username.strip():
                st.error("❌ El nombre de usuario es obligatorio")
                return False
                
            if len(password) < 4:
                st.error("❌ La contraseña debe tener al menos 4 caracteres")
                return False
            
            # Verificar si el usuario ya existe
            usuario_existente = ejecutar_consulta(
                "SELECT id FROM usuarios WHERE username = %s", (username,)
            )
            
            if usuario_existente:
                st.error("❌ El nombre de usuario ya existe. Por favor elija otro.")
                return False
            
            # En una implementación real, aquí se hashearía la contraseña
            # Por ahora, guardamos en texto plano (SOLO PARA DESARROLLO)
            password_hash = password  # EN PRODUCCIÓN: usar bcrypt o similar
            
            query = """
                INSERT INTO usuarios (username, passwordhash, rol_sistema, id_promotor, activo)
                VALUES (%s, %s, %s, %s, 1)
            """
            
            params = (
                str(username), 
                str(password_hash), 
                "PROMOTORA", 
                int(id_promotor)
            )
            
            if ejecutar_comando(query, params):
                st.success(f"✅ Usuario '{username}' creado exitosamente para el promotor")
                
                # Mostrar credenciales temporales
                with st.expander("🔑 Credenciales de Acceso del Promotor", expanded=True):
                    st.code(f"""
USUARIO: {username}
CONTRASEÑA TEMPORAL: {password}
ROL: PROMOTORA

⚠️ **INSTRUCCIONES:**
1. Comparta estas credenciales de manera segura con el promotor
2. El promotor deberá cambiar la contraseña en su primer acceso
3. La contraseña temporal es: {password}
                    """)
                return True
            else:
                st.error("❌ Error inesperado creando el usuario")
                return False
    
    return None

def listar_promotores():
    """Mostrar lista de promotores existentes"""
    
    st.subheader("Promotores Registrados")
    
    promotores = obtener_promotores()
    
    if promotores:
        st.metric("📊 Total de Promotores", len(promotores))
        
        for promotor in promotores:
            with st.expander(f"👤 {promotor['nombre']} {promotor['apellido']} - {promotor['nombre_distrito']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**📞 Teléfono:** {promotor['tele']}")
                    st.write(f"**🏠 Dirección:** {promotor['direccion']}")
                
                with col2:
                    st.write(f"**🗺️ Distrito:** {promotor['nombre_distrito']}")
                    st.write(f"**📊 Estado:** {'✅ Activo' if promotor['activo'] else '❌ Inactivo'}")
                
                with col3:
                    # Verificar si tiene usuario
                    usuario = ejecutar_consulta(
                        "SELECT username FROM usuarios WHERE id_promotor = %s", 
                        (promotor['id_promotor'],)
                    )
                    
                    if usuario:
                        st.write(f"**🔐 Usuario:** {usuario[0]['username']}")
                    else:
                        st.write("**🔐 Usuario:** ❌ No tiene")
                    
                    # Acciones
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if not usuario:
                            if st.button("🔐 Crear Usuario", key=f"user_{promotor['id_promotor']}"):
                                crear_usuario_promotor(promotor['id_promotor'], promotor['nombre'], promotor['apellido'])
                                st.rerun()
                    
                    with col_act2:
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
    """Editar promotor existente - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener datos actuales del promotor
    promotor_data = ejecutar_consulta(
        "SELECT * FROM promotores WHERE id_promotor = %s", 
        (id_promotor,)
    )
    
    if not promotor_data:
        st.error("❌ Promotor no encontrado")
        return
    
    promotor = promotor_data[0]
    
    st.subheader(f"✏️ Editar Promotor: {promotor['nombre']} {promotor['apellido']}")
    
    with st.form(f"form_editar_promotor_{id_promotor}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_nombre = st.text_input("Nombre", value=promotor['nombre'])
            nuevo_apellido = st.text_input("Apellido", value=promotor['apellido'])
            nuevo_telefono = st.text_input("Teléfono", value=promotor['tele'])
        
        with col2:
            nueva_direccion = st.text_input("Dirección", value=promotor['direccion'])
            
            # Obtener distrito actual
            distritos_opciones = obtener_distritos()
            distrito_actual = next((d for d in distritos_opciones if d[0] == promotor['id_distrito']), None)
            indice_actual = distritos_opciones.index(distrito_actual) if distrito_actual else 0
            
            nuevo_id_distrito = st.selectbox(
                "Distrito", 
                options=[d[0] for d in distritos_opciones],
                format_func=lambda x: next((d[1] for d in distritos_opciones if d[0] == x), "Seleccionar"),
                index=indice_actual
            )
            
            nuevo_activo = st.checkbox("Activo", value=bool(promotor['activo']))
        
        col1, col2 = st.columns(2)
        with col1:
            guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if guardar_cambios:
            if validar_promotor(nuevo_nombre, nuevo_apellido, nuevo_telefono):
                if actualizar_promotor(id_promotor, nuevo_nombre, nuevo_apellido, nuevo_telefono, 
                                     nueva_direccion, nuevo_id_distrito, nuevo_activo):
                    st.success("✅ Promotor actualizado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar el promotor")
        
        if cancelar:
            st.rerun()

def actualizar_promotor(id_promotor, nombre, apellido, telefono, direccion, id_distrito, activo):
    """Actualizar promotor en la base de datos"""
    query = """
        UPDATE promotores 
        SET nombre = %s, apellido = %s, tele = %s, direccion = %s, id_distrito = %s, activo = %s
        WHERE id_promotor = %s
    """
    
    params = (
        str(nombre),
        str(apellido), 
        str(telefono),
        str(direccion),
        int(id_distrito),
        bool(activo),
        int(id_promotor)
    )
    
    try:
        return ejecutar_comando(query, params)
    except Exception as e:
        st.error(f"❌ Error al actualizar promotor: {e}")
        return None

def eliminar_promotor(id_promotor):
    """Eliminar promotor (lógico) - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener datos del promotor para confirmación
    promotor_data = ejecutar_consulta(
        "SELECT nombre, apellido FROM promotores WHERE id_promotor = %s", 
        (id_promotor,)
    )
    
    if not promotor_data:
        st.error("❌ Promotor no encontrado")
        return
    
    promotor = promotor_data[0]
    
    st.warning(f"⚠️ ¿Está seguro de que desea eliminar al promotor **{promotor['nombre']} {promotor['apellido']}**?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Sí, eliminar", key=f"confirm_eliminar_{id_promotor}"):
            # Verificar si el promotor tiene grupos asignados
            grupos_asignados = ejecutar_consulta(
                "SELECT COUNT(*) as count FROM grupos WHERE id_promotor = %s",
                (id_promotor,)
            )
            
            if grupos_asignados and grupos_asignados[0]['count'] > 0:
                st.error("❌ No se puede eliminar el promotor porque tiene grupos asignados. Reasigne los grupos primero.")
                return
            
            # Eliminar usuario asociado si existe
            ejecutar_comando(
                "DELETE FROM usuarios WHERE id_promotor = %s",
                (id_promotor,)
            )
            
            # Eliminar promotor
            if ejecutar_comando("DELETE FROM promotores WHERE id_promotor = %s", (id_promotor,)):
                st.success("✅ Promotor eliminado exitosamente")
                st.rerun()
            else:
                st.error("❌ Error al eliminar el promotor")
    
    with col2:
        if st.button("🔄 Desactivar", key=f"desactivar_{id_promotor}"):
            if ejecutar_comando("UPDATE promotores SET activo = 0 WHERE id_promotor = %s", (id_promotor,)):
                st.success("✅ Promotor desactivado exitosamente")
                st.rerun()
            else:
                st.error("❌ Error al desactivar el promotor")
    
    with col3:
        if st.button("❌ Cancelar", key=f"cancel_eliminar_{id_promotor}"):
            st.rerun()

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
        departamento = st.text_input("Departamento", placeholder="Ej: Francisco Morazán")
        
        submitted = st.form_submit_button("💾 Guardar Distrito")
        
        if submitted:
            if nombre_distrito and municipio:
                if guardar_distrito(nombre_distrito, municipio, departamento):
                    st.success("✅ Distrito creado exitosamente")
                    st.rerun()
            else:
                st.error("❌ Complete todos los campos obligatorios")

def guardar_distrito(nombre, municipio, departamento=""):
    """Guardar distrito en la base de datos"""
    query = "INSERT INTO distrito (nombre_distrito, municipio, departamento) VALUES (%s, %s, %s)"
    params = (str(nombre), str(municipio), str(departamento))
    return ejecutar_comando(query, params)

def listar_distritos():
    """Mostrar lista de distritos existentes - FUNCIÓN MEJORADA"""
    
    st.subheader("Distritos Registrados")
    
    distritos = obtener_todos_distritos()
    
    if distritos:
        st.metric("📊 Total de Distritos", len(distritos))
        
        for distrito in distritos:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{distrito['nombre_distrito']}**")
            with col2:
                st.write(f"**Municipio:** {distrito['municipio']}")
            with col3:
                st.write(f"**Departamento:** {distrito.get('departamento', 'N/A')}")
            with col4:
                if st.button("🗑️", key=f"eliminar_distrito_{distrito['id_distrito']}"):
                    eliminar_distrito(distrito['id_distrito'], distrito['nombre_distrito'])

def eliminar_distrito(id_distrito, nombre_distrito):
    """Eliminar distrito - FUNCIÓN IMPLEMENTADA"""
    
    st.warning(f"⚠️ ¿Está seguro de que desea eliminar el distrito **{nombre_distrito}**?")
    
    # Verificar si el distrito tiene promotores o grupos asignados
    promotores_asignados = ejecutar_consulta(
        "SELECT COUNT(*) as count FROM promotores WHERE id_distrito = %s",
        (id_distrito,)
    )
    
    grupos_asignados = ejecutar_consulta(
        "SELECT COUNT(*) as count FROM grupos WHERE id_distrito = %s",
        (id_distrito,)
    )
    
    if promotores_asignados and promotores_asignados[0]['count'] > 0:
        st.error("❌ No se puede eliminar el distrito porque tiene promotores asignados.")
        return
    
    if grupos_asignados and grupos_asignados[0]['count'] > 0:
        st.error("❌ No se puede eliminar el distrito porque tiene grupos asignados.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Sí, eliminar", key=f"confirm_eliminar_distrito_{id_distrito}"):
            if ejecutar_comando("DELETE FROM distrito WHERE id_distrito = %s", (id_distrito,)):
                st.success("✅ Distrito eliminado exitosamente")
                st.rerun()
            else:
                st.error("❌ Error al eliminar el distrito")
    
    with col2:
        if st.button("❌ Cancelar", key=f"cancel_eliminar_distrito_{id_distrito}"):
            st.rerun()

def obtener_todos_distritos():
    """Obtener todos los distritos"""
    return ejecutar_consulta("SELECT * FROM distrito ORDER BY nombre_distrito")