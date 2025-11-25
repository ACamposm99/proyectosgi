import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime, timedelta

def modulo_supervision_grupos():
    """Módulo de supervisión de grupos para promotoras"""
    
    st.title("👁️ Supervisión de Grupos")
    
    # Verificar que el usuario sea una promotora
    if st.session_state.rol != "PROMOTORA":
        st.error("❌ No tiene permisos para acceder a esta sección")
        return
    
    # Obtener ID de la promotora
    id_promotora = obtener_id_promotora()
    if not id_promotora:
        st.error("❌ No se pudo identificar a la promotora")
        return
    
    # Verificar si se ha seleccionado un grupo para ver sus socios
    if 'grupo_seleccionado_socios' in st.session_state and st.session_state.grupo_seleccionado_socios:
        mostrar_socios_grupo(st.session_state.grupo_seleccionado_socios)
        return
    
    # Mostrar métricas rápidas
    mostrar_metricas_rapidas(id_promotora)
    
    # Mostrar grupos asignados
    mostrar_grupos_asignados(id_promotora)

def obtener_id_promotora():
    """Obtener el ID de la promotora desde la sesión o la base de datos"""
    
    if 'id_promotora' in st.session_state:
        return st.session_state.id_promotora
    
    # Buscar en la base de datos
    try:
        resultado = ejecutar_consulta(
            "SELECT id_promotor FROM promotores WHERE nombre = %s OR id_promotor IN (SELECT id_promotor FROM usuarios WHERE username = %s)",
            (st.session_state.usuario, st.session_state.usuario)
        )
        
        if resultado:
            st.session_state.id_promotora = resultado[0]['id_promotor']
            return st.session_state.id_promotora
        else:
            st.error("❌ No se encontró el perfil de promotora")
            return None
    except Exception as e:
        st.error(f"❌ Error al obtener ID de promotora: {str(e)}")
        return None

def mostrar_metricas_rapidas(id_promotora):
    """Mostrar métricas rápidas de supervisión"""
    
    st.subheader("📊 Métricas de Supervisión")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total de grupos
        total_grupos = ejecutar_consulta(
            "SELECT COUNT(*) as total FROM grupos WHERE id_promotor = %s AND estado = 'ACTIVO'",
            (id_promotora,)
        )
        st.metric("🏢 Grupos Activos", total_grupos[0]['total'] if total_grupos else 0)
    
    with col2:
        # Total de socios
        total_socios = ejecutar_consulta(
            "SELECT COUNT(*) as total FROM socios s JOIN grupos g ON s.id_grupo = g.id_grupo WHERE g.id_promotor = %s AND s.estado = 'ACTIVO'",
            (id_promotora,)
        )
        st.metric("👥 Total Socios", total_socios[0]['total'] if total_socios else 0)
    
    with col3:
        # Reuniones esta semana
        reuniones_semana = ejecutar_consulta(
            """SELECT COUNT(*) as total FROM sesion s 
               JOIN grupos g ON s.id_grupo = g.id_grupo 
               WHERE g.id_promotor = %s AND s.fecha_sesion >= %s""",
            (id_promotora, datetime.now().date() - timedelta(days=7))
        )
        st.metric("📅 Reuniones (7d)", reuniones_semana[0]['total'] if reuniones_semana else 0)
    
    with col4:
        # Préstamos pendientes de validación
        prestamos_pendientes = ejecutar_consulta(
            """SELECT COUNT(*) as total FROM prestamo p 
               JOIN grupos g ON p.id_grupo = g.id_grupo 
               WHERE g.id_promotor = %s AND p.id_estado_prestamo = 1""",  # PENDIENTE
            (id_promotora,)
        )
        st.metric("⏳ Préstamos por Validar", prestamos_pendientes[0]['total'] if prestamos_pendientes else 0)

def mostrar_grupos_asignados(id_promotora):
    """Mostrar los grupos asignados a la promotora con detalles"""
    
    st.subheader("🎯 Grupos Asignados")
    
    # Obtener grupos asignados
    grupos = ejecutar_consulta(
        """SELECT g.id_grupo, g.nombre_grupo, g.lugar_reunion, g.fecha_creacion, 
                  g.dia_reunion, g.hora_reunion, g.estado,
                  COUNT(s.id_socio) as total_socios,
                  d.nombre_distrito
           FROM grupos g 
           LEFT JOIN socios s ON g.id_grupo = s.id_grupo AND s.estado = 'ACTIVO'
           LEFT JOIN distrito d ON g.id_distrito = d.id_distrito
           WHERE g.id_promotor = %s
           GROUP BY g.id_grupo, g.nombre_grupo, g.lugar_reunion, g.fecha_creacion, 
                    g.dia_reunion, g.hora_reunion, g.estado, d.nombre_distrito
           ORDER BY g.nombre_grupo""",
        (id_promotora,)
    )
    
    if not grupos:
        st.info("ℹ️ No tienes grupos asignados para supervisar")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "ACTIVO", "INACTIVO"])
    
    with col2:
        buscar_nombre = st.text_input("Buscar por nombre:")
    
    # Aplicar filtros
    grupos_filtrados = grupos
    if filtro_estado != "Todos":
        grupos_filtrados = [g for g in grupos_filtrados if g['estado'] == filtro_estado]
    
    if buscar_nombre:
        grupos_filtrados = [g for g in grupos_filtrados if buscar_nombre.lower() in g['nombre_grupo'].lower()]
    
    st.metric("📊 Grupos Mostrados", len(grupos_filtrados))
    
    # Mostrar grupos
    for grupo in grupos_filtrados:
        with st.expander(f"🏢 {grupo['nombre_grupo']} - {grupo['total_socios']} socios - {grupo['estado']}"):
            mostrar_detalles_grupo(grupo)

def mostrar_detalles_grupo(grupo):
    """Mostrar detalles específicos de un grupo"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**📋 Información General:**")
        st.write(f"**Distrito:** {grupo['nombre_distrito']}")
        st.write(f"**Lugar reunión:** {grupo['lugar_reunion']}")
        st.write(f"**Fecha creación:** {grupo['fecha_creacion'].strftime('%d/%m/%Y')}")
        st.write(f"**Estado:** {grupo['estado']}")
    
    with col2:
        st.write("**📅 Reuniones:**")
        st.write(f"**Día:** {grupo['dia_reunion'] or 'No definido'}")
        st.write(f"**Hora:** {grupo['hora_reunion'] or 'No definido'}")
        
        # Última reunión
        ultima_reunion = ejecutar_consulta(
            "SELECT fecha_sesion FROM sesion WHERE id_grupo = %s ORDER BY fecha_sesion DESC LIMIT 1",
            (grupo['id_grupo'],)
        )
        if ultima_reunion:
            st.write(f"**Última reunión:** {ultima_reunion[0]['fecha_sesion'].strftime('%d/%m/%Y')}")
        else:
            st.write("**Última reunión:** Sin reuniones")
    
    with col3:
        st.write("**💰 Estado Financiero:**")
        
        # Ahorro total del grupo
        ahorro_total = ejecutar_consulta("""
            SELECT COALESCE(SUM(ad.saldo_final), 0) as total 
            FROM ahorro_detalle ad
            WHERE ad.id_socio IN (SELECT id_socio FROM socios WHERE id_grupo = %s)
            AND ad.id_ahorro_detalle IN (
                SELECT MAX(ad2.id_ahorro_detalle)
                FROM ahorro_detalle ad2
                WHERE ad2.id_socio = ad.id_socio
                GROUP BY ad2.id_socio
            )
        """, (grupo['id_grupo'],))
        
        st.write(f"**Ahorro total:** ${ahorro_total[0]['total']:,.2f}" if ahorro_total else "**Ahorro total:** $0.00")
        
        # Préstamos activos
        prestamos_activos = ejecutar_consulta(
            "SELECT COUNT(*) as total FROM prestamo WHERE id_grupo = %s AND id_estado_prestamo IN (4, 6)",  # VIGENTE o MORA
            (grupo['id_grupo'],)
        )
        st.write(f"**Préstamos activos:** {prestamos_activos[0]['total'] if prestamos_activos else 0}")
    
    # Acciones rápidas
    st.markdown("---")
    st.write("**🚀 Acciones Rápidas:**")
    
    col_act1, col_act2, col_act3 = st.columns(3)
    
    
    with col_act2:
        if st.button("👥 Ver Socios", key=f"socios_{grupo['id_grupo']}"):
            # Guardar el grupo seleccionado en la sesión
            st.session_state.grupo_seleccionado_socios = grupo['id_grupo']
            st.session_state.nombre_grupo_seleccionado = grupo['nombre_grupo']
            st.rerun()
    
    
def mostrar_socios_grupo(id_grupo):
    """Mostrar los socios de un grupo específico"""
    
    # Obtener información del grupo
    grupo_info = ejecutar_consulta(
        "SELECT nombre_grupo FROM grupos WHERE id_grupo = %s",
        (id_grupo,)
    )
    
    if not grupo_info:
        st.error("❌ Grupo no encontrado")
        return
    
    nombre_grupo = grupo_info[0]['nombre_grupo']
    
    st.subheader(f"👥 Socios del Grupo: {nombre_grupo}")
    
    # Botón para volver a la lista de grupos
    if st.button("⬅️ Volver a la lista de grupos"):
        del st.session_state.grupo_seleccionado_socios
        if 'nombre_grupo_seleccionado' in st.session_state:
            del st.session_state.nombre_grupo_seleccionado
        st.rerun()
    
    # Obtener socios del grupo
    socios = ejecutar_consulta(
        """SELECT s.id_socio, s.nombre, s.apellido, s.telefono, s.direccion, 
                  s.estado, d.nombre_distrito
           FROM socios s
           LEFT JOIN distrito d ON s.id_distrito = d.id_distrito
           WHERE s.id_grupo = %s
           ORDER BY s.nombre, s.apellido""",
        (id_grupo,)
    )
    
    if not socios:
        st.info("ℹ️ Este grupo no tiene socios registrados")
        return
    
    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_socios = len(socios)
        st.metric("👥 Total Socios", total_socios)
    
    with col2:
        socios_activos = len([s for s in socios if s['estado'] == 'ACTIVO'])
        st.metric("✅ Socios Activos", socios_activos)
    
    with col3:
        socios_inactivos = len([s for s in socios if s['estado'] == 'INACTIVO'])
        st.metric("❌ Socios Inactivos", socios_inactivos)
    
    # Filtros
    st.markdown("---")
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "ACTIVO", "INACTIVO"])
    
    with col_filtro2:
        buscar_nombre = st.text_input("Buscar por nombre:")
    
    # Aplicar filtros
    socios_filtrados = socios
    if filtro_estado != "Todos":
        socios_filtrados = [s for s in socios_filtrados if s['estado'] == filtro_estado]
    
    if buscar_nombre:
        socios_filtrados = [s for s in socios_filtrados if 
                           buscar_nombre.lower() in s['nombre'].lower() or 
                           buscar_nombre.lower() in s['apellido'].lower()]
    
    # Mostrar socios
    st.write(f"**Socios encontrados:** {len(socios_filtrados)}")
    
    for socio in socios_filtrados:
        with st.expander(f"👤 {socio['nombre']} {socio['apellido']} - {socio['estado']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📞 Teléfono:** {socio['telefono'] or 'No registrado'}")
                st.write(f"**🏠 Dirección:** {socio['direccion'] or 'No registrada'}")
            
            with col2:
                st.write(f"**🗺️ Distrito:** {socio['nombre_distrito'] or 'No asignado'}")
                st.write(f"**📊 Estado:** {socio['estado']}")
            
            # Información adicional del socio (ahorro, préstamos, etc.)
            mostrar_info_adicional_socio(socio['id_socio'])

def mostrar_info_adicional_socio(id_socio):
    """Mostrar información adicional del socio (ahorro, préstamos)"""
    
    st.markdown("---")
    st.write("**💰 Información Financiera:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ahorro del socio
        ahorro_socio = ejecutar_consulta("""
            SELECT saldo_final 
            FROM ahorro_detalle 
            WHERE id_socio = %s 
            ORDER BY id_ahorro_detalle DESC 
            LIMIT 1
        """, (id_socio,))
        
        if ahorro_socio and ahorro_socio[0]['saldo_final']:
            st.write(f"**Ahorro actual:** ${ahorro_socio[0]['saldo_final']:,.2f}")
        else:
            st.write("**Ahorro actual:** $0.00")
    
    with col2:
        # Préstamos del socio
        prestamos_socio = ejecutar_consulta(
            "SELECT COUNT(*) as total FROM prestamo WHERE id_socio = %s AND id_estado_prestamo IN (4, 6)",  # VIGENTE o MORA
            (id_socio,)
        )
        
        st.write(f"**Préstamos activos:** {prestamos_socio[0]['total'] if prestamos_socio else 0}")
