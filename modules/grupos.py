import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime
import pandas as pd

def modulo_conformacion_grupo():
    """Módulo principal para la conformación de grupos"""
    
    st.header("🏢 Conformación del Grupo")
    
    tab1, tab2, tab3 = st.tabs(["📋 Registro de Grupo", "👥 Directiva", "⚙️ Reglas Básicas"])
    
    with tab1:
        registro_grupo()
    
    with tab2:
        gestion_directiva()
    
    with tab3:
        configuracion_reglas()

def registro_grupo():
    """Registro de nuevo grupo"""
    
    st.subheader("Crear Nuevo Grupo")
    
    with st.form("form_nuevo_grupo"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_grupo = st.text_input("🏷️ Nombre del Grupo", placeholder="Ej: Grupo Solidaridad 2024")
            
            # Obtener solo el ID de los selectboxes
            distritos_opciones = obtener_distritos()
            id_distrito = st.selectbox("🗺️ Distrito", options=[d[0] for d in distritos_opciones], 
                                     format_func=lambda x: next((d[1] for d in distritos_opciones if d[0] == x), "Seleccionar"))
            
            fecha_creacion = st.date_input("📅 Fecha de Inicio", datetime.now())
            
            frecuencias_opciones = obtener_frecuencias()
            id_frecuencia = st.selectbox("🔄 Frecuencia de Reuniones", options=[f[0] for f in frecuencias_opciones],
                                       format_func=lambda x: next((f[1] for f in frecuencias_opciones if f[0] == x), "Seleccionar"))
        
        with col2:
            hora_reunion = st.time_input("⏰ Hora de Reunión", value=datetime.strptime("14:00", "%H:%M").time())
            lugar_reunion = st.text_input("📍 Lugar de Reunión", placeholder="Ej: Casa de la Presidenta")
            dia_reunion = st.selectbox("📅 Día de Reunión", 
                                     ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
            
            promotores_opciones = obtener_promotores()
            id_promotor = st.selectbox("👩‍💼 Promotor/a Asignado", options=[p[0] for p in promotores_opciones],
                                     format_func=lambda x: next((p[1] for p in promotores_opciones if p[0] == x), "Seleccionar"))
        
        meta_social = st.text_area("🎯 Meta Social del Grupo", 
                                 placeholder="Ej: Mejorar las condiciones de vida de las familias mediante el ahorro...")
        otras_reglas = st.text_area("📜 Otras Reglas del Grupo", 
                                  placeholder="Reglas adicionales acordadas por el grupo...")
        
        submitted = st.form_submit_button("💾 Crear Grupo")
        
        if submitted:
            if validar_grupo(nombre_grupo, lugar_reunion):
                id_grupo = crear_grupo(
                    nombre_grupo, id_distrito, fecha_creacion, id_promotor,
                    id_frecuencia, hora_reunion, lugar_reunion, dia_reunion,
                    meta_social, otras_reglas
                )
                if id_grupo:
                    st.success(f"✅ Grupo '{nombre_grupo}' creado exitosamente (ID: {id_grupo})")
                    st.info("🎉 Ahora puede asignar la directiva y configurar las reglas del grupo.")

def validar_grupo(nombre, lugar):
    """Validar datos del grupo"""
    if not nombre.strip():
        st.error("❌ El nombre del grupo es obligatorio")
        return False
    if not lugar.strip():
        st.error("❌ El lugar de reunión es obligatorio")
        return False
    return True

def crear_grupo(nombre, distrito, fecha, promotor, frecuencia, hora, lugar, dia, meta, reglas):
    """Crear nuevo grupo en la base de datos"""
    
    # CONVERSIÓN EXPLÍCITA DE TIPOS DE DATOS
    try:
        # Convertir objetos date/datetime a string
        if hasattr(fecha, 'strftime'):
            fecha = fecha.strftime('%Y-%m-%d')
        
        # Convertir objetos time a string
        if hasattr(hora, 'strftime'):
            hora = hora.strftime('%H:%M:%S')
        
        # Asegurar que los IDs sean enteros
        distrito = int(distrito) if distrito else None
        promotor = int(promotor) if promotor else None
        frecuencia = int(frecuencia) if frecuencia else None
        
        # Asegurar que textos sean strings (incluso si son None)
        nombre = str(nombre) if nombre is not None else ""
        lugar = str(lugar) if lugar is not None else ""
        dia = str(dia) if dia is not None else ""
        meta = str(meta) if meta is not None else ""
        reglas = str(reglas) if reglas is not None else ""
        
    except (ValueError, TypeError) as e:
        st.error(f"❌ Error en conversión de datos: {e}")
        return False
    
    query = """
        INSERT INTO grupos (nombre_grupo, id_distrito, fecha_creacion, id_promotor, 
                          id_frecuencia, hora_reunion, lugar_reunion, dia_reunion, 
                          meta_social, `otras_reglas`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (nombre, distrito, fecha, promotor, frecuencia, hora, lugar, dia, meta, reglas)
    
    return ejecutar_comando(query, params)

def gestion_directiva():
    """Gestión de la directiva del grupo"""
    
    st.subheader("👥 Asignación de Directiva")
    
    # Seleccionar grupo
    grupos = obtener_grupos_con_nombres()
    if not grupos:
        st.warning("📝 Primero debe crear un grupo en la pestaña 'Registro de Grupo'")
        return
    
    id_grupo = st.selectbox("Seleccionar Grupo", grupos, key="select_grupo_directiva")
    
    if id_grupo:
        # Mostrar directiva actual
        st.markdown("### Directiva Actual")
        mostrar_directiva_actual(id_grupo)
        
        # Formulario para asignar nueva directiva
        st.markdown("### Asignar Nuevo Miembro a Directiva")
        
        with st.form("form_directiva"):
            col1, col2 = st.columns(2)
            
            with col1:
                socios_grupo = obtener_socios_por_grupo(id_grupo)
                if not socios_grupo:
                    st.warning("No hay socios en este grupo. Primero registre socios.")
                    return
                
                id_socio = st.selectbox("👤 Socio", socios_grupo)
                id_rol = st.selectbox("🎯 Rol", obtener_roles_directiva())
            
            with col2:
                fecha_inicio = st.date_input("📅 Fecha de Inicio", datetime.now())
                fecha_fin = st.date_input("📅 Fecha de Fin", 
                                        datetime.now().replace(year=datetime.now().year + 1))
                id_estado = st.selectbox("📊 Estado", obtener_estados_directiva())
            
            submitted = st.form_submit_button("➕ Asignar a Directiva")
            
            if submitted:
                if asignar_directiva(id_socio, id_grupo, id_rol, fecha_inicio, fecha_fin, id_estado):
                    st.success("✅ Miembro asignado a directiva exitosamente")
                    st.rerun()

def configuracion_reglas():
    """Configuración de reglas del grupo"""
    
    st.subheader("⚙️ Configuración de Reglas del Grupo")
    
    grupos = obtener_grupos_con_nombres()
    if not grupos:
        st.warning("📝 Primero debe crear un grupo en la pestaña 'Registro de Grupo'")
        return
    
    id_grupo = st.selectbox("Seleccionar Grupo", grupos, key="select_grupo_reglas")
    
    if id_grupo:
        # Verificar si ya existen reglas
        reglas_actuales = obtener_reglas_grupo(id_grupo)
        
        with st.form("form_reglas"):
            st.markdown("### Parámetros Financieros")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cantidad_multa = st.number_input("💰 Monto de Multa", min_value=0.0, value=20.0, step=5.0)
                interes = st.number_input("📈 Tasa de Interés (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
            
            with col2:
                monto_max_prestamo = st.number_input("💵 Monto Máximo Préstamo", min_value=0.0, value=1000.0, step=100.0)
                un_prestamo_alavez = st.checkbox("¿Solo un préstamo a la vez?", value=True)
            
            with col3:
                fecha_inicio_ciclo = st.date_input("🔄 Inicio del Ciclo", datetime.now())
                duracion_ciclo = st.selectbox("⏱️ Duración del Ciclo (meses)", [6, 12], index=1)
            
            fecha_fin_ciclo = fecha_inicio_ciclo.replace(
                year=fecha_inicio_ciclo.year + (fecha_inicio_ciclo.month + duracion_ciclo - 1) // 12,
                month=(fecha_inicio_ciclo.month + duracion_ciclo - 1) % 12 + 1
            )
            
            st.info(f"📅 El ciclo finalizará el: {fecha_fin_ciclo.strftime('%d/%m/%Y')}")
            
            submitted = st.form_submit_button("💾 Guardar Reglas")
            
            if submitted:
                if guardar_reglas_grupo(id_grupo, cantidad_multa, interes, monto_max_prestamo, 
                                      un_prestamo_alavez, fecha_inicio_ciclo, fecha_fin_ciclo, duracion_ciclo):
                    st.success("✅ Reglas del grupo guardadas exitosamente")

# =============================================================================
# FUNCIONES AUXILIARES - TODAS IMPLEMENTADAS
# =============================================================================

def obtener_distritos():
    """Obtener lista de distritos"""
    resultado = ejecutar_consulta("SELECT id_distrito, nombre_distrito FROM distrito")
    if resultado:
        return [(row['id_distrito'], row['nombre_distrito']) for row in resultado]
    return []

def obtener_frecuencias():
    """Obtener lista de frecuencias"""
    resultado = ejecutar_consulta("SELECT `id_frecuencia`, `tipo_frecuencia` FROM `frecuencia`")
    if resultado:
        return [(row['id_frecuencia'], row['tipo_frecuencia']) for row in resultado]
    return []

def obtener_promotores():
    """Obtener lista de promotores"""
    resultado = ejecutar_consulta("SELECT `id_promotor`, CONCAT(`nombre`, ' ', `apellido`) as nombre FROM `promotores`")
    if resultado:
        return [(row['id_promotor'], row['nombre']) for row in resultado]
    return [(1, "Promotor Demo")]

def obtener_grupos_con_nombres():
    """Obtener grupos con formato para selectbox"""
    resultado = ejecutar_consulta("SELECT id_grupo, nombre_grupo FROM grupos")
    if resultado:
        return [(row['id_grupo'], row['nombre_grupo']) for row in resultado]
    return []

def obtener_roles_directiva():
    """Obtener roles de directiva"""
    resultado = ejecutar_consulta("SELECT id_rol, tipo_rol FROM roles")
    if resultado:
        return [(row['id_rol'], row['tipo_rol']) for row in resultado]
    return []

def obtener_estados_directiva():
    """Obtener estados de directiva"""
    resultado = ejecutar_consulta("SELECT id_estadodirectiva, estado FROM estado_directiva")
    if resultado:
        return [(row['id_estadodirectiva'], row['estado']) for row in resultado]
    return []

def obtener_socios_por_grupo(id_grupo):
    """Obtener socios de un grupo específico"""
    query = """
        SELECT id_socio, CONCAT(nombre, ' ', apellido) as nombre 
        FROM socios 
        WHERE id_grupo = %s
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    if resultado:
        return [(row['id_socio'], row['nombre']) for row in resultado]
    return []

def mostrar_directiva_actual(id_grupo):
    """Mostrar la directiva actual del grupo - FUNCIÓN COMPLETAMENTE IMPLEMENTADA"""
    query = """
        SELECT d.id_directiva, s.nombre, s.apellido, r.tipo_rol, ed.estado,
               d.fecha_inicio, d.fecha_fin, d.id_socio, d.id_rol
        FROM directiva_de_grupo d
        JOIN socios s ON d.id_socio = s.id_socio
        JOIN roles r ON d.id_rol = r.id_rol
        JOIN estado_directiva ed ON d.id_estado_directiva = ed.id_estadodirectiva
        WHERE d.id_grupo = %s
        ORDER BY r.id_rol
    """
    
    directiva = ejecutar_consulta(query, (id_grupo,))
    
    if directiva:
        for miembro in directiva:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.write(f"**{miembro['tipo_rol']}:** {miembro['nombre']} {miembro['apellido']}")
                with col2:
                    st.write(f"**Inicio:** {miembro['fecha_inicio'].strftime('%d/%m/%Y')}")
                with col3:
                    st.write(f"**Fin:** {miembro['fecha_fin'].strftime('%d/%m/%Y')}")
                    st.write(f"**Estado:** {miembro['estado']}")
                with col4:
                    # Botones de acción
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ Editar", key=f"editar_{miembro['id_directiva']}"):
                            st.session_state[f'editar_directiva_{miembro["id_directiva"]}'] = True
                    
                    with col_del:
                        if st.button("🗑️ Eliminar", key=f"eliminar_{miembro['id_directiva']}"):
                            st.session_state[f'eliminar_directiva_{miembro["id_directiva"]}'] = True
            
            # Editar directiva si se hizo clic en editar
            if f'editar_directiva_{miembro["id_directiva"]}' in st.session_state and st.session_state[f'editar_directiva_{miembro["id_directiva"]}']:
                editar_miembro_directiva(miembro['id_directiva'], id_grupo)
            
            # Eliminar directiva si se hizo clic en eliminar
            if f'eliminar_directiva_{miembro["id_directiva"]}' in st.session_state and st.session_state[f'eliminar_directiva_{miembro["id_directiva"]}']:
                eliminar_miembro_directiva(miembro['id_directiva'], miembro['nombre'] + " " + miembro['apellido'], miembro['tipo_rol'])
            
            st.markdown("---")
    else:
        st.info("ℹ️ No hay directiva asignada para este grupo")

def editar_miembro_directiva(id_directiva, id_grupo):
    """Editar miembro de la directiva - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener datos actuales del miembro
    miembro_data = ejecutar_consulta("""
        SELECT d.*, s.nombre, s.apellido 
        FROM directiva_de_grupo d
        JOIN socios s ON d.id_socio = s.id_socio
        WHERE d.id_directiva = %s
    """, (id_directiva,))
    
    if not miembro_data:
        st.error("❌ Miembro no encontrado")
        return
    
    miembro = miembro_data[0]
    
    st.subheader(f"✏️ Editar Miembro de Directiva: {miembro['nombre']} {miembro['apellido']}")
    
    with st.form(f"form_editar_directiva_{id_directiva}"):
        # Obtener opciones actualizadas
        socios_grupo = obtener_socios_por_grupo(id_grupo)
        roles = obtener_roles_directiva()
        estados = obtener_estados_directiva()
        
        # Encontrar índices actuales
        socio_actual_idx = next((i for i, (id_soc, _) in enumerate(socios_grupo) if id_soc == miembro['id_socio']), 0)
        rol_actual_idx = next((i for i, (id_rol, _) in enumerate(roles) if id_rol == miembro['id_rol']), 0)
        estado_actual_idx = next((i for i, (id_est, _) in enumerate(estados) if id_est == miembro['id_estado_directiva']), 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_id_socio = st.selectbox(
                "👤 Socio", 
                options=[s[0] for s in socios_grupo],
                format_func=lambda x: next((s[1] for s in socios_grupo if s[0] == x), "Seleccionar"),
                index=socio_actual_idx,
                key=f"socio_edit_{id_directiva}"
            )
            
            nuevo_id_rol = st.selectbox(
                "🎯 Rol",
                options=[r[0] for r in roles],
                format_func=lambda x: next((r[1] for r in roles if r[0] == x), "Seleccionar"),
                index=rol_actual_idx,
                key=f"rol_edit_{id_directiva}"
            )
        
        with col2:
            nueva_fecha_inicio = st.date_input(
                "📅 Fecha de Inicio", 
                value=miembro['fecha_inicio'],
                key=f"fecha_ini_edit_{id_directiva}"
            )
            
            nueva_fecha_fin = st.date_input(
                "📅 Fecha de Fin", 
                value=miembro['fecha_fin'],
                key=f"fecha_fin_edit_{id_directiva}"
            )
            
            nuevo_id_estado = st.selectbox(
                "📊 Estado",
                options=[e[0] for e in estados],
                format_func=lambda x: next((e[1] for e in estados if e[0] == x), "Seleccionar"),
                index=estado_actual_idx,
                key=f"estado_edit_{id_directiva}"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if guardar_cambios:
            if actualizar_miembro_directiva(id_directiva, nuevo_id_socio, nuevo_id_rol, nueva_fecha_inicio, nueva_fecha_fin, nuevo_id_estado):
                st.success("✅ Miembro de directiva actualizado exitosamente")
                # Limpiar estado de edición
                st.session_state[f'editar_directiva_{id_directiva}'] = False
                st.rerun()
        
        if cancelar:
            st.session_state[f'editar_directiva_{id_directiva}'] = False
            st.rerun()

def actualizar_miembro_directiva(id_directiva, id_socio, id_rol, fecha_inicio, fecha_fin, id_estado):
    """Actualizar miembro de directiva en la base de datos"""
    query = """
        UPDATE directiva_de_grupo 
        SET id_socio = %s, id_rol = %s, fecha_inicio = %s, fecha_fin = %s, id_estado_directiva = %s
        WHERE id_directiva = %s
    """
    
    params = (
        int(id_socio), 
        int(id_rol), 
        fecha_inicio, 
        fecha_fin, 
        int(id_estado), 
        int(id_directiva)
    )
    
    try:
        return ejecutar_comando(query, params)
    except Exception as e:
        st.error(f"❌ Error al actualizar miembro de directiva: {e}")
        return False

def eliminar_miembro_directiva(id_directiva, nombre_miembro, rol):
    """Eliminar miembro de la directiva - FUNCIÓN IMPLEMENTADA"""
    
    st.warning(f"⚠️ ¿Está seguro de que desea eliminar a **{nombre_miembro}** del rol de **{rol}**?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Sí, eliminar", key=f"confirm_eliminar_{id_directiva}"):
            if ejecutar_comando("DELETE FROM directiva_de_grupo WHERE id_directiva = %s", (id_directiva,)):
                st.success("✅ Miembro eliminado de la directiva exitosamente")
                # Limpiar estado de eliminación
                st.session_state[f'eliminar_directiva_{id_directiva}'] = False
                st.rerun()
            else:
                st.error("❌ Error al eliminar el miembro de la directiva")
    
    with col2:
        if st.button("❌ Cancelar", key=f"cancel_eliminar_{id_directiva}"):
            st.session_state[f'eliminar_directiva_{id_directiva}'] = False
            st.rerun()

def asignar_directiva(id_socio, id_grupo, id_rol, fecha_inicio, fecha_fin, id_estado):
    """Asignar miembro a directiva"""
    
    # Verificar si el socio ya tiene un rol activo en la directiva
    directiva_existente = ejecutar_consulta("""
        SELECT id_directiva FROM directiva_de_grupo 
        WHERE id_socio = %s AND id_grupo = %s AND id_estado_directiva IN (
            SELECT id_estadodirectiva FROM estado_directiva WHERE estado = 'Activo'
        )
    """, (id_socio, id_grupo))
    
    if directiva_existente:
        st.error("❌ Este socio ya tiene un rol activo en la directiva. Edite el rol existente en lugar de crear uno nuevo.")
        return False
    
    query = """
        INSERT INTO directiva_de_grupo (id_socio, id_grupo, id_rol, fecha_inicio, fecha_fin, id_estado_directiva)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    params = (
        int(id_socio), 
        int(id_grupo), 
        int(id_rol), 
        fecha_inicio, 
        fecha_fin, 
        int(id_estado)
    )
    
    try:
        return ejecutar_comando(query, params)
    except Exception as e:
        st.error(f"❌ Error al asignar directiva: {e}")
        return False

def obtener_reglas_grupo(id_grupo):
    """Obtener reglas actuales del grupo"""
    resultado = ejecutar_consulta("SELECT * FROM reglas_del_grupo WHERE id_grupo = %s", (id_grupo,))
    if resultado:
        return resultado[0]  # Devolver el primer registro
    return None

def guardar_reglas_grupo(id_grupo, cantidad_multa, interes, monto_max_prestamo, 
                        un_prestamo_alavez, fecha_inicio_ciclo, fecha_fin_ciclo, duracion_ciclo):
    """Guardar reglas del grupo - FUNCIÓN MEJORADA"""
    
    # Verificar si ya existen reglas para actualizar o insertar
    reglas_existentes = obtener_reglas_grupo(id_grupo)
    
    try:
        # Convertir boolean a entero para MySQL
        un_prestamo_alavez_int = 1 if un_prestamo_alavez else 0
        
        if reglas_existentes:
            query = """
                UPDATE reglas_del_grupo 
                SET cantidad_multa = %s, interes = %s, montomax_prestamo = %s, 
                    unprestamo_alavez = %s, fecha_inicio_ciclo = %s, 
                    fecha_fin_ciclo = %s, duracion_ciclo_meses = %s
                WHERE id_grupo = %s
            """
            params = (
                float(cantidad_multa), 
                float(interes), 
                float(monto_max_prestamo), 
                un_prestamo_alavez_int,
                fecha_inicio_ciclo, 
                fecha_fin_ciclo, 
                int(duracion_ciclo), 
                int(id_grupo)
            )
        else:
            query = """
                INSERT INTO reglas_del_grupo (id_grupo, cantidad_multa, interes, montomax_prestamo,
                                            unprestamo_alavez, fecha_inicio_ciclo, fecha_fin_ciclo,
                                            duracion_ciclo_meses)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                int(id_grupo), 
                float(cantidad_multa), 
                float(interes), 
                float(monto_max_prestamo), 
                un_prestamo_alavez_int,
                fecha_inicio_ciclo, 
                fecha_fin_ciclo, 
                int(duracion_ciclo)
            )
        
        return ejecutar_comando(query, params)
        
    except Exception as e:
        st.error(f"❌ Error al guardar reglas del grupo: {e}")
        return False

# =============================================================================
# FUNCIONES ADICIONALES PARA MEJORAR LA GESTIÓN DE GRUPOS
# =============================================================================

def generar_reporte_directiva(id_grupo):
    """Generar reporte de la directiva actual del grupo"""
    
    directiva = ejecutar_consulta("""
        SELECT s.nombre, s.apellido, r.tipo_rol, ed.estado,
               d.fecha_inicio, d.fecha_fin
        FROM directiva_de_grupo d
        JOIN socios s ON d.id_socio = s.id_socio
        JOIN roles r ON d.id_rol = r.id_rol
        JOIN estado_directiva ed ON d.id_estado_directiva = ed.id_estadodirectiva
        WHERE d.id_grupo = %s
        ORDER BY r.id_rol
    """, (id_grupo,))
    
    if directiva:
        st.subheader("📊 Reporte de Directiva")
        
        # Crear DataFrame para mejor visualización
        df = pd.DataFrame(directiva)
        st.dataframe(df, use_container_width=True)
        
        # Opción de exportar
        csv = df.to_csv(index=False)
        st.download_button(
            label="📤 Exportar Reporte a CSV",
            data=csv,
            file_name=f"directiva_grupo_{id_grupo}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ No hay directiva para generar reporte")

def mostrar_resumen_grupo(id_grupo):
    """Mostrar resumen completo del grupo"""
    
    datos_grupo = ejecutar_consulta("""
        SELECT g.*, d.nombre_distrito, p.nombre as nombre_promotor, p.apellido as apellido_promotor,
               f.tipo_frecuencia
        FROM grupos g
        LEFT JOIN distrito d ON g.id_distrito = d.id_distrito
        LEFT JOIN promotores p ON g.id_promotor = p.id_promotor
        LEFT JOIN frecuencia f ON g.id_frecuencia = f.id_frecuencia
        WHERE g.id_grupo = %s
    """, (id_grupo,))
    
    if datos_grupo:
        grupo = datos_grupo[0]
        
        st.subheader(f"📋 Resumen del Grupo: {grupo['nombre_grupo']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**🗺️ Distrito:** {grupo['nombre_distrito']}")
            st.write(f"**📅 Fecha de Creación:** {grupo['fecha_creacion'].strftime('%d/%m/%Y')}")
            st.write(f"**🔄 Frecuencia:** {grupo['tipo_frecuencia']}")
            st.write(f"**⏰ Hora de Reunión:** {grupo['hora_reunion']}")
        
        with col2:
            st.write(f"**📍 Lugar de Reunión:** {grupo['lugar_reunion']}")
            st.write(f"**📅 Día de Reunión:** {grupo['dia_reunion']}")
            st.write(f"**👩‍💼 Promotor:** {grupo['nombre_promotor']} {grupo['apellido_promotor']}")
        
        # Contar socios
        total_socios = ejecutar_consulta("SELECT COUNT(*) as total FROM socios WHERE id_grupo = %s", (id_grupo,))
        if total_socios:
            st.write(f"**👥 Total de Socios:** {total_socios[0]['total']}")
        
        # Mostrar meta social si existe
        if grupo['meta_social']:
            st.write(f"**🎯 Meta Social:** {grupo['meta_social']}")
        
        # Mostrar reglas adicionales si existen
        if grupo['otras_reglas']:
            with st.expander("📜 Otras Reglas del Grupo"):
                st.write(grupo['otras_reglas'])