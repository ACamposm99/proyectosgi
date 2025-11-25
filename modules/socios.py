import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime
import pandas as pd
import plotly.express as px

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
            
            # CORREGIDO: Obtener solo el ID de los selectboxes
            grupos_opciones = obtener_grupos_con_nombres()
            id_grupo = st.selectbox("🏢 Grupo", 
                                   options=[g[0] for g in grupos_opciones],
                                   format_func=lambda x: next((g[1] for g in grupos_opciones if g[0] == x), "Seleccionar"))
            
            distritos_opciones = obtener_distritos()
            id_distrito = st.selectbox("🗺️ Distrito", 
                                      options=[d[0] for d in distritos_opciones],
                                      format_func=lambda x: next((d[1] for d in distritos_opciones if d[0] == x), "Seleccionar"))
        
        # Campos adicionales para información más completa
        st.markdown("### 📝 Información Adicional")
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            fecha_nacimiento = st.date_input(
                "🎂 Fecha de Nacimiento", 
                min_value=datetime(1920, 1, 1),
                max_value=datetime.now(),
                value=datetime(1990, 1, 1)
            )
            
            genero = st.selectbox(
                "⚧️ Género",
                ["", "Femenino", "Masculino", "Otro", "Prefiero no decir"]
            )
        
        with col_info2:
            ocupacion = st.text_input("💼 Ocupación", placeholder="Ej: Comerciante, Ama de casa, Estudiante...")
            email = st.text_input("📧 Email (opcional)", placeholder="Ej: maria.garcia@email.com")
        
        observaciones = st.text_area(
            "📋 Observaciones", 
            placeholder="Información adicional relevante sobre el socio..."
        )
        
        submitted = st.form_submit_button("💾 Registrar Socio")
        
        if submitted:
            if validar_socio(nombre, apellido, telefono):
                id_socio = crear_socio(
                    nombre, apellido, telefono, direccion, id_grupo, id_distrito,
                    fecha_nacimiento, genero, ocupacion, email, observaciones
                )
                if id_socio:
                    st.success(f"✅ Socio '{nombre} {apellido}' registrado exitosamente (ID: {id_socio})")
                    
                    # Mostrar resumen del registro
                    with st.expander("📋 Ver Resumen del Registro", expanded=True):
                        st.write(f"**Nombre completo:** {nombre} {apellido}")
                        st.write(f"**Teléfono:** {telefono}")
                        st.write(f"**Dirección:** {direccion}")
                        st.write(f"**Grupo:** {next((g[1] for g in grupos_opciones if g[0] == id_grupo), 'N/A')}")
                        st.write(f"**Distrito:** {next((d[1] for d in distritos_opciones if d[0] == id_distrito), 'N/A')}")
                        
                        if ocupacion:
                            st.write(f"**Ocupación:** {ocupacion}")
                        if email:
                            st.write(f"**Email:** {email}")

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
    
    # Validar formato de teléfono (solo números y al menos 8 dígitos)
    telefono_limpio = ''.join(filter(str.isdigit, telefono))
    if len(telefono_limpio) < 8:
        st.error("❌ El teléfono debe tener al menos 8 dígitos")
        return False
    
    return True

def crear_socio(nombre, apellido, telefono, direccion, id_grupo, id_distrito, 
                fecha_nacimiento=None, genero="", ocupacion="", email="", observaciones=""):
    """Crear nuevo socio en la base de datos - FUNCIÓN MEJORADA"""
    
    # CONVERSIÓN EXPLÍCITA DE TIPOS DE DATOS
    try:
        # Asegurar que los IDs sean enteros
        id_grupo = int(id_grupo) if id_grupo else None
        id_distrito = int(id_distrito) if id_distrito else None
        
        # Asegurar que textos sean strings
        nombre = str(nombre) if nombre else ""
        apellido = str(apellido) if apellido else ""
        telefono = str(telefono) if telefono else ""
        direccion = str(direccion) if direccion else ""
        genero = str(genero) if genero else ""
        ocupacion = str(ocupacion) if ocupacion else ""
        email = str(email) if email else ""
        observaciones = str(observaciones) if observaciones else ""
        
        # Formatear fecha de nacimiento
        if fecha_nacimiento and hasattr(fecha_nacimiento, 'strftime'):
            fecha_nacimiento = fecha_nacimiento.strftime('%Y-%m-%d')
        
    except (ValueError, TypeError) as e:
        st.error(f"❌ Error en conversión de datos: {e}")
        return False
    
    query = """
        INSERT INTO socios (nombre, apellido, telefono, direccion, id_grupo, id_distrito,
                          fecha_nacimiento, genero, ocupacion, email, observaciones, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (
        nombre, apellido, telefono, direccion, id_grupo, id_distrito,
        fecha_nacimiento, genero, ocupacion, email, observaciones, datetime.now()
    )
    
    return ejecutar_comando(query, params)

def listar_socios():
    """Mostrar lista de socios existentes - FUNCIÓN COMPLETAMENTE IMPLEMENTADA"""
    
    st.subheader("Socios Registrados")
    
    # Filtros avanzados
    st.markdown("### 🔍 Filtros de Búsqueda")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        grupos_opciones = obtener_grupos_con_nombres()
        nombres_grupos = [grupo[1] for grupo in grupos_opciones]
        filtro_grupo = st.selectbox("Filtrar por Grupo", ["Todos"] + nombres_grupos)
    
    with col2:
        distritos_opciones = obtener_distritos()
        nombres_distritos = [distrito[1] for distrito in distritos_opciones]
        filtro_distrito = st.selectbox("Filtrar por Distrito", ["Todos"] + nombres_distritos)
    
    with col3:
        filtro_estado = st.selectbox("Filtrar por Estado", ["Todos", "Activos", "Inactivos"])
    
    # Búsqueda por nombre
    busqueda_nombre = st.text_input("🔎 Buscar por nombre o apellido", placeholder="Ej: María García")
    
    # Obtener socios con filtros
    socios = obtener_socios_filtrados(filtro_grupo, filtro_distrito, filtro_estado, busqueda_nombre)
    
    if socios:
        # Mostrar estadísticas
        total_socios = len(socios)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total de Socios", total_socios)
        
        with col2:
            # Calcular promedio de edad
            edades = [calcular_edad(socio.get('fecha_nacimiento')) for socio in socios if socio.get('fecha_nacimiento')]
            promedio_edad = sum(edades) / len(edades) if edades else 0
            st.metric("📅 Edad Promedio", f"{promedio_edad:.1f} años")
        
        with col3:
            # Contar por género
            generos = [socio.get('genero', '') for socio in socios]
            femenino = generos.count('Femenino')
            masculino = generos.count('Masculino')
            st.metric("⚧️ Género", f"♀{femenino} ♂{masculino}")
        
        with col4:
            # Socios por grupo
            grupos_count = {}
            for socio in socios:
                grupo = socio['nombre_grupo']
                grupos_count[grupo] = grupos_count.get(grupo, 0) + 1
            grupo_mayor = max(grupos_count.items(), key=lambda x: x[1]) if grupos_count else ("N/A", 0)
            st.metric("🏢 Grupo Mayor", f"{grupo_mayor[1]} en {grupo_mayor[0]}")
        
        # Gráfico de distribución por grupo
        if len(grupos_count) > 1:
            st.markdown("### 📈 Distribución por Grupo")
            df_grupos = pd.DataFrame(list(grupos_count.items()), columns=['Grupo', 'Cantidad'])
            fig = px.pie(df_grupos, values='Cantidad', names='Grupo', title='Socios por Grupo')
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de socios
        st.markdown("### 👥 Lista de Socios")
        
        for socio in socios:
            with st.expander(f"👤 {socio['nombre']} {socio['apellido']} - {socio['nombre_grupo']}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**📞 Teléfono:** {socio['telefono']}")
                    st.write(f"**🏠 Dirección:** {socio['direccion']}")
                    if socio.get('email'):
                        st.write(f"**📧 Email:** {socio['email']}")
                    if socio.get('fecha_nacimiento'):
                        edad = calcular_edad(socio['fecha_nacimiento'])
                        st.write(f"**🎂 Edad:** {edad} años")
                
                with col2:
                    st.write(f"**🏢 Grupo:** {socio['nombre_grupo']}")
                    st.write(f"**🗺️ Distrito:** {socio['nombre_distrito']}")
                    if socio.get('ocupacion'):
                        st.write(f"**💼 Ocupación:** {socio['ocupacion']}")
                    if socio.get('genero'):
                        st.write(f"**⚧️ Género:** {socio['genero']}")
                    st.write(f"**📅 Fecha Registro:** {socio['fecha_registro'].strftime('%d/%m/%Y')}")
                
                with col3:
                    # Acciones
                    col_edit, col_det, col_del = st.columns(3)
                    
                    with col_edit:
                        if st.button("✏️", key=f"editar_{socio['id_socio']}", help="Editar socio"):
                            st.session_state[f'editar_socio_{socio["id_socio"]}'] = True
                    
                    with col_det:
                        if st.button("👁️", key=f"detalles_{socio['id_socio']}", help="Ver detalles"):
                            st.session_state[f'detalles_socio_{socio["id_socio"]}'] = True
                    
                    with col_del:
                        if st.button("🗑️", key=f"eliminar_{socio['id_socio']}", help="Eliminar socio"):
                            st.session_state[f'eliminar_socio_{socio["id_socio"]}'] = True
                
                # Editar socio si se hizo clic en editar
                if f'editar_socio_{socio["id_socio"]}' in st.session_state and st.session_state[f'editar_socio_{socio["id_socio"]}']:
                    editar_socio(socio['id_socio'])
                
                # Ver detalles si se hizo clic en detalles
                if f'detalles_socio_{socio["id_socio"]}' in st.session_state and st.session_state[f'detalles_socio_{socio["id_socio"]}']:
                    ver_detalles_socio(socio['id_socio'])
                
                # Eliminar socio si se hizo clic en eliminar
                if f'eliminar_socio_{socio["id_socio"]}' in st.session_state and st.session_state[f'eliminar_socio_{socio["id_socio"]}']:
                    eliminar_socio(socio['id_socio'], f"{socio['nombre']} {socio['apellido']}")
        
        # Opción de exportar datos
        st.markdown("---")
        if st.button("📤 Exportar Lista de Socios a CSV"):
            exportar_socios_csv(socios)
    else:
        st.info("ℹ️ No hay socios registrados que coincidan con los filtros")

def obtener_socios_filtrados(filtro_grupo, filtro_distrito, filtro_estado, busqueda_nombre):
    """Obtener socios aplicando filtros - FUNCIÓN IMPLEMENTADA"""
    
    query = """
        SELECT s.*, g.nombre_grupo, d.nombre_distrito
        FROM socios s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        JOIN distrito d ON s.id_distrito = d.id_distrito
        WHERE 1=1
    """
    
    params = []
    
    if filtro_grupo != "Todos":
        query += " AND g.nombre_grupo = %s"
        params.append(filtro_grupo)
    
    if filtro_distrito != "Todos":
        query += " AND d.nombre_distrito = %s"
        params.append(filtro_distrito)
    
    if filtro_estado != "Todos":
        if filtro_estado == "Activos":
            query += " AND s.activo = 1"
        elif filtro_estado == "Inactivos":
            query += " AND s.activo = 0"
    
    if busqueda_nombre.strip():
        query += " AND (s.nombre LIKE %s OR s.apellido LIKE %s)"
        params.extend([f"%{busqueda_nombre}%", f"%{busqueda_nombre}%"])
    
    query += " ORDER BY g.nombre_grupo, s.apellido, s.nombre"
    
    return ejecutar_consulta(query, params)

def editar_socio(id_socio):
    """Editar socio existente - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener datos actuales del socio
    socio_data = ejecutar_consulta("""
        SELECT s.*, g.nombre_grupo, d.nombre_distrito
        FROM socios s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        JOIN distrito d ON s.id_distrito = d.id_distrito
        WHERE s.id_socio = %s
    """, (id_socio,))
    
    if not socio_data:
        st.error("❌ Socio no encontrado")
        return
    
    socio = socio_data[0]
    
    st.subheader(f"✏️ Editar Socio: {socio['nombre']} {socio['apellido']}")
    
    with st.form(f"form_editar_socio_{id_socio}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_nombre = st.text_input("👤 Nombre", value=socio['nombre'])
            nuevo_apellido = st.text_input("👤 Apellido", value=socio['apellido'])
            nuevo_telefono = st.text_input("📞 Teléfono", value=socio['telefono'])
            nueva_direccion = st.text_input("🏠 Dirección", value=socio['direccion'])
            
            # Obtener grupos y distritos actualizados
            grupos_opciones = obtener_grupos_con_nombres()
            grupo_actual = next((g for g in grupos_opciones if g[0] == socio['id_grupo']), None)
            indice_grupo = grupos_opciones.index(grupo_actual) if grupo_actual else 0
            
            nuevo_id_grupo = st.selectbox(
                "🏢 Grupo", 
                options=[g[0] for g in grupos_opciones],
                format_func=lambda x: next((g[1] for g in grupos_opciones if g[0] == x), "Seleccionar"),
                index=indice_grupo
            )
        
        with col2:
            # Campos adicionales
            if socio.get('fecha_nacimiento'):
                nueva_fecha_nacimiento = st.date_input(
                    "🎂 Fecha de Nacimiento", 
                    value=socio['fecha_nacimiento']
                )
            else:
                nueva_fecha_nacimiento = st.date_input("🎂 Fecha de Nacimiento")
            
            nuevo_genero = st.selectbox(
                "⚧️ Género",
                ["", "Femenino", "Masculino", "Otro", "Prefiero no decir"],
                index=["", "Femenino", "Masculino", "Otro", "Prefiero no decir"].index(socio.get('genero', ''))
            )
            
            nueva_ocupacion = st.text_input("💼 Ocupación", value=socio.get('ocupacion', ''))
            nuevo_email = st.text_input("📧 Email", value=socio.get('email', ''))
            
            # Obtener distritos actualizados
            distritos_opciones = obtener_distritos()
            distrito_actual = next((d for d in distritos_opciones if d[0] == socio['id_distrito']), None)
            indice_distrito = distritos_opciones.index(distrito_actual) if distrito_actual else 0
            
            nuevo_id_distrito = st.selectbox(
                "🗺️ Distrito", 
                options=[d[0] for d in distritos_opciones],
                format_func=lambda x: next((d[1] for d in distritos_opciones if d[0] == x), "Seleccionar"),
                index=indice_distrito
            )
        
        nuevas_observaciones = st.text_area(
            "📋 Observaciones", 
            value=socio.get('observaciones', '')
        )
        
        nuevo_activo = st.checkbox("✅ Socio activo", value=bool(socio.get('activo', True)))
        
        col1, col2 = st.columns(2)
        with col1:
            guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if guardar_cambios:
            if validar_socio(nuevo_nombre, nuevo_apellido, nuevo_telefono):
                if actualizar_socio(
                    id_socio, nuevo_nombre, nuevo_apellido, nuevo_telefono, nueva_direccion,
                    nuevo_id_grupo, nuevo_id_distrito, nueva_fecha_nacimiento, nuevo_genero,
                    nueva_ocupacion, nuevo_email, nuevas_observaciones, nuevo_activo
                ):
                    st.success("✅ Socio actualizado exitosamente")
                    # Limpiar estado de edición
                    st.session_state[f'editar_socio_{id_socio}'] = False
                    st.rerun()
        
        if cancelar:
            st.session_state[f'editar_socio_{id_socio}'] = False
            st.rerun()

def actualizar_socio(id_socio, nombre, apellido, telefono, direccion, id_grupo, id_distrito,
                    fecha_nacimiento=None, genero="", ocupacion="", email="", observaciones="", activo=True):
    """Actualizar socio en la base de datos"""
    
    query = """
        UPDATE socios 
        SET nombre = %s, apellido = %s, telefono = %s, direccion = %s, 
            id_grupo = %s, id_distrito = %s, fecha_nacimiento = %s, 
            genero = %s, ocupacion = %s, email = %s, observaciones = %s, activo = %s
        WHERE id_socio = %s
    """
    
    params = (
        str(nombre), str(apellido), str(telefono), str(direccion),
        int(id_grupo), int(id_distrito), fecha_nacimiento,
        str(genero), str(ocupacion), str(email), str(observaciones), bool(activo),
        int(id_socio)
    )
    
    try:
        return ejecutar_comando(query, params)
    except Exception as e:
        st.error(f"❌ Error al actualizar socio: {e}")
        return False

def ver_detalles_socio(id_socio):
    """Ver detalles completos de un socio - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener información completa del socio
    socio_info = ejecutar_consulta("""
        SELECT s.*, g.nombre_grupo, d.nombre_distrito
        FROM socios s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        JOIN distrito d ON s.id_distrito = d.id_distrito
        WHERE s.id_socio = %s
    """, (id_socio,))
    
    if not socio_info:
        st.error("❌ Socio no encontrado")
        return
    
    socio = socio_info[0]
    
    st.subheader(f"👤 Detalles del Socio: {socio['nombre']} {socio['apellido']}")
    
    # Información personal
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Información Personal")
        st.write(f"**Nombre completo:** {socio['nombre']} {socio['apellido']}")
        st.write(f"**Teléfono:** {socio['telefono']}")
        st.write(f"**Dirección:** {socio['direccion']}")
        
        if socio.get('email'):
            st.write(f"**Email:** {socio['email']}")
        
        if socio.get('fecha_nacimiento'):
            edad = calcular_edad(socio['fecha_nacimiento'])
            st.write(f"**Fecha de nacimiento:** {socio['fecha_nacimiento'].strftime('%d/%m/%Y')}")
            st.write(f"**Edad:** {edad} años")
        
        if socio.get('genero'):
            st.write(f"**Género:** {socio['genero']}")
        
        if socio.get('ocupacion'):
            st.write(f"**Ocupación:** {socio['ocupacion']}")
    
    with col2:
        st.markdown("### 🏢 Información del Grupo")
        st.write(f"**Grupo:** {socio['nombre_grupo']}")
        st.write(f"**Distrito:** {socio['nombre_distrito']}")
        st.write(f"**Fecha de registro:** {socio['fecha_registro'].strftime('%d/%m/%Y')}")
        st.write(f"**Estado:** {'✅ Activo' if socio.get('activo', True) else '❌ Inactivo'}")
        
        if socio.get('observaciones'):
            st.markdown("### 📝 Observaciones")
            st.write(socio['observaciones'])
    
    # Información financiera
    st.markdown("### 💰 Información Financiera")
    
    col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
    
    with col_fin1:
        # Obtener saldo de ahorro
        saldo_ahorro = obtener_saldo_ahorro_socio(id_socio)
        st.metric("💰 Ahorro Actual", f"${saldo_ahorro:,.2f}")
    
    with col_fin2:
        # Obtener préstamos activos
        prestamos_activos = obtener_prestamos_activos_socio(id_socio)
        st.metric("🏦 Préstamos Activos", prestamos_activos)
    
    with col_fin3:
        # Obtener total pagado en préstamos
        total_pagado = obtener_total_pagado_socio(id_socio)
        st.metric("💵 Total Pagado", f"${total_pagado:,.2f}")
    
    with col_fin4:
        # Obtener multas pendientes
        multas_pendientes = obtener_multas_pendientes_socio(id_socio)
        st.metric("⚠️ Multas Pendientes", f"${multas_pendientes:,.2f}")
    
    # Historial de asistencia
    st.markdown("### 📅 Historial de Asistencia Reciente")
    
    asistencia_reciente = obtener_asistencia_reciente_socio(id_socio, 5)
    
    if asistencia_reciente:
        for asistencia in asistencia_reciente:
            col_asist1, col_asist2 = st.columns([3, 1])
            with col_asist1:
                st.write(f"**Reunión del {asistencia['fecha_sesion'].strftime('%d/%m/%Y')}**")
            with col_asist2:
                if asistencia['presencial']:
                    st.success("✅ Presente")
                else:
                    st.error("❌ Ausente")
                    if asistencia.get('justificacion_ausencia'):
                        st.write(f"*Justificación: {asistencia['justificacion_ausencia']}*")
    else:
        st.info("ℹ️ No hay registro de asistencia reciente")
    
    # Botón para cerrar detalles
    if st.button("⬅️ Volver a la lista"):
        st.session_state[f'detalles_socio_{id_socio}'] = False
        st.rerun()

def eliminar_socio(id_socio, nombre_completo):
    """Eliminar socio - FUNCIÓN IMPLEMENTADA"""
    
    st.warning(f"⚠️ ¿Está seguro de que desea eliminar al socio **{nombre_completo}**?")
    
    # Verificar si el socio tiene registros financieros
    tiene_ahorro = obtener_saldo_ahorro_socio(id_socio) > 0
    tiene_prestamos = obtener_prestamos_activos_socio(id_socio) > 0
    tiene_multas = obtener_multas_pendientes_socio(id_socio) > 0
    
    if tiene_ahorro or tiene_prestamos or tiene_multas:
        st.error("❌ No se puede eliminar el socio porque tiene registros financieros activos:")
        
        if tiene_ahorro:
            st.write(f"   • Tiene ahorros por: ${obtener_saldo_ahorro_socio(id_socio):,.2f}")
        if tiene_prestamos:
            st.write(f"   • Tiene {obtener_prestamos_activos_socio(id_socio)} préstamo(s) activo(s)")
        if tiene_multas:
            st.write(f"   • Tiene multas pendientes por: ${obtener_multas_pendientes_socio(id_socio):,.2f}")
        
        st.info("💡 **Sugerencia:** En lugar de eliminar, marque al socio como inactivo.")
        
        if st.button("🔒 Marcar como Inactivo", key=f"inactivar_{id_socio}"):
            if actualizar_estado_socio(id_socio, False):
                st.success("✅ Socio marcado como inactivo")
                st.session_state[f'eliminar_socio_{id_socio}'] = False
                st.rerun()
        
        if st.button("❌ Cancelar Eliminación", key=f"cancel_eliminar_{id_socio}"):
            st.session_state[f'eliminar_socio_{id_socio}'] = False
            st.rerun()
        
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Sí, eliminar", key=f"confirm_eliminar_{id_socio}"):
            if ejecutar_comando("DELETE FROM socios WHERE id_socio = %s", (id_socio,)):
                st.success("✅ Socio eliminado exitosamente")
                st.session_state[f'eliminar_socio_{id_socio}'] = False
                st.rerun()
            else:
                st.error("❌ Error al eliminar el socio")
    
    with col2:
        if st.button("❌ Cancelar", key=f"cancel_{id_socio}"):
            st.session_state[f'eliminar_socio_{id_socio}'] = False
            st.rerun()

# =============================================================================
# FUNCIONES AUXILIARES (TODAS IMPLEMENTADAS)
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

def calcular_edad(fecha_nacimiento):
    """Calcular edad a partir de la fecha de nacimiento"""
    if not fecha_nacimiento:
        return 0
    hoy = datetime.now().date()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def obtener_saldo_ahorro_socio(id_socio):
    """Obtener saldo actual de ahorro del socio"""
    query = """
        SELECT saldo_final 
        FROM ahorro_detalle 
        WHERE id_socio = %s 
        ORDER BY id_ahorrodetalle DESC 
        LIMIT 1
    """
    resultado = ejecutar_consulta(query, (id_socio,))
    return resultado[0]['saldo_final'] if resultado else 0

def obtener_prestamos_activos_socio(id_socio):
    """Obtener número de préstamos activos del socio"""
    query = """
        SELECT COUNT(*) as total 
        FROM prestamo 
        WHERE id_socio = %s AND id_estado_prestamo IN (2, 5)
    """
    resultado = ejecutar_consulta(query, (id_socio,))
    return resultado[0]['total'] if resultado else 0

def obtener_total_pagado_socio(id_socio):
    """Obtener total pagado en préstamos por el socio"""
    query = """
        SELECT COALESCE(SUM(total_pagado), 0) as total
        FROM `detalle de pagos` 
        WHERE id_prestamo IN (SELECT id_prestamo FROM prestamo WHERE id_socio = %s)
    """
    resultado = ejecutar_consulta(query, (id_socio,))
    return float(resultado[0]['total']) if resultado else 0

def obtener_multas_pendientes_socio(id_socio):
    """Obtener total de multas pendientes del socio"""
    query = """
        SELECT COALESCE(SUM(monto_a_pagar - monto_pagado), 0) as total
        FROM multa 
        WHERE id_socio = %s AND (monto_a_pagar - monto_pagado) > 0
    """
    resultado = ejecutar_consulta(query, (id_socio,))
    return float(resultado[0]['total']) if resultado else 0

def obtener_asistencia_reciente_socio(id_socio, limite=5):
    """Obtener historial reciente de asistencia del socio"""
    query = """
        SELECT a.presencial, a.justificacion_ausencia, s.fecha_sesion
        FROM asistencia a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE a.id_socio = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT %s
    """
    return ejecutar_consulta(query, (id_socio, limite))

def actualizar_estado_socio(id_socio, activo):
    """Actualizar estado activo/inactivo del socio"""
    query = "UPDATE socios SET activo = %s WHERE id_socio = %s"
    return ejecutar_comando(query, (activo, id_socio))

def exportar_socios_csv(socios):
    """Exportar lista de socios a archivo CSV"""
    
    # Preparar datos para CSV
    datos_exportar = []
    for socio in socios:
        datos_exportar.append({
            'ID': socio['id_socio'],
            'Nombre': socio['nombre'],
            'Apellido': socio['apellido'],
            'Teléfono': socio['telefono'],
            'Dirección': socio['direccion'],
            'Email': socio.get('email', ''),
            'Grupo': socio['nombre_grupo'],
            'Distrito': socio['nombre_distrito'],
            'Ocupación': socio.get('ocupacion', ''),
            'Género': socio.get('genero', ''),
            'Fecha Registro': socio['fecha_registro'].strftime('%d/%m/%Y'),
            'Estado': 'Activo' if socio.get('activo', True) else 'Inactivo'
        })
    
    df = pd.DataFrame(datos_exportar)
    csv = df.to_csv(index=False, encoding='utf-8')
    
    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M')
    
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"socios_exportacion_{fecha_actual}.csv",
        mime="text/csv"
    )