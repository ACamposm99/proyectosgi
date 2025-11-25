import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime
import hashlib  # AGREGAR ESTA IMPORTACIÓN

def hash_password(password: str) -> str:
    """Hashear contraseña usando SHA-256 (igual que en auth.py)"""
    return hashlib.sha256(password.encode()).hexdigest()


def modulo_gestion_promotores():
    """Módulo para gestión de promotores (solo ADMIN)"""
    
    st.header("👩‍💼 Gestión de Promotores")
    
    if st.session_state.rol != "ADMIN":
        st.warning("⚠️ Solo los administradores pueden gestionar promotores")
        return
    
    # Usar estado de sesión para controlar el flujo
    if 'promotor_creado' not in st.session_state:
        st.session_state.promotor_creado = None
    
    if st.session_state.promotor_creado:
        # Mostrar formulario de usuario para el promotor recién creado
        crear_usuario_para_promotor_existente()
    else:
        # Mostrar tabs normales
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
                    
                    # Si se marcó crear usuario, guardar en sesión y mostrar formulario de usuario
                    if crear_usuario:
                        st.session_state.promotor_creado = {
                            'id_promotor': id_promotor,
                            'nombre': nombre,
                            'apellido': apellido
                        }
                        st.rerun()
                else:
                    st.error("❌ Error al crear el promotor")

def crear_usuario_para_promotor_existente():
    """Formulario separado para crear usuario después de crear el promotor"""
    
    promotor_info = st.session_state.promotor_creado
    st.subheader(f"🔐 Crear Usuario para {promotor_info['nombre']} {promotor_info['apellido']}")
    
    st.info("Complete la información del usuario de acceso para el promotor")
    
    # Formulario separado para el usuario
    with st.form("form_usuario_promotor"):
        username = st.text_input("👤 Nombre de usuario", 
                               value=f"{promotor_info['nombre'].lower()}.{promotor_info['apellido'].lower()}",
                               help="Nombre de usuario para que el promotor acceda al sistema")
        
        password = st.text_input("🔒 Contraseña temporal", type="password", value="temp123",
                               help="Contraseña temporal que el promotor deberá cambiar en su primer acceso")
        
        # El rol para promotores debe ser "PROMOTORA"
        rol = st.selectbox("🎯 Rol", ["PROMOTORA"], 
                          disabled=True,
                          help="Los promotores tienen rol PROMOTORA por defecto")
        
        submitted = st.form_submit_button("👤 Crear Usuario")
        
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
                "SELECT id_usuario FROM usuarios WHERE username = %s", (username,)
            )
            
            if usuario_existente:
                st.error("❌ El nombre de usuario ya existe. Por favor elija otro.")
                return False
            
            # CORRECCIÓN: Hashear la contraseña antes de guardarla
            password_hash = hash_password(password)
            
            query = """
                INSERT INTO usuarios (username, passwordhash, rol_sistema, id_promotor, activo)
                VALUES (%s, %s, %s, %s, 1)
            """
            
            params = (
                str(username), 
                str(password_hash),  # Ahora guardamos el hash, no la contraseña en texto plano
                "PROMOTORA", 
                int(promotor_info['id_promotor'])
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
                
                # Limpiar estado de sesión y volver a la lista
                st.session_state.promotor_creado = None
                st.rerun()
                return True
            else:
                st.error("❌ Error inesperado creando el usuario")
                return False
    
    # Botón para cancelar la creación de usuario
    if st.button("❌ Cancelar creación de usuario"):
        st.session_state.promotor_creado = None
        st.rerun()


# El resto de las funciones se mantienen igual...
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
                                # Usar un enfoque similar para crear usuario desde la lista
                                st.session_state.crear_usuario_desde_lista = {
                                    'id_promotor': promotor['id_promotor'],
                                    'nombre': promotor['nombre'],
                                    'apellido': promotor['apellido']
                                }
                                st.rerun()
                    
                    with col_act2:
                        if st.button("✏️ Editar", key=f"editar_{promotor['id_promotor']}"):
                            editar_promotor(promotor['id_promotor'])
                        
                        if st.button("🗑️ Eliminar", key=f"eliminar_{promotor['id_promotor']}"):
                            eliminar_promotor(promotor['id_promotor'])
        
        # Manejar la creación de usuario desde la lista
        if 'crear_usuario_desde_lista' in st.session_state:
            crear_usuario_desde_lista()
    else:
        st.info("ℹ️ No hay promotores registrados")

def crear_usuario_desde_lista():
    """Crear usuario para promotor desde la lista"""
    
    promotor_info = st.session_state.crear_usuario_desde_lista
    
    st.subheader(f"🔐 Crear Usuario para {promotor_info['nombre']} {promotor_info['apellido']}")
    
    with st.form("form_usuario_desde_lista"):
        username = st.text_input("👤 Nombre de usuario", 
                               value=f"{promotor_info['nombre'].lower()}.{promotor_info['apellido'].lower()}",
                               key="username_lista")
        
        password = st.text_input("🔒 Contraseña temporal", type="password", value="temp123",
                               key="password_lista")
        
        submitted = st.form_submit_button("👤 Crear Usuario")
        
        if submitted:
            if not username.strip():
                st.error("❌ El nombre de usuario es obligatorio")
                return
                
            if len(password) < 4:
                st.error("❌ La contraseña debe tener al menos 4 caracteres")
                return
            
            # Verificar si el usuario ya existe
            usuario_existente = ejecutar_consulta(
                "SELECT id_usuario FROM usuarios WHERE username = %s", (username,)
            )
            
            if usuario_existente:
                st.error("❌ El nombre de usuario ya existe. Por favor elija otro.")
                return
            
            # CORRECCIÓN: Hashear la contraseña
            password_hash = hash_password(password)
            
            query = """
                INSERT INTO usuarios (username, passwordhash, rol_sistema, id_promotor, activo)
                VALUES (%s, %s, %s, %s, 1)
            """
            
            params = (
                str(username), 
                str(password_hash),  # Guardar el hash
                "PROMOTORA", 
                int(promotor_info['id_promotor'])
            )
            
            if ejecutar_comando(query, params):
                st.success(f"✅ Usuario '{username}' creado exitosamente")
                del st.session_state.crear_usuario_desde_lista
                st.rerun()
            else:
                st.error("❌ Error al crear el usuario")
    
    if st.button("❌ Cancelar", key="cancelar_desde_lista"):
        del st.session_state.crear_usuario_desde_lista
        st.rerun()


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

# ... (las funciones editar_promotor, actualizar_promotor, eliminar_promotor se mantienen igual)

def editar_promotor(id_promotor):
    """Editar promotor existente"""
    
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
    """Eliminar promotor (lógico)"""
    
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
    
    # Tabs para las diferentes operaciones CRUD
    tab1, tab2 = st.tabs(["➕ Nuevo Distrito", "📋 Lista de Distritos"])
    
    with tab1:
        crear_distrito()
    
    with tab2:
        listar_distritos()

def crear_distrito():
    """Formulario para crear nuevo distrito"""
    
    st.subheader("Crear Nuevo Distrito")
    
    with st.form("form_nuevo_distrito"):
        nombre_distrito = st.text_input("Nombre del Distrito *", placeholder="Ej: Distrito Central")
        municipio = st.text_input("Municipio *", placeholder="Ej: La Libertad")
        
        submitted = st.form_submit_button("💾 Guardar Distrito")
        
        if submitted:
            if nombre_distrito.strip() and municipio.strip():
                if guardar_distrito(nombre_distrito, municipio):
                    st.success("✅ Distrito creado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al crear el distrito")
            else:
                st.error("❌ Complete los campos obligatorios (*)")

def guardar_distrito(nombre, municipio):
    """Guardar distrito en la base de datos"""
    try:
        query = "INSERT INTO distrito (nombre_distrito, municipio) VALUES (%s, %s)"
        params = (
            str(nombre).strip(),
            str(municipio).strip() 
        )
        
        resultado = ejecutar_comando(query, params)
        return resultado is not None and resultado > 0
    except Exception as e:
        st.error(f"❌ Error al guardar distrito: {str(e)}")
        return False

def listar_distritos():
    """Mostrar lista de distritos existentes con opciones CRUD"""
    
    st.subheader("Distritos Registrados")
    
    # Obtener todos los distritos
    distritos = obtener_todos_distritos()
    
    if distritos:
        st.metric("📊 Total de Distritos", len(distritos))
        
        # Mostrar cada distrito con opciones de editar y eliminar
        for distrito in distritos:
            with st.expander(f"🗺️ {distrito['nombre_distrito']} - {distrito['municipio']}"):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**🏙️ Municipio:** {distrito['municipio']}")
                    
                with col2:
                    # Contar promotores en este distrito
                    promotores_count = contar_promotores_por_distrito(distrito['id_distrito'])
                    st.write(f"**👤 Promotores:** {promotores_count}")
                    
                    # Contar grupos en este distrito
                    grupos_count = contar_grupos_por_distrito(distrito['id_distrito'])
                    st.write(f"**🏢 Grupos:** {grupos_count}")
                
                with col3:
                    # Botones de acción
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✏️", key=f"editar_{distrito['id_distrito']}"):
                            st.session_state.editar_distrito_id = distrito['id_distrito']
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🗑️", key=f"eliminar_{distrito['id_distrito']}"):
                            st.session_state.eliminar_distrito_id = distrito['id_distrito']
                            st.rerun()
        
        # Manejar edición de distrito
        if 'editar_distrito_id' in st.session_state:
            editar_distrito(st.session_state.editar_distrito_id)
        
        # Manejar eliminación de distrito
        if 'eliminar_distrito_id' in st.session_state:
            eliminar_distrito(st.session_state.eliminar_distrito_id)
    
    else:
        st.info("ℹ️ No hay distritos registrados")

def obtener_todos_distritos():
    """Obtener todos los distritos de la base de datos"""
    try:
        return ejecutar_consulta("SELECT * FROM distrito ORDER BY nombre_distrito")
    except Exception as e:
        st.error(f"❌ Error al obtener distritos: {str(e)}")
        return []

def contar_promotores_por_distrito(id_distrito):
    """Contar cuántos promotores tiene un distrito"""
    try:
        resultado = ejecutar_consulta(
            "SELECT COUNT(*) as total FROM promotores WHERE id_distrito = %s",
            (id_distrito,)
        )
        return resultado[0]['total'] if resultado else 0
    except Exception:
        return 0

def contar_grupos_por_distrito(id_distrito):
    """Contar cuántos grupos tiene un distrito"""
    try:
        resultado = ejecutar_consulta(
            "SELECT COUNT(*) as total FROM grupos WHERE id_distrito = %s",
            (id_distrito,)
        )
        return resultado[0]['total'] if resultado else 0
    except Exception:
        return 0

def editar_distrito(id_distrito):
    """Editar distrito existente"""
    
    # Obtener datos actuales del distrito
    distrito_data = ejecutar_consulta(
        "SELECT * FROM distrito WHERE id_distrito = %s", 
        (id_distrito,)
    )
    
    if not distrito_data:
        st.error("❌ Distrito no encontrado")
        del st.session_state.editar_distrito_id
        return
    
    distrito = distrito_data[0]
    
    st.subheader(f"✏️ Editar Distrito: {distrito['nombre_distrito']}")
    
    with st.form(f"form_editar_distrito_{id_distrito}"):
        nuevo_nombre = st.text_input("Nombre del Distrito *", value=distrito['nombre_distrito'])
        nuevo_municipio = st.text_input("Municipio *", value=distrito['municipio'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
        
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if guardar_cambios:
            if nuevo_nombre.strip() and nuevo_municipio.strip():
                if actualizar_distrito(id_distrito, nuevo_nombre, nuevo_municipio):
                    st.success("✅ Distrito actualizado exitosamente")
                    del st.session_state.editar_distrito_id
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar el distrito")
            else:
                st.error("❌ Complete los campos obligatorios (*)")
        
        if cancelar:
            del st.session_state.editar_distrito_id
            st.rerun()

def actualizar_distrito(id_distrito, nombre, municipio):
    """Actualizar distrito en la base de datos"""
    try:
        query = """
            UPDATE distrito 
            SET nombre_distrito = %s, municipio = %s
            WHERE id_distrito = %s
        """
        
        params = (
            str(nombre).strip(),
            str(municipio).strip(),
            int(id_distrito)
        )
        
        resultado = ejecutar_comando(query, params)
        return resultado is not None and resultado > 0
    except Exception as e:
        st.error(f"❌ Error al actualizar distrito: {str(e)}")
        return False

def eliminar_distrito(id_distrito):
    """Eliminar distrito con validaciones"""
    
    # Obtener datos del distrito para confirmación
    distrito_data = ejecutar_consulta(
        "SELECT nombre_distrito FROM distrito WHERE id_distrito = %s", 
        (id_distrito,)
    )
    
    if not distrito_data:
        st.error("❌ Distrito no encontrado")
        del st.session_state.eliminar_distrito_id
        return
    
    nombre_distrito = distrito_data[0]['nombre_distrito']
    
    st.warning(f"⚠️ ¿Está seguro de que desea eliminar el distrito **{nombre_distrito}**?")
    
    # Verificar si el distrito tiene promotores asignados
    promotores_asignados = contar_promotores_por_distrito(id_distrito)
    
    # Verificar si el distrito tiene grupos asignados
    grupos_asignados = contar_grupos_por_distrito(id_distrito)
    
    if promotores_asignados > 0:
        st.error(f"❌ No se puede eliminar el distrito porque tiene {promotores_asignados} promotor(es) asignado(s).")
        st.info("ℹ️ Reasigne los promotores a otro distrito antes de eliminar.")
    
    if grupos_asignados > 0:
        st.error(f"❌ No se puede eliminar el distrito porque tiene {grupos_asignados} grupo(s) asignado(s).")
        st.info("ℹ️ Reasigne los grupos a otro distrito antes de eliminar.")
    
    # Solo permitir eliminar si no hay dependencias
    if promotores_asignados == 0 and grupos_asignados == 0:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sí, eliminar", key=f"confirm_eliminar_distrito_{id_distrito}"):
                if ejecutar_comando("DELETE FROM distrito WHERE id_distrito = %s", (id_distrito,)):
                    st.success("✅ Distrito eliminado exitosamente")
                    del st.session_state.eliminar_distrito_id
                    st.rerun()
                else:
                    st.error("❌ Error al eliminar el distrito")
        
        with col2:
            if st.button("❌ Cancelar", key=f"cancel_eliminar_distrito_{id_distrito}"):
                del st.session_state.eliminar_distrito_id
                st.rerun()
    else:
        # Botón para cancelar si no se puede eliminar
        if st.button("❌ Cancelar", key=f"cancel_eliminar_distrito_{id_distrito}"):
            del st.session_state.eliminar_distrito_id
            st.rerun()
def modulo_gestion_directiva():
    """Módulo para gestión de directiva (solo ADMIN)"""
    
    st.header("👨‍💼 Gestión de Directiva")
    
    if st.session_state.rol != "ADMIN":
        st.warning("⚠️ Solo los administradores pueden gestionar la directiva")
        return
    
    # Tabs para las diferentes operaciones
    tab1, tab2 = st.tabs(["➕ Asignar Directivo", "📋 Lista de Directivos"])
    
    with tab1:
        asignar_directivo()
    
    with tab2:
        listar_directivos()

def asignar_directivo():
    """Formulario para asignar un directivo a un grupo"""
    
    st.subheader("Asignar Nuevo Directivo")
    
    # Obtener grupos activos
    grupos = obtener_grupos_activos()
    if not grupos:
        st.error("❌ No hay grupos activos disponibles")
        return
    
    # Obtener socios
    socios = obtener_socios_activos()
    if not socios:
        st.error("❌ No hay socios disponibles")
        return
    
    # Obtener roles de directiva
    roles = obtener_roles_directiva()
    if not roles:
        st.error("❌ No hay roles de directiva definidos")
        return
    
    with st.form("form_asignar_directivo"):
        # Seleccionar grupo
        grupo_seleccionado = st.selectbox(
            "Grupo *",
            options=grupos,
            format_func=lambda x: f"{x['nombre_grupo']} - {x['lugar_reunion']}"
        )
        
        # Seleccionar socio
        socio_seleccionado = st.selectbox(
            "Socio *",
            options=socios,
            format_func=lambda x: f"{x['nombre']} {x['apellido']} - {x['nombre_grupo']}"
        )
        
        # Seleccionar rol
        rol_seleccionado = st.selectbox(
            "Rol en la Directiva *",
            options=roles,
            format_func=lambda x: f"{x['tipo_rol']} - {x['funcion']}"
        )
        
        # Fecha de inicio
        fecha_inicio = st.date_input("Fecha de inicio *", datetime.now())
        
        # Estado
        estado = st.selectbox("Estado *", ["ACTIVO", "INACTIVO"])
        
        # Opción para crear usuario
        st.markdown("---")
        st.subheader("👤 Crear Usuario de Acceso")
        crear_usuario = st.checkbox("Crear usuario de acceso para este directivo", value=True)
        
        usuario_data = {}
        if crear_usuario:
            col_user1, col_user2 = st.columns(2)
            with col_user1:
                # Generar username sugerido
                username_sugerido = f"{socio_seleccionado['nombre'].lower()}.{socio_seleccionado['apellido'].lower()}"
                usuario_data['username'] = st.text_input(
                    "Nombre de usuario *", 
                    value=username_sugerido,
                    placeholder="Nombre para iniciar sesión"
                )
            with col_user2:
                usuario_data['password'] = st.text_input(
                    "Contraseña temporal *", 
                    type="password", 
                    value="temp123",
                    placeholder="Contraseña segura"
                )
        
        submitted = st.form_submit_button("💾 Asignar Directivo y Crear Usuario")
        
        if submitted:
            if not grupo_seleccionado or not socio_seleccionado or not rol_seleccionado:
                st.error("❌ Complete todos los campos obligatorios (*)")
                return
            
            if crear_usuario and (not usuario_data.get('username') or not usuario_data.get('password')):
                st.error("❌ Para crear usuario, complete nombre de usuario y contraseña")
                return
            
            # Verificar si el socio ya tiene un rol en este grupo
            directivo_existente = ejecutar_consulta(
                "SELECT id_directiva FROM directiva_grupo WHERE id_socio = %s AND id_grupo = %s",
                (socio_seleccionado['id_socio'], grupo_seleccionado['id_grupo'])
            )
            
            if directivo_existente:
                st.error("❌ Este socio ya tiene un rol asignado en este grupo")
                return
            
            # Verificar si el username ya existe
            if crear_usuario:
                usuario_existente = ejecutar_consulta(
                    "SELECT id_usuario FROM usuarios WHERE username = %s", 
                    (usuario_data['username'],)
                )
                if usuario_existente:
                    st.error("❌ El nombre de usuario ya existe. Por favor elija otro.")
                    return
            
            # Asignar directivo
            id_directiva = guardar_directivo(
                socio_seleccionado['id_socio'], 
                grupo_seleccionado['id_grupo'], 
                rol_seleccionado['id_rol'], 
                fecha_inicio, 
                estado
            )
            
            if id_directiva:
                st.success("✅ Directivo asignado exitosamente")
                
                # Crear usuario si está marcado
                if crear_usuario and usuario_data.get('username') and usuario_data.get('password'):
                    if crear_usuario_directivo(
                        socio_seleccionado['id_socio'], 
                        usuario_data['username'], 
                        usuario_data['password'],
                        socio_seleccionado['nombre'],
                        socio_seleccionado['apellido'],
                        rol_seleccionado['tipo_rol']
                    ):
                        st.success("✅ Usuario creado exitosamente")
                    else:
                        st.error("❌ Error al crear el usuario")
                
                st.rerun()
            else:
                st.error("❌ Error al asignar el directivo")

def crear_usuario_directivo(id_socio, username, password, nombre, apellido, rol_directiva):
    """Crear usuario para un directivo"""
    try:
        # Hashear la contraseña
        password_hash = hash_password(password)
        
        query = """
            INSERT INTO usuarios (username, passwordhash, rol_sistema, id_socio, activo)
            VALUES (%s, %s, %s, %s, 1)
        """
        
        params = (
            str(username), 
            str(password_hash), 
            "DIRECTIVA", 
            int(id_socio)
        )
        
        resultado = ejecutar_comando(query, params)
        
        if resultado and resultado > 0:
            # Mostrar credenciales
            with st.expander("🔑 Credenciales de Acceso del Directivo", expanded=True):
                st.code(f"""
                USUARIO: {username}
                CONTRASEÑA TEMPORAL: {password}
                ROL SISTEMA: DIRECTIVA
                ROL EN GRUPO: {rol_directiva}
                NOMBRE: {nombre} {apellido}

                ⚠️ **INSTRUCCIONES:**
                1. Comparta estas credenciales de manera segura con el directivo
                2. El directivo deberá cambiar la contraseña en su primer acceso
                3. La contraseña temporal es: {password}
                """)
            return True
        else:
            st.error("❌ Error al crear el usuario en la base de datos")
            return False
            
    except Exception as e:
        st.error(f"❌ Error al crear usuario para directivo: {str(e)}")
        return False


def guardar_directivo(id_socio, id_grupo, id_rol, fecha_inicio, estado):
    """Guardar asignación de directivo en la base de datos"""
    try:
        query = """
            INSERT INTO directiva_grupo (id_socio, id_grupo, id_rol, fecha_inicio, estado)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        params = (
            int(id_socio),
            int(id_grupo),
            int(id_rol),
            fecha_inicio,
            estado
        )
        
        resultado = ejecutar_comando(query, params)
        return resultado is not None and resultado > 0
    except Exception as e:
        st.error(f"❌ Error al guardar directivo: {str(e)}")
        return False

def listar_directivos():
    """Mostrar lista de directivos existentes con opciones CRUD"""
    
    st.subheader("Directivos Registrados")
    
    # Obtener todos los directivos
    directivos = obtener_todos_directivos()
    
    if directivos:
        st.metric("📊 Total de Directivos", len(directivos))
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "ACTIVO", "INACTIVO"])
        with col2:
            filtro_grupo = st.selectbox("Filtrar por grupo:", ["Todos"] + list(set([d['nombre_grupo'] for d in directivos])))
        
        # Aplicar filtros
        directivos_filtrados = directivos
        if filtro_estado != "Todos":
            directivos_filtrados = [d for d in directivos_filtrados if d['estado'] == filtro_estado]
        if filtro_grupo != "Todos":
            directivos_filtrados = [d for d in directivos_filtrados if d['nombre_grupo'] == filtro_grupo]
        
        st.metric("📊 Directivos Mostrados", len(directivos_filtrados))
        
        # Mostrar directivos
        for directivo in directivos_filtrados:
            with st.expander(f"👤 {directivo['nombre_socio']} {directivo['apellido_socio']} - {directivo['tipo_rol']} - {directivo['nombre_grupo']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Grupo:** {directivo['nombre_grupo']}")
                    st.write(f"**Socio:** {directivo['nombre_socio']} {directivo['apellido_socio']}")
                    st.write(f"**Rol:** {directivo['tipo_rol']}")
                    st.write(f"**Función:** {directivo['funcion']}")
                
                with col2:
                    st.write(f"**Fecha inicio:** {directivo['fecha_inicio'].strftime('%d/%m/%Y')}")
                    if directivo['fecha_fin']:
                        st.write(f"**Fecha fin:** {directivo['fecha_fin'].strftime('%d/%m/%Y')}")
                    else:
                        st.write("**Fecha fin:** Activo")
                    st.write(f"**Estado:** {directivo['estado']}")
                
                with col3:
                    # Verificar si tiene usuario
                    usuario = ejecutar_consulta(
                        "SELECT username FROM usuarios WHERE id_socio = %s", 
                        (directivo['id_socio'],)
                    )
                    
                    if usuario:
                        st.write(f"**🔐 Usuario:** {usuario[0]['username']}")
                    else:
                        st.write("**🔐 Usuario:** ❌ No tiene")
                        if st.button("🔐 Crear Usuario", key=f"user_{directivo['id_directiva']}"):
                            st.session_state.crear_usuario_directivo = {
                                'id_socio': directivo['id_socio'],
                                'nombre': directivo['nombre_socio'],
                                'apellido': directivo['apellido_socio'],
                                'rol_directiva': directivo['tipo_rol'],
                                'id_directiva': directivo['id_directiva']
                            }
                            st.rerun()
                    
                    # Botones de acción
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✏️ Editar", key=f"editar_{directivo['id_directiva']}"):
                            st.session_state.editar_directiva_id = directivo['id_directiva']
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🗑️ Eliminar", key=f"eliminar_{directivo['id_directiva']}"):
                            st.session_state.eliminar_directiva_id = directivo['id_directiva']
                            st.rerun()
        
        # Manejar creación de usuario desde la lista
        if 'crear_usuario_directivo' in st.session_state:
            crear_usuario_directivo_desde_lista()
        
        # Manejar edición de directivo
        if 'editar_directiva_id' in st.session_state:
            editar_directivo(st.session_state.editar_directiva_id)
        
        # Manejar eliminación de directivo
        if 'eliminar_directiva_id' in st.session_state:
            eliminar_directivo(st.session_state.eliminar_directiva_id)
    
    else:
        st.info("ℹ️ No hay directivos registrados")

def crear_usuario_directivo_desde_lista():
    """Crear usuario para directivo desde la lista"""
    
    directivo_info = st.session_state.crear_usuario_directivo
    
    st.subheader(f"🔐 Crear Usuario para {directivo_info['nombre']} {directivo_info['apellido']}")
    
    with st.form("form_usuario_directivo_lista"):
        # Generar username sugerido
        username_sugerido = f"{directivo_info['nombre'].lower()}.{directivo_info['apellido'].lower()}"
        username = st.text_input("👤 Nombre de usuario *", value=username_sugerido)
        password = st.text_input("🔒 Contraseña temporal *", type="password", value="temp123")
        
        submitted = st.form_submit_button("👤 Crear Usuario")
        
        if submitted:
            if not username or not password:
                st.error("❌ Complete todos los campos obligatorios")
                return
            
            # Verificar si el username ya existe
            usuario_existente = ejecutar_consulta(
                "SELECT id_usuario FROM usuarios WHERE username = %s", 
                (username,)
            )
            if usuario_existente:
                st.error("❌ El nombre de usuario ya existe. Por favor elija otro.")
                return
            
            if crear_usuario_directivo(
                directivo_info['id_socio'],
                username,
                password,
                directivo_info['nombre'],
                directivo_info['apellido'],
                directivo_info['rol_directiva']
            ):
                del st.session_state.crear_usuario_directivo
                st.rerun()
    
    if st.button("❌ Cancelar", key="cancelar_usuario_directivo"):
        del st.session_state.crear_usuario_directivo
        st.rerun()

def obtener_todos_directivos():
    """Obtener todos los directivos con información relacionada"""
    query = """
        SELECT dg.id_directiva, dg.fecha_inicio, dg.fecha_fin, dg.estado,
               s.id_socio, s.nombre as nombre_socio, s.apellido as apellido_socio,
               g.id_grupo, g.nombre_grupo,
               r.id_rol, r.tipo_rol, r.funcion
        FROM directiva_grupo dg
        JOIN socios s ON dg.id_socio = s.id_socio
        JOIN grupos g ON dg.id_grupo = g.id_grupo
        JOIN roles r ON dg.id_rol = r.id_rol
        ORDER BY g.nombre_grupo, r.tipo_rol
    """
    return ejecutar_consulta(query)

def obtener_grupos_activos():
    """Obtener lista de grupos activos"""
    return ejecutar_consulta("SELECT id_grupo, nombre_grupo, lugar_reunion FROM grupos WHERE estado = 'ACTIVO' ORDER BY nombre_grupo")

def obtener_socios_activos():
    """Obtener lista de socios activos con sus grupos"""
    return ejecutar_consulta("""
        SELECT s.id_socio, s.nombre, s.apellido, g.nombre_grupo 
        FROM socios s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        WHERE s.estado = 'ACTIVO'
        ORDER BY s.nombre, s.apellido
    """)

def obtener_roles_directiva():
    """Obtener lista de roles de directiva"""
    return ejecutar_consulta("SELECT id_rol, tipo_rol, funcion FROM roles ORDER BY id_rol")

def editar_directivo(id_directiva):
    """Editar directivo existente"""
    
    # Obtener datos actuales del directivo
    directivo_data = ejecutar_consulta(
        "SELECT * FROM directiva_grupo WHERE id_directiva = %s", 
        (id_directiva,)
    )
    
    if not directivo_data:
        st.error("❌ Directivo no encontrado")
        del st.session_state.editar_directiva_id
        return
    
    directivo = directivo_data[0]
    
    # Obtener información adicional
    info_adicional = ejecutar_consulta("""
        SELECT s.nombre, s.apellido, g.nombre_grupo, r.tipo_rol, s.id_socio
        FROM directiva_grupo dg
        JOIN socios s ON dg.id_socio = s.id_socio
        JOIN grupos g ON dg.id_grupo = g.id_grupo
        JOIN roles r ON dg.id_rol = r.id_rol
        WHERE dg.id_directiva = %s
    """, (id_directiva,))[0]
    
    st.subheader(f"✏️ Editar Directivo: {info_adicional['nombre']} {info_adicional['apellido']}")
    
    # Obtener opciones para los selectores
    roles = obtener_roles_directiva()
    
    # Verificar si tiene usuario
    usuario_existente = ejecutar_consulta(
        "SELECT username FROM usuarios WHERE id_socio = %s", 
        (info_adicional['id_socio'],)
    )
    
    with st.form(f"form_editar_directivo_{id_directiva}"):
        # Mostrar información actual (solo lectura)
        st.write(f"**Grupo:** {info_adicional['nombre_grupo']}")
        st.write(f"**Socio:** {info_adicional['nombre']} {info_adicional['apellido']}")
        
        if usuario_existente:
            st.write(f"**🔐 Usuario:** {usuario_existente[0]['username']}")
        else:
            st.write("**🔐 Usuario:** ❌ No tiene usuario")
        
        # Selector de rol
        rol_actual = next((r for r in roles if r['id_rol'] == directivo['id_rol']), None)
        indice_rol = roles.index(rol_actual) if rol_actual else 0
        nuevo_rol = st.selectbox(
            "Rol *",
            options=roles,
            index=indice_rol,
            format_func=lambda x: f"{x['tipo_rol']} - {x['funcion']}"
        )
        
        # Fechas
        nueva_fecha_inicio = st.date_input("Fecha de inicio *", value=directivo['fecha_inicio'])
        nueva_fecha_fin = st.date_input("Fecha de fin (opcional)", value=directivo.get('fecha_fin'))
        
        # Estado
        nuevo_estado = st.selectbox("Estado *", ["ACTIVO", "INACTIVO"], 
                                   index=0 if directivo['estado'] == 'ACTIVO' else 1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
        
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if guardar_cambios:
            if actualizar_directivo(id_directiva, nuevo_rol['id_rol'], nueva_fecha_inicio, nueva_fecha_fin, nuevo_estado):
                st.success("✅ Directivo actualizado exitosamente")
                del st.session_state.editar_directiva_id
                st.rerun()
            else:
                st.error("❌ Error al actualizar el directivo")
        
        if cancelar:
            del st.session_state.editar_directiva_id
            st.rerun()

def actualizar_directivo(id_directiva, id_rol, fecha_inicio, fecha_fin, estado):
    """Actualizar directivo en la base de datos"""
    try:
        query = """
            UPDATE directiva_grupo 
            SET id_rol = %s, fecha_inicio = %s, fecha_fin = %s, estado = %s
            WHERE id_directiva = %s
        """
        
        params = (
            int(id_rol),
            fecha_inicio,
            fecha_fin,
            estado,
            int(id_directiva)
        )
        
        resultado = ejecutar_comando(query, params)
        return resultado is not None and resultado > 0
    except Exception as e:
        st.error(f"❌ Error al actualizar directivo: {str(e)}")
        return False

def eliminar_directivo(id_directiva):
    """Eliminar directivo y su usuario si existe"""
    
    # Obtener datos del directivo para confirmación
    directivo_data = ejecutar_consulta("""
        SELECT s.nombre, s.apellido, g.nombre_grupo, r.tipo_rol, s.id_socio
        FROM directiva_grupo dg
        JOIN socios s ON dg.id_socio = s.id_socio
        JOIN grupos g ON dg.id_grupo = g.id_grupo
        JOIN roles r ON dg.id_rol = r.id_rol
        WHERE dg.id_directiva = %s
    """, (id_directiva,))
    
    if not directivo_data:
        st.error("❌ Directivo no encontrado")
        del st.session_state.eliminar_directiva_id
        return
    
    directivo = directivo_data[0]
    
    st.warning(f"⚠️ ¿Está seguro de que desea eliminar a **{directivo['nombre']} {directivo['apellido']}** como **{directivo['tipo_rol']}** del grupo **{directivo['nombre_grupo']}**?")
    
    st.info("ℹ️ **Nota:** Esta acción también eliminará el usuario de acceso del directivo si existe.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Sí, eliminar", key=f"confirm_eliminar_directivo_{id_directiva}"):
            try:
                # Eliminar usuario primero si existe
                ejecutar_comando(
                    "DELETE FROM usuarios WHERE id_socio = %s",
                    (directivo['id_socio'],)
                )
                
                # Eliminar directivo
                if ejecutar_comando("DELETE FROM directiva_grupo WHERE id_directiva = %s", (id_directiva,)):
                    st.success("✅ Directivo y usuario eliminados exitosamente")
                    del st.session_state.eliminar_directiva_id
                    st.rerun()
                else:
                    st.error("❌ Error al eliminar el directivo")
            except Exception as e:
                st.error(f"❌ Error al eliminar: {str(e)}")
    
    with col_btn2:
        if st.button("❌ Cancelar", key=f"cancel_eliminar_directivo_{id_directiva}"):
            del st.session_state.eliminar_directiva_id
            st.rerun()