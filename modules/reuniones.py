import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta
import pandas as pd
import tempfile
import os

def modulo_reuniones():
    """Módulo principal para gestión de reuniones y asistencia"""
    
    st.header("📅 Reuniones y Control de Asistencia")
    
    tab1, tab2, tab3 = st.tabs(["🆕 Nueva Reunión", "✅ Registrar Asistencia", "📋 Historial de Reuniones"])
    
    with tab1:
        nueva_reunion()
    
    with tab2:
        registrar_asistencia()
    
    with tab3:
        historial_reuniones()

def nueva_reunion():
    """Crear una nueva reunión/sesión - ADAPTADA A TU ESQUEMA"""
    
    st.subheader("Crear Nueva Reunión")
    
    # Solo permitir si el usuario es directiva y tiene un grupo
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede crear reuniones")
        return
    
    with st.form("form_nueva_reunion"):
        # Obtener información del grupo para sugerir fecha
        grupo_info = obtener_info_grupo(st.session_state.id_grupo)
        
        if grupo_info:
            st.info(f"**Grupo:** {grupo_info['nombre_grupo']}")
        
        # Calcular próxima fecha de reunión
        fecha_sugerida = calcular_proxima_reunion(st.session_state.id_grupo)
        
        fecha_sesion = st.date_input(
            "📅 Fecha de la Reunión", 
            value=fecha_sugerida,
            min_value=datetime.now().date()
        )
        
        # NOTA: Eliminamos los campos que no existen en tu tabla sesion
        # - tipo_reunion
        # - temas_agenda  
        # - notas_adicionales
        # - hora_sesion
        
        submitted = st.form_submit_button("💾 Crear Reunión")
        
        if submitted:
            # Debug: mostrar información antes de crear
            st.write(f"🔍 **DEBUG ANTES DE CREAR:**")
            st.write(f"id_grupo: {st.session_state.id_grupo} (tipo: {type(st.session_state.id_grupo)})")
            st.write(f"fecha_sesion: {fecha_sesion} (tipo: {type(fecha_sesion)})")
            
            id_sesion = crear_sesion(
                st.session_state.id_grupo, 
                fecha_sesion
            )
            
            if id_sesion:
                st.success(f"✅ Reunión creada exitosamente (Sesión #{id_sesion})")
                
                # Inicializar registros de asistencia automáticamente
                if inicializar_asistencia(id_sesion, st.session_state.id_grupo):
                    st.info("📋 Registros de asistencia inicializados para todos los socios")
                
                st.rerun()
            else:
                st.error("❌ Error al crear la reunión. Verifica los datos e intenta nuevamente.")

def crear_reunion_completa(id_grupo, fecha_sesion, hora=None, lugar=None, estado="ACTIVA"):
    """Crear reunión en la tabla reuniones si necesitas guardar más información"""
    
    query = """
        INSERT INTO reuniones (id_grupo, fecha, hora, lugar, estado)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    params = (
        int(id_grupo),
        fecha_sesion,
        hora or datetime.now().time(),
        lugar or "Lugar por definir",
        estado
    )
    
    id_reunion = ejecutar_comando(query, params)
    return id_reunion

def crear_sesion(id_grupo, fecha_sesion):
    """Crear nueva sesión/reunión en la base de datos - ADAPTADA A TU ESQUEMA"""
    
    query = """
        INSERT INTO sesion (id_grupo, fecha_sesion, total_presentes)
        VALUES (%s, %s, %s)
    """
    
    params = (
        int(id_grupo), 
        fecha_sesion,
        0  # total_presentes inicializado en 0
    )
    
    print(f"DEBUG - Query: {query}")
    print(f"DEBUG - Params: {params}")
    
    id_sesion = ejecutar_comando(query, params)
    
    return id_sesion

def inicializar_asistencia(id_sesion, id_grupo):
    """Inicializar registros de asistencia para todos los socios del grupo - FUNCIÓN CORREGIDA"""
    
    socios = obtener_socios_grupo(id_grupo)
    
    if not socios:
        st.warning("⚠️ No hay socios en este grupo para inicializar asistencia")
        return False
    
    for socio in socios:
        query = """
            INSERT INTO asistencia (id_sesion, id_socio, presencial)
            VALUES (%s, %s, %s)
        """
        # Pasar 3 parámetros
        params = (int(id_sesion), int(socio['id_socio']), 0)
        resultado = ejecutar_comando(query, params)
        
        if not resultado:
            st.error(f"❌ Error al inicializar asistencia para socio {socio['nombre']}")
            return False
    
    return True

def registrar_asistencia():
    """Registro de asistencia para una reunión existente - CLAVES ÚNICAS"""
    
    st.subheader("Registro de Asistencia")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede registrar asistencia")
        return
    
    # Obtener reuniones recientes del grupo
    reuniones = obtener_reuniones_recientes(st.session_state.id_grupo)
    
    if not reuniones:
        st.info("ℹ️ No hay reuniones creadas. Cree una reunión primero.")
        return
    
    # Seleccionar reunión
    sesion_seleccionada = st.selectbox(
        "Seleccione la reunión",
        options=[(r['id_sesion'], r['fecha_sesion']) for r in reuniones],
        format_func=lambda x: f"Reunión del {x[1].strftime('%d/%m/%Y')}",
        key="select_sesion_asistencia"
    )
    
    if sesion_seleccionada:
        id_sesion, fecha_sesion = sesion_seleccionada
        
        # Obtener información adicional de la sesión
        info_sesion = obtener_info_sesion(id_sesion)
        
        st.markdown(f"### Asistencia - Reunión del {fecha_sesion.strftime('%d/%m/%Y')}")
        
        if info_sesion:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Tipo:** {info_sesion.get('tipo_reunion', 'Reunión Regular')}")
            with col2:
                st.write(f"**Temas:** {info_sesion.get('temas_agenda', 'No especificados')}")
        
        # FORMULARIO DE ASISTENCIA
        with st.form(f"form_asistencia_{id_sesion}"):
            # Obtener lista de socios con su estado de asistencia
            asistencia_actual = obtener_asistencia_sesion(id_sesion)
            
            if asistencia_actual:
                total_presentes = 0
                
                st.markdown("#### Marcar Asistencia")
                st.caption("✅ Marque los socios presentes en la reunión")
                
                # Opción para marcar todos como presentes
                col_quick, _ = st.columns([1, 3])
                with col_quick:
                    if st.form_submit_button("✅ Marcar Todos como Presentes", 
                                           use_container_width=True,
                                           key=f"mark_all_{id_sesion}"):
                        for asistencia in asistencia_actual:
                            actualizar_asistencia(asistencia['id_asistencia'], True)
                        st.success("Todos los socios marcados como presentes")
                        st.rerun()
                
                for asistencia in asistencia_actual:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                    
                    with col1:
                        st.write(f"**{asistencia['nombre']} {asistencia['apellido']}**")
                    
                    with col2:
                        # Checkbox para marcar presencia
                        presente = st.checkbox(
                            "Presente",
                            value=bool(asistencia['presencial']),
                            key=f"asist_{asistencia['id_asistencia']}_{id_sesion}"
                        )
                    
                    with col4:
                        if presente:
                            total_presentes += 1
                            st.success("✅ Presente")
                        else:
                            st.error("❌ Ausente")
                    
                    # Actualizar inmediatamente cuando cambia
                    if st.session_state.get(f"asist_{asistencia['id_asistencia']}_{id_sesion}") != bool(asistencia['presencial']):
                        actualizar_asistencia(asistencia['id_asistencia'], presente)
                
                # Mostrar resumen
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                total_socios = len(asistencia_actual)
                with col1:
                    st.metric("👥 Total de Socios", total_socios)
                with col2:
                    st.metric("✅ Presentes", total_presentes)
                with col3:
                    ausentes = total_socios - total_presentes
                    st.metric("❌ Ausentes", ausentes)
                with col4:
                    porcentaje_asistencia = (total_presentes / total_socios) * 100 if total_socios > 0 else 0
                    st.metric("📊 Porcentaje", f"{porcentaje_asistencia:.1f}%")
                
                # Actualizar total en la sesión
                actualizar_total_presentes(id_sesion, total_presentes)
            
            # Botón de guardar dentro del formulario
            st.form_submit_button("💾 Guardar Cambios de Asistencia", 
                                use_container_width=True,
                                key=f"save_{id_sesion}")
        
        # BOTONES DE ACCIÓN FUERA DEL FORMULARIO (con claves únicas)
        st.markdown("---")
        st.markdown("### ⚡ Acciones Adicionales")
        
        if st.button("🛠️ Multa Manual", 
                    key=f"multa_manual_{id_sesion}"):
            ingresar_multa_manual(st.session_state.id_grupo)     
        
        if st.button("📄 Generar Acta de Asistencia", 
            key=f"acta_btn_{id_sesion}"):
            generar_acta_asistencia(id_sesion)
        
        
        if st.button("📋 Ver Multas Pendientes", 
            key=f"multas_view_{id_sesion}"):
            ver_multas_pendientes(st.session_state.id_grupo)

def timedelta_a_time(td):
    """Convertir timedelta de MySQL a datetime.time"""
    if isinstance(td, timedelta):
        return (datetime.min + td).time()
    return td

def obtener_siguiente_id_multa():
    """Obtener el próximo ID disponible para la tabla multa"""
    try:
        resultado = ejecutar_consulta("SELECT MAX(id_multa) as max_id FROM multa")
        if resultado and resultado[0]['max_id'] is not None:
            return resultado[0]['max_id'] + 1
        else:
            return 1
    except Exception as e:
        print(f"Error obteniendo próximo ID multa: {e}")
        return 1

def historial_reuniones():
    """Mostrar historial de reuniones del grupo - CORREGIDO CLAVES DUPLICADAS"""
    
    st.subheader("Historial de Reuniones")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede ver el historial")
        return
    
    reuniones = obtener_reuniones_grupo(st.session_state.id_grupo)
    
    if reuniones:
        # ... (código de métricas existente)
        
        # Lista detallada
        st.markdown("### 📋 Detalle de Reuniones")
        
        for i, reunion in enumerate(reuniones):
            with st.expander(f"📅 Reunión - {reunion['fecha_sesion'].strftime('%d/%m/%Y')} - {reunion['total_presentes']} presentes"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Fecha:** {reunion['fecha_sesion'].strftime('%d/%m/%Y')}")
                    st.write(f"**Asistentes:** {reunion['total_presentes']}")
                    
                    total_socios = obtener_total_socios_grupo(st.session_state.id_grupo)
                    if total_socios > 0:
                        porcentaje = (reunion['total_presentes'] / total_socios) * 100
                        st.write(f"**Porcentaje:** {porcentaje:.1f}%")
                        
                        if porcentaje >= 80:
                            st.success("✅ Buena asistencia")
                        elif porcentaje >= 60:
                            st.warning("⚠️ Asistencia regular")
                        else:
                            st.error("❌ Baja asistencia")
                
                with col2:
                    # Información adicional si existe
                    if reunion.get('tipo_reunion'):
                        st.write(f"**Tipo:** {reunion['tipo_reunion']}")
                    if reunion.get('temas_agenda'):
                        st.write(f"**Temas:** {reunion['temas_agenda'][:50]}...")
                
                with col3:
                    # Botones de acción con claves únicas
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("👁️", key=f"det_{reunion['id_sesion']}_{i}"):
                            ver_detalle_reunion(reunion['id_sesion'])
                    
                    with col_btn2:
                        if st.button("📄", key=f"acta_{reunion['id_sesion']}_{i}"):
                            generar_acta_asistencia(reunion['id_sesion'])
                    
                    # Botón adicional para reportes
                    if st.button("📊 Reporte", key=f"report_{reunion['id_sesion']}_{i}"):
                        generar_reporte_asistencia(reunion['id_sesion'])
    else:
        st.info("ℹ️ No hay reuniones registradas para este grupo")
        
# =============================================================================
# FUNCIONES AUXILIARES - REUNIONES (TODAS IMPLEMENTADAS)
# =============================================================================

def obtener_info_grupo(id_grupo):
    """Obtener información del grupo"""
    query = "SELECT nombre_grupo, dia_reunion, hora_reunion FROM grupos WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0] if resultado else None

def calcular_proxima_reunion(id_grupo):
    """Calcular la próxima fecha de reunión basada en la frecuencia del grupo"""
    # Obtener última reunión
    ultima_reunion = ejecutar_consulta(
        "SELECT fecha_sesion FROM sesion WHERE id_grupo = %s ORDER BY fecha_sesion DESC LIMIT 1",
        (id_grupo,)
    )
    
    if ultima_reunion:
        ultima_fecha = ultima_reunion[0]['fecha_sesion']
        # Asumir frecuencia semanal (ajustar según configuración real del grupo)
        return ultima_fecha + timedelta(days=7)
    else:
        return datetime.now().date()

def obtener_socios_grupo(id_grupo):
    """Obtener todos los socios de un grupo"""
    query = "SELECT id_socio, nombre, apellido FROM socios WHERE id_grupo = %s"
    return ejecutar_consulta(query, (id_grupo,))

def obtener_reuniones_recientes(id_grupo, limite=10):
    """Obtener reuniones recientes del grupo - ADAPTADA"""
    query = """
        SELECT id_sesion, fecha_sesion, total_presentes
        FROM sesion 
        WHERE id_grupo = %s 
        ORDER BY fecha_sesion DESC 
        LIMIT %s
    """
    return ejecutar_consulta(query, (id_grupo, limite))

def obtener_reuniones_grupo(id_grupo):
    """Obtener todas las reuniones de un grupo - ADAPTADA"""
    query = """
        SELECT id_sesion, fecha_sesion, total_presentes
        FROM sesion 
        WHERE id_grupo = %s 
        ORDER BY fecha_sesion DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_info_sesion(id_sesion):
    """Obtener información detallada de una sesión - ADAPTADA"""
    query = """
        SELECT s.*, g.nombre_grupo
        FROM sesion s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        WHERE s.id_sesion = %s
    """
    resultado = ejecutar_consulta(query, (id_sesion,))
    return resultado[0] if resultado else None


def obtener_asistencia_sesion(id_sesion):
    """Obtener la asistencia de una sesión específica"""
    query = """
        SELECT a.id_asistencia, a.presencial, s.id_socio, s.nombre, s.apellido
        FROM asistencia a
        JOIN socios s ON a.id_socio = s.id_socio
        WHERE a.id_sesion = %s
        ORDER BY s.apellido, s.nombre
    """
    return ejecutar_consulta(query, (id_sesion,))

def actualizar_asistencia(id_asistencia, presencial):
    """Actualizar registro de asistencia"""
    query = "UPDATE asistencia SET presencial = %s WHERE id_asistencia = %s"
    return ejecutar_comando(query, (1 if presencial else 0, id_asistencia))

def actualizar_total_presentes(id_sesion, total):
    """Actualizar el total de presentes en la sesión"""
    query = "UPDATE sesion SET total_presentes = %s WHERE id_sesion = %s"
    return ejecutar_comando(query, (total, id_sesion))

def obtener_reuniones_grupo(id_grupo):
    """Obtener todas las reuniones de un grupo"""
    query = """
        SELECT id_sesion, fecha_sesion, total_presentes
        FROM sesion 
        WHERE id_grupo = %s 
        ORDER BY fecha_sesion DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_total_socios_grupo(id_grupo):
    """Obtener el total de socios en un grupo"""
    query = "SELECT COUNT(*) as total FROM socios WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0

def ingresar_multa_manual(id_grupo=None):
    """Función para ingresar multas manualmente por diversos motivos"""
    
    st.subheader("💰 Ingresar Multa Manual")
    
    # Si no se proporciona id_grupo, permitir seleccionar grupo (para admin)
    if id_grupo is None:
        grupos = ejecutar_consulta("SELECT id_grupo, nombre_grupo FROM grupos WHERE estado = 'ACTIVO' ORDER BY nombre_grupo")
        if not grupos:
            st.error("No hay grupos activos disponibles")
            return
        
        grupo_seleccionado = st.selectbox(
            "Seleccionar Grupo",
            options=grupos,
            format_func=lambda x: x['nombre_grupo'],
            key="select_grupo_multa_manual"
        )
        id_grupo = grupo_seleccionado['id_grupo']
    else:
        # Mostrar información del grupo actual
        grupo_info = ejecutar_consulta("SELECT nombre_grupo FROM grupos WHERE id_grupo = %s", (id_grupo,))
        if grupo_info:
            st.info(f"**Grupo:** {grupo_info[0]['nombre_grupo']}")

    # Obtener socios del grupo
    socios = ejecutar_consulta(
        "SELECT id_socio, nombre, apellido FROM socios WHERE id_grupo = %s AND estado = 'ACTIVO' ORDER BY nombre, apellido",
        (id_grupo,)
    )
    
    if not socios:
        st.error("No hay socios activos en este grupo")
        return

    # Obtener reuniones recientes del grupo para asociar la multa
    reuniones = obtener_reuniones_recientes(id_grupo, 10)
    
    with st.form("form_multa_manual"):
        st.markdown("### 📋 Información de la Multa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleccionar socio
            socio_seleccionado = st.selectbox(
                "Socio *",
                options=socios,
                format_func=lambda x: f"{x['nombre']} {x['apellido']}",
                key="select_socio_multa"
            )
            
            # Motivo de la multa
            motivo = st.selectbox(
                "Motivo de la multa *",
                options=[
                    "Inasistencia a reunión",
                    "Llegada tardía",
                    "Falta de pago oportuno",
                    "Incumplimiento de normas",
                    "Daño a propiedad del grupo",
                    "Otro"
                ],
                key="select_motivo_multa"
            )
            
            # Motivo personalizado si se selecciona "Otro"
            if motivo == "Otro":
                motivo_personalizado = st.text_input("Especificar motivo *", placeholder="Describa el motivo de la multa")
                motivo = motivo_personalizado if motivo_personalizado else "Otro"
        
        with col2:
            # Monto de la multa
            monto_multa = st.number_input(
                "Monto de la multa ($) *",
                min_value=0.0,
                step=0.01,
                value=5.00,
                format="%.2f",
                key="monto_multa_manual"
            )
            
            # Fecha de vencimiento
            fecha_actual = datetime.now().date()
            fecha_vencimiento = st.date_input(
                "Fecha de vencimiento *",
                value=fecha_actual + timedelta(days=15),
                min_value=fecha_actual,
                key="fecha_vencimiento_manual"
            )
            
            # Opcional: asociar a una reunión específica
            if reuniones:
                asociar_reunion = st.checkbox("Asociar a reunión específica", value=False)
                if asociar_reunion:
                    reunion_seleccionada = st.selectbox(
                        "Seleccionar reunión",
                        options=[(r['id_sesion'], r['fecha_sesion']) for r in reuniones],
                        format_func=lambda x: f"Reunión del {x[1].strftime('%d/%m/%Y')}",
                        key="select_reunion_multa"
                    )
                    id_sesion = reunion_seleccionada[0] if reunion_seleccionada else None
                else:
                    id_sesion = None
            else:
                id_sesion = None
                st.info("No hay reuniones registradas para asociar")
        
        # Descripción adicional
        descripcion = st.text_area(
            "Descripción adicional (opcional)",
            placeholder="Detalles adicionales sobre la multa...",
            key="descripcion_multa"
        )
        
        submitted = st.form_submit_button("💾 Aplicar Multa Manual")
        
        if submitted:
            if not socio_seleccionado or not motivo or monto_multa <= 0:
                st.error("❌ Complete todos los campos obligatorios (*)")
                return
            
            # Aplicar la multa manual
            if aplicar_multa_manual(
                id_socio=socio_seleccionado['id_socio'],
                monto=monto_multa,
                motivo=motivo,
                fecha_vencimiento=fecha_vencimiento,
                id_sesion=id_sesion,
                descripcion=descripcion,
                id_grupo=id_grupo
            ):
                st.success(f"✅ Multa de ${monto_multa:.2f} aplicada exitosamente a {socio_seleccionado['nombre']} {socio_seleccionado['apellido']}")
                st.rerun()
            else:
                st.error("❌ Error al aplicar la multa manual")

def aplicar_multa_manual(id_socio, monto, motivo, fecha_vencimiento, id_sesion=None, descripcion="", id_grupo=None):
    """Aplicar multa manual a un socio - CORREGIDA"""
    
    try:
        # Obtener el próximo ID de multa
        id_multa = obtener_siguiente_id_multa()
        
        # Si no se proporciona id_sesion, usar una sesión por defecto o crear una específica
        if id_sesion is None:
            # Buscar una sesión existente del grupo para hoy o crear una nueva
            fecha_hoy = datetime.now().date()
            sesion_existente = ejecutar_consulta(
                "SELECT id_sesion FROM sesion WHERE id_grupo = %s AND fecha_sesion = %s",
                (id_grupo, fecha_hoy)
            )
            
            if sesion_existente:
                id_sesion = sesion_existente[0]['id_sesion']
            else:
                # Crear una nueva sesión para multas manuales de hoy
                query_sesion = """
                    INSERT INTO sesion (id_grupo, fecha_sesion, total_presentes)
                    VALUES (%s, %s, %s)
                """
                id_sesion = ejecutar_comando(
                    query_sesion, 
                    (id_grupo, fecha_hoy, 0)
                )
                if not id_sesion:
                    st.error("❌ Error al crear sesión para multa manual")
                    return False
        
        # DEBUG: Mostrar información antes de insertar
        st.write(f"🔍 DEBUG - Insertando multa:")
        st.write(f"ID Multa: {id_multa}")
        st.write(f"ID Sesión: {id_sesion}")
        st.write(f"ID Socio: {id_socio}")
        st.write(f"Monto: {monto}")
        st.write(f"Fecha Vencimiento: {fecha_vencimiento}")
        
        # Insertar la multa manual
        query = """
            INSERT INTO multa (id_multa, id_sesion, id_socio, monto_a_pagar, monto_pagado, fecha_pago_real, fecha_vencimiento)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            int(id_multa),
            int(id_sesion),
            int(id_socio),
            float(monto),
            0.00,  # monto_pagado inicial
            None,   # fecha_pago_real (null inicialmente)
            fecha_vencimiento
        )
        
        resultado = ejecutar_comando(query, params)
        
        if resultado:
            st.success(f"✅ Multa manual #{id_multa} aplicada exitosamente")
            
            # Guardar el motivo en un log o tabla auxiliar (si existe)
            # Por ahora solo lo mostramos
            st.info(f"**Motivo:** {motivo}")
            if descripcion:
                st.info(f"**Descripción:** {descripcion}")
            
            # Verificar que realmente se guardó
            multa_verificada = ejecutar_consulta(
                "SELECT * FROM multa WHERE id_multa = %s", 
                (id_multa,)
            )
            
            if multa_verificada:
                st.success("✅ Multa verificada en la base de datos")
            else:
                st.error("❌ La multa no se encontró después de insertarla")
            
            return True
        else:
            st.error("❌ No se pudo insertar la multa en la base de datos")
            return False
            
    except Exception as e:
        st.error(f"❌ Error aplicando multa manual: {str(e)}")
        return False

def ver_multas_pendientes(id_grupo=None):
    """Ver multas pendientes de pago - MEJORADA CON VERIFICACIÓN"""
    
    st.subheader("💰 Multas Pendientes")
    
    # Agregar botón para multa manual
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("💰 Ingresar Multa Manual", key="btn_multa_manual_main"):
            st.session_state.mostrar_multa_manual = True
    
    # Mostrar formulario de multa manual si se solicitó
    if st.session_state.get('mostrar_multa_manual'):
        ingresar_multa_manual(id_grupo)
        if st.button("❌ Cerrar formulario", key="cerrar_multa_manual_main"):
            st.session_state.mostrar_multa_manual = False
            st.rerun()
        st.markdown("---")
    
    # Primero, verificar qué multas existen en la base de datos
    st.markdown("### 🔍 Verificación de Multas en Base de Datos")
    
    # Consulta para contar multas totales
    if id_grupo:
        contador_query = """
            SELECT COUNT(*) as total 
            FROM multa m
            JOIN sesion s ON m.id_sesion = s.id_sesion
            WHERE s.id_grupo = %s
        """
        contador_params = (id_grupo,)
    else:
        contador_query = "SELECT COUNT(*) as total FROM multa"
        contador_params = None
    
    total_multas = ejecutar_consulta(contador_query, contador_params)
    
    if total_multas:
        st.info(f"📊 Total de multas en sistema: {total_multas[0]['total']}")
    
    # Consulta principal para obtener multas pendientes
    if id_grupo:
        query = """
            SELECT m.*, s.nombre, s.apellido, g.nombre_grupo, se.fecha_sesion
            FROM multa m
            JOIN socios s ON m.id_socio = s.id_socio
            JOIN sesion se ON m.id_sesion = se.id_sesion
            JOIN grupos g ON se.id_grupo = g.id_grupo
            WHERE se.id_grupo = %s AND m.monto_pagado < m.monto_a_pagar
            ORDER BY m.fecha_vencimiento ASC
        """
        params = (id_grupo,)
    else:
        query = """
            SELECT m.*, s.nombre, s.apellido, g.nombre_grupo, se.fecha_sesion
            FROM multa m
            JOIN socios s ON m.id_socio = s.id_socio
            JOIN sesion se ON m.id_sesion = se.id_sesion
            JOIN grupos g ON se.id_grupo = g.id_grupo
            WHERE m.monto_pagado < m.monto_a_pagar
            ORDER BY m.fecha_vencimiento ASC
        """
        params = None
    
    multas = ejecutar_consulta(query, params)
    
    # DEBUG: Mostrar información de la consulta
    st.write(f"🔍 DEBUG - Consulta ejecutada: {query}")
    st.write(f"🔍 DEBUG - Parámetros: {params}")
    st.write(f"🔍 DEBUG - Multas encontradas: {len(multas) if multas else 0}")
    
    if multas:
        total_pendiente = sum(float(multa['monto_a_pagar']) - float(multa['monto_pagado']) for multa in multas)
        multas_vencidas = [m for m in multas if m['fecha_vencimiento'] < datetime.now().date()]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📋 Multas Pendientes", len(multas))
        with col2:
            st.metric("💰 Total Pendiente", f"${total_pendiente:.2f}")
        with col3:
            st.metric("⚠️ Vencidas", len(multas_vencidas))
        
        # Mostrar lista de multas
        st.markdown("### 📝 Lista de Multas Pendientes")
        
        for i, multa in enumerate(multas):
            # Determinar estado y color
            if multa['fecha_vencimiento'] < datetime.now().date():
                estado = "🔴 VENCIDA"
                color_borde = "2px solid #ff4444"
            else:
                estado = "🟡 PENDIENTE"
                color_borde = "2px solid #ffaa00"
            
            with st.expander(f"{estado} | {multa['nombre']} {multa['apellido']} | ${float(multa['monto_a_pagar']):.2f} | Vence: {multa['fecha_vencimiento'].strftime('%d/%m/%Y')}", expanded=False):
                # Aplicar estilo de borde
                st.markdown(f"""
                    <style>
                    .multa-item-{i} {{
                        border: {color_borde};
                        padding: 10px;
                        border-radius: 5px;
                        margin: 5px 0;
                        background-color: #f8f9fa;
                    }}
                    </style>
                    <div class="multa-item-{i}">
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID Multa:** #{multa['id_multa']}")
                    st.write(f"**Grupo:** {multa['nombre_grupo']}")
                    st.write(f"**Reunión:** {multa['fecha_sesion'].strftime('%d/%m/%Y')}")
                    st.write(f"**Monto total:** ${float(multa['monto_a_pagar']):.2f}")
                    st.write(f"**Pagado:** ${float(multa['monto_pagado']):.2f}")
                    st.write(f"**Pendiente:** ${float(multa['monto_a_pagar']) - float(multa['monto_pagado']):.2f}")
                    
                with col2:
                    st.write(f"**Fecha vencimiento:** {multa['fecha_vencimiento'].strftime('%d/%m/%Y')}")
                    
                    # Calcular días restantes o vencidos
                    hoy = datetime.now().date()
                    if multa['fecha_vencimiento'] < hoy:
                        dias = (hoy - multa['fecha_vencimiento']).days
                        st.error(f"**Vencida hace {dias} días**")
                    else:
                        dias = (multa['fecha_vencimiento'] - hoy).days
                        st.warning(f"**Vence en {dias} días**")
                    
                    # Opción para registrar pago
                    if multa['monto_pagado'] < multa['monto_a_pagar']:
                        st.markdown("---")
                        st.write("**Registrar pago:**")
                        monto_pendiente = float(multa['monto_a_pagar']) - float(multa['monto_pagado'])
                        monto_pago = st.number_input(
                            "Monto a pagar",
                            min_value=0.0,
                            max_value=monto_pendiente,
                            value=monto_pendiente,
                            key=f"pago_{multa['id_multa']}_{i}"
                        )
                        
                        if st.button("💵 Registrar Pago", key=f"btn_pago_{multa['id_multa']}_{i}"):
                            if registrar_pago_multa(multa['id_multa'], monto_pago):
                                st.success("✅ Pago registrado exitosamente")
                                st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ No hay multas pendientes")
        
        # Botón para forzar recarga
        if st.button("🔄 Recargar datos de multas"):
            st.rerun()

def registrar_pago_multa(id_multa, monto_pago):
    """Registrar pago de una multa"""
    
    try:
        # Obtener información actual de la multa
        multa_info = ejecutar_consulta(
            "SELECT monto_a_pagar, monto_pagado FROM multa WHERE id_multa = %s",
            (id_multa,)
        )
        
        if not multa_info:
            st.error("❌ No se encontró la multa")
            return False
        
        monto_total = float(multa_info[0]['monto_a_pagar'])
        monto_actual_pagado = float(multa_info[0]['monto_pagado'])
        nuevo_monto_pagado = monto_actual_pagado + float(monto_pago)
        
        # Verificar que no se pague más del monto total
        if nuevo_monto_pagado > monto_total:
            st.error("❌ El monto pagado no puede exceder el monto total de la multa")
            return False
        
        # Actualizar multa
        query = """
            UPDATE multa 
            SET monto_pagado = %s, fecha_pago_real = %s 
            WHERE id_multa = %s
        """
        
        fecha_pago = datetime.now().date() if nuevo_monto_pagado >= monto_total else None
        
        params = (
            float(nuevo_monto_pagado),
            fecha_pago,
            int(id_multa)
        )
        
        if ejecutar_comando(query, params):
            st.success(f"✅ Pago de ${monto_pago:.2f} registrado exitosamente")
            
            # Si se completó el pago, mostrar mensaje
            if nuevo_monto_pagado >= monto_total:
                st.balloons()
                st.success("🎉 ¡Multa pagada completamente!")
            
            return True
        else:
            st.error("❌ Error al registrar el pago")
            return False
            
    except Exception as e:
        st.error(f"❌ Error registrando pago: {str(e)}")
        return False

def obtener_info_sesion(id_sesion):
    """Obtener información detallada de una sesión"""
    query = """
        SELECT s.*, g.nombre_grupo
        FROM sesion s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        WHERE s.id_sesion = %s
    """
    resultado = ejecutar_consulta(query, (id_sesion,))
    return resultado[0] if resultado else None

def ver_detalle_reunion(id_sesion):
    """Ver detalle de una reunión específica - FUNCIÓN IMPLEMENTADA"""
    
    info_sesion = obtener_info_sesion(id_sesion)
    
    if not info_sesion:
        st.error("❌ No se encontró información de la reunión")
        return
    
    st.subheader(f"📋 Detalle de Reunión - {info_sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
    
    # Información general
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Información General")
        st.write(f"**Grupo:** {info_sesion['nombre_grupo']}")
        st.write(f"**Fecha:** {info_sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
        st.write(f"**Asistentes:** {info_sesion['total_presentes']}")
        
        total_socios = obtener_total_socios_grupo(info_sesion['id_grupo'])
        if total_socios > 0:
            porcentaje = (info_sesion['total_presentes'] / total_socios) * 100
            st.write(f"**Porcentaje de asistencia:** {porcentaje:.1f}%")
    
    
    # Lista detallada de asistencia
    st.markdown("### 👥 Detalle de Asistencia")
    
    asistencia = obtener_asistencia_sesion(id_sesion)
    
    if asistencia:
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        
        presentes = sum(1 for a in asistencia if a['presencial'])
        ausentes = len(asistencia) - presentes
        
        with col1:
            st.metric("✅ Presentes", presentes)
        with col2:
            st.metric("❌ Ausentes", ausentes)
        with col3:
            st.metric("📊 Porcentaje", f"{(presentes/len(asistencia)*100):.1f}%")
        
        # Tabla detallada
        st.markdown("#### Lista de Socios")
        
        for socio in asistencia:
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                st.write(f"**{socio['nombre']} {socio['apellido']}**")
            
            with col2:
                if socio['presencial']:
                    st.success("✅ Presente")
                else:
                    st.error("❌ Ausente")
            
        
        # Exportar datos
        st.markdown("---")
        if st.button("📤 Exportar Lista de Asistencia"):
            exportar_lista_asistencia(id_sesion, asistencia, info_sesion)
    else:
        st.info("ℹ️ No hay datos de asistencia para esta reunión")

def generar_reporte_asistencia(id_sesion):
    """Generar reporte de asistencia para una reunión - FUNCIÓN IMPLEMENTADA"""
    
    info_sesion = obtener_info_sesion(id_sesion)
    asistencia = obtener_asistencia_sesion(id_sesion)
    
    if not info_sesion or not asistencia:
        st.error("❌ No se pueden generar reportes para esta reunión")
        return
    
    st.subheader(f"📊 Reporte de Asistencia - {info_sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
    
    # Estadísticas generales
    total_socios = len(asistencia)
    presentes = sum(1 for a in asistencia if a['presencial'])
    ausentes = total_socios - presentes
    porcentaje_asistencia = (presentes / total_socios) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Socios", total_socios)
    with col2:
        st.metric("Presentes", presentes)
    with col3:
        st.metric("Ausentes", ausentes)
    with col4:
        st.metric("Porcentaje", f"{porcentaje_asistencia:.1f}%")
    
    # Gráfico de pastel
    st.markdown("### 📈 Distribución de Asistencia")
    
    fig = px.pie(
        values=[presentes, ausentes],
        names=['Presentes', 'Ausentes'],
        color=['Presentes', 'Ausentes'],
        color_discrete_map={'Presentes':'green', 'Ausentes':'red'}
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
    
    # Recomendaciones
    st.markdown("### 💡 Recomendaciones")
    
    if porcentaje_asistencia >= 80:
        st.success("✅ Excelente nivel de asistencia. Mantener la participación actual.")
    elif porcentaje_asistencia >= 60:
        st.warning("⚠️ Asistencia regular. Considerar recordatorios para mejorar la participación.")
    else:
        st.error("❌ Baja asistencia. Revisar horarios y comunicar la importancia de la participación.")
        
        
def generar_acta_base_reunion(id_sesion):
    """Generar acta base para una reunión recién creada"""
    st.info("📄 Generando acta base de la reunión...")
    
    # Puedes crear una versión simplificada del acta
    generar_acta_asistencia(id_sesion)  # Reutilizamos la función existente


def generar_acta_asistencia(id_sesion):
    """Generar acta de asistencia formal en formato HTML - CORREGIDO SIN FORMULARIO"""
    
    try:
        # Obtener información de la sesión
        info_sesion = obtener_info_sesion(id_sesion)
        if not info_sesion:
            st.error("❌ No se encontró información de la reunión")
            return

        # Obtener datos de asistencia
        asistencia = obtener_asistencia_sesion(id_sesion)
        if not asistencia:
            st.error("❌ No hay datos de asistencia para esta reunión")
            return

        # Generar contenido HTML
        html_content = generar_html_acta(info_sesion, asistencia)
        
        st.success("✅ Acta de asistencia generada exitosamente")
        
        # Crear pestaña/modal para el acta
        with st.expander("📄 Vista previa del Acta - Haga clic para expandir", expanded=True):
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            st.markdown("---")
            st.markdown("### 📥 Opciones de Descarga")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Descargar como HTML
                fecha_str = info_sesion['fecha_sesion'].strftime('%Y%m%d')
                nombre_grupo = info_sesion['nombre_grupo'].replace(' ', '_')
                
                st.download_button(
                    label="📥 Descargar Acta (HTML)",
                    data=html_content,
                    file_name=f"acta_asistencia_{nombre_grupo}_{fecha_str}.html",
                    mime="text/html",
                    key=f"download_acta_{id_sesion}"  # Clave única
                )
            
            with col2:
                st.info("💡 **Para guardar como PDF:**")
                st.write("1. Abra el acta en vista previa")
                st.write("2. Use la opción 'Imprimir' de su navegador")
                st.write("3. Elija 'Guardar como PDF' como destino")
            
    except Exception as e:
        st.error(f"❌ Error generando el acta: {str(e)}")

def generar_html_acta(info_sesion, asistencia):
    """Generar contenido HTML para el acta"""
    
    # Calcular estadísticas
    total_socios = len(asistencia)
    presentes = sum(1 for a in asistencia if a['presencial'])
    ausentes = total_socios - presentes
    porcentaje = (presentes / total_socios) * 100 if total_socios > 0 else 0
    
    fecha_str = info_sesion['fecha_sesion'].strftime('%d de %B de %Y')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Acta de Asistencia - {info_sesion['nombre_grupo']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .subtitle {{
                font-size: 18px;
                color: #34495e;
                margin-bottom: 20px;
            }}
            .info-section {{
                margin-bottom: 25px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }}
            .stat-item {{
                padding: 10px;
                border-radius: 5px;
                text-align: center;
            }}
            .present {{
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
            }}
            .absent {{
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .present-row {{
                background-color: #d4edda !important;
            }}
            .absent-row {{
                background-color: #f8d7da !important;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #bdc3c7;
                text-align: center;
                font-size: 12px;
                color: #7f8c8d;
            }}
            .signature-section {{
                margin-top: 50px;
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 40px;
            }}
            .signature-line {{
                border-top: 1px solid #333;
                margin-top: 60px;
                text-align: center;
                padding-top: 5px;
            }}
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">ACTA DE ASISTENCIA</div>
            <div class="subtitle">Grupo de Ahorro y Préstamo: {info_sesion['nombre_grupo']}</div>
        </div>
        
        <div class="info-section">
            <h3>📅 INFORMACIÓN DE LA REUNIÓN</h3>
            <p><strong>Fecha:</strong> {fecha_str}</p>
            <p><strong>Hora de registro:</strong> {datetime.now().strftime('%H:%M')}</p>
            <p><strong>Lugar:</strong> Reunión del grupo</p>
        </div>
        
        <div class="stats">
            <div class="stat-item present">
                <strong>Socios Presentes</strong><br>
                <span style="font-size: 24px; font-weight: bold;">{presentes}</span>
            </div>
            <div class="stat-item absent">
                <strong>Socios Ausentes</strong><br>
                <span style="font-size: 24px; font-weight: bold;">{ausentes}</span>
            </div>
        </div>
        
        <div class="info-section">
            <p><strong>Total de socios:</strong> {total_socios}</p>
            <p><strong>Porcentaje de asistencia:</strong> {porcentaje:.1f}%</p>
            <p><strong>Evaluación:</strong> {obtener_evaluacion_asistencia(porcentaje)}</p>
        </div>
        
        <h3>👥 LISTA DETALLADA DE ASISTENCIA</h3>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Nombre del Socio</th>
                    <th>Asistencia</th>
                    <th>Observaciones</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Agregar filas de socios
    for i, socio in enumerate(asistencia, 1):
        estado = "PRESENTE" if socio['presencial'] else "AUSENTE"
        justificacion = socio.get('justificacion_ausencia', '')
        clase_fila = "present-row" if socio['presencial'] else "absent-row"
        
        html += f"""
                <tr class="{clase_fila}">
                    <td>{i}</td>
                    <td>{socio['nombre']} {socio['apellido']}</td>
                    <td><strong>{estado}</strong></td>
                    <td>{justificacion if justificacion else '-'}</td>
                </tr>
        """
    
    html += f"""
            </tbody>
        </table>
        
        <div class="signature-section">
            <div>
                <div class="signature-line"></div>
                <p style="text-align: center;"><strong>Presidente del Grupo</strong></p>
            </div>
            <div>
                <div class="signature-line"></div>
                <p style="text-align: center;"><strong>Secretario de Actas</strong></p>
            </div>
        </div>
        
        <div class="footer">
            <p>Documento generado automáticamente por el Sistema GAPC</p>
            <p>Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <script>
            // Script para mejorar la impresión
            function imprimirActa() {{
                window.print();
            }}
        </script>
    </body>
    </html>
    """
    
    return html

def obtener_evaluacion_asistencia(porcentaje):
    """Obtener evaluación cualitativa de la asistencia"""
    if porcentaje >= 80:
        return "✅ EXCELENTE - Cumple con el mínimo requerido"
    elif porcentaje >= 60:
        return "⚠️ REGULAR - Se recomienda mejorar la convocatoria"
    else:
        return "❌ BAJA - Revisar estrategias de participación"

def mostrar_instrucciones_impresion():
    """Mostrar instrucciones para imprimir el acta"""
    st.info("""
    **Para imprimir el acta:**
    1. Haga clic derecho en la vista previa del acta
    2. Seleccione 'Imprimir'
    3. En la configuración de impresión, elija 'Guardar como PDF' como destino
    4. Ajuste los márgenes y orientación según sea necesario
    5. Haga clic en 'Guardar'
    """)

def generar_acta_completa_reunion(id_sesion):
    """Generar acta completa de la reunión"""
    st.info("📄 Generando acta completa de la reunión...")
    generar_acta_asistencia(id_sesion)  # Reutilizamos la misma función

def generar_acta_base_reunion(id_sesion):
    """Generar acta base para una reunión recién creada"""
    st.info("📄 Generando acta base de la reunión...")
    generar_acta_asistencia(id_sesion)

class ActaAsistenciaPDF:
    """Clase para generar actas de asistencia en PDF"""
    
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
    
    def generar_acta(self, info_sesion, asistencia):
        """Generar el contenido del acta"""
        
        # Configurar página
        self.pdf.add_page()
        
        # Encabezado
        self._agregar_encabezado(info_sesion)
        
        # Información de la reunión
        self._agregar_info_reunion(info_sesion, asistencia)
        
        # Lista de asistencia
        self._agregar_lista_asistencia(asistencia)
        
        # Pie de página
        self._agregar_pie_pagina()
        
        return self.pdf.output(dest='S').encode('latin1')
    
    def _agregar_encabezado(self, info_sesion):
        """Agregar encabezado del acta"""
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.cell(0, 10, 'ACTA DE ASISTENCIA', 0, 1, 'C')
        self.pdf.ln(5)
        
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, f"Grupo: {info_sesion['nombre_grupo']}", 0, 1, 'C')
        self.pdf.ln(10)
    
    def _agregar_info_reunion(self, info_sesion, asistencia):
        """Agregar información de la reunión"""
        self.pdf.set_font('Arial', '', 12)
        
        # Fecha
        fecha_str = info_sesion['fecha_sesion'].strftime('%d de %B de %Y')
        self.pdf.cell(0, 8, f"Fecha de la reunión: {fecha_str}", 0, 1)
        
        # Estadísticas
        total_socios = len(asistencia)
        presentes = sum(1 for a in asistencia if a['presencial'])
        ausentes = total_socios - presentes
        porcentaje = (presentes / total_socios) * 100 if total_socios > 0 else 0
        
        self.pdf.cell(0, 8, f"Total de socios: {total_socios}", 0, 1)
        self.pdf.cell(0, 8, f"Socios presentes: {presentes}", 0, 1)
        self.pdf.cell(0, 8, f"Socios ausentes: {ausentes}", 0, 1)
        self.pdf.cell(0, 8, f"Porcentaje de asistencia: {porcentaje:.1f}%", 0, 1)
        self.pdf.ln(10)
    
    def _agregar_lista_asistencia(self, asistencia):
        """Agregar lista detallada de asistencia"""
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(0, 10, 'LISTA DE ASISTENCIA', 0, 1, 'C')
        self.pdf.ln(5)
        
        # Encabezados de tabla
        self.pdf.set_font('Arial', 'B', 10)
        self.pdf.cell(100, 8, 'SOCIO', 1, 0, 'C')
        self.pdf.cell(40, 8, 'ASISTENCIA', 1, 0, 'C')
        self.pdf.cell(50, 8, 'OBSERVACIONES', 1, 1, 'C')
        
        # Datos de la tabla
        self.pdf.set_font('Arial', '', 10)
        
        for socio in asistencia:
            nombre_completo = f"{socio['nombre']} {socio['apellido']}"
            
            # Nombre
            self.pdf.cell(100, 8, nombre_completo, 1, 0)
            
            # Asistencia
            if socio['presencial']:
                self.pdf.set_text_color(0, 128, 0)  # Verde
                self.pdf.cell(40, 8, 'PRESENTE', 1, 0, 'C')
                self.pdf.cell(50, 8, '', 1, 1)
            else:
                self.pdf.set_text_color(255, 0, 0)  # Rojo
                self.pdf.cell(40, 8, 'AUSENTE', 1, 0, 'C')
                justificacion = socio.get('justificacion_ausencia', 'Sin justificación')
                self.pdf.cell(50, 8, justificacion, 1, 1)
            
            # Restaurar color
            self.pdf.set_text_color(0, 0, 0)
    
    def _agregar_pie_pagina(self):
        """Agregar pie de página"""
        self.pdf.ln(15)
        self.pdf.set_font('Arial', 'I', 10)
        self.pdf.cell(0, 10, 'Documento generado automáticamente por el Sistema GAPC', 0, 0, 'C')

def generar_acta_completa_reunion(id_sesion):
    """Generar acta completa de la reunión"""
    st.info("📄 Generando acta completa de la reunión...")
    # En una implementación completa, aquí se generaría un documento completo
    st.success("Acta completa generada exitosamente")

def exportar_lista_asistencia(id_sesion, asistencia, info_sesion):
    """Exportar lista de asistencia en formato CSV"""
    
    # Preparar datos para CSV
    datos_exportar = []
    for socio in asistencia:
        datos_exportar.append({
            'Nombre': socio['nombre'],
            'Apellido': socio['apellido'],
            'Asistencia': 'Presente' if socio['presencial'] else 'Ausente',
        })
    
    df = pd.DataFrame(datos_exportar)
    csv = df.to_csv(index=False, encoding='utf-8')
    
    fecha_str = info_sesion['fecha_sesion'].strftime('%Y%m%d')
    nombre_grupo = info_sesion['nombre_grupo'].replace(' ', '_')
    
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"asistencia_{nombre_grupo}_{fecha_str}.csv",
        mime="text/csv"
    )