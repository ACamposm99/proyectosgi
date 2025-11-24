import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime
from utils.exportadores import generar_pdf_acta

def modulo_actas():
    """Módulo principal para generación de actas"""
    
    st.header("📄 Actas y Documentos Oficiales")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Acta de Reunión", "🏦 Acta de Préstamo", "🔚 Acta de Cierre", "📚 Historial de Actas"
    ])
    
    with tab1:
        acta_reunion()
    
    with tab2:
        acta_prestamo()
    
    with tab3:
        acta_cierre()
    
    with tab4:
        historial_actas()

def acta_reunion():
    """Generar acta de reunión"""
    
    st.subheader("📋 Generar Acta de Reunión")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede generar actas de reunión")
        return
    
    # Seleccionar reunión
    reuniones = obtener_reuniones_sin_acta(st.session_state.id_grupo)
    
    if not reuniones:
        st.info("ℹ️ No hay reuniones pendientes de acta")
        return
    
    reunion_seleccionada = st.selectbox(
        "Seleccionar Reunión",
        options=[(r['id_sesion'], r['fecha_sesion']) for r in reuniones],
        format_func=lambda x: f"Reunión del {x[1].strftime('%d/%m/%Y')}",
        key="select_reunion_acta"
    )
    
    if not reunion_seleccionada:
        return
    
    id_sesion, fecha_sesion = reunion_seleccionada
    
    # Obtener datos de la reunión
    datos_reunion = obtener_datos_reunion(id_sesion)
    
    if not datos_reunion:
        st.error("❌ No se pudieron obtener los datos de la reunión")
        return
    
    # Formulario para completar acta
    with st.form("form_acta_reunion"):
        st.markdown(f"### Acta de Reunión - {fecha_sesion.strftime('%d/%m/%Y')}")
        
        # Información básica
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Grupo:** {datos_reunion['nombre_grupo']}")
            st.write(f"**Lugar:** {datos_reunion['lugar_reunion']}")
            st.write(f"**Hora de inicio:** {datos_reunion['hora_inicio'] if datos_reunion['hora_inicio'] else '19:00'}")
        
        with col2:
            st.write(f"**Asistentes:** {datos_reunion['total_presentes']} de {datos_reunion['total_socios']}")
            st.write(f"**Porcentaje de asistencia:** {(datos_reunion['total_presentes']/datos_reunion['total_socios']*100):.1f}%")
        
        # Temas tratados
        st.markdown("#### 📝 Temas Tratados")
        temas_tratados = st.text_area(
            "Describa los temas tratados en la reunión:",
            placeholder="1. Revisión de estado de caja...\n2. Aprobación de nuevos préstamos...\n3. Planificación de actividades...",
            height=150
        )
        
        # Acuerdos y decisiones
        st.markdown("#### 🤝 Acuerdos y Decisiones")
        acuerdos = st.text_area(
            "Registre los acuerdos y decisiones tomadas:",
            placeholder="1. Se aprobó el préstamo para María García...\n2. Se programó rifa para el próximo mes...",
            height=150
        )
        
        # Aportes de ahorro
        st.markdown("#### 💰 Resumen de Aportes")
        
        if datos_reunion['total_ahorro'] > 0:
            st.write(f"**Total de aportes registrados:** ${datos_reunion['total_ahorro']:,.2f}")
            st.write(f"**Nuevo saldo de caja:** ${datos_reunion['saldo_cierre']:,.2f}")
        else:
            st.info("No se registraron aportes en esta reunión")
        
        # Firmas
        st.markdown("#### ✍️ Firmas de Validación")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            firma_presidenta = st.text_input("Presidente/a", key="presidenta_reunion")
        
        with col2:
            firma_secretaria = st.text_input("Secretario/a", key="secretaria_reunion")
        
        with col3:
            firma_tesorera = st.text_input("Tesorero/a", key="tesorera_reunion")
        
        if st.form_submit_button("📄 Generar Acta de Reunión"):
            if firma_presidenta and firma_secretaria and firma_tesorera:
                # Guardar acta
                if guardar_acta_reunion(
                    id_sesion, temas_tratados, acuerdos,
                    firma_presidenta, firma_secretaria, firma_tesorera
                ):
                    st.success("✅ Acta de reunión generada exitosamente")
                    
                    # Opción para descargar PDF
                    if st.button("📥 Descargar Acta en PDF"):
                        generar_acta_reunion_pdf(datos_reunion, temas_tratados, acuerdos)
                else:
                    st.error("❌ Error al guardar el acta")
            else:
                st.error("❌ Complete todas las firmas")

def acta_prestamo():
    """Generar acta de aprobación de préstamo"""
    
    st.subheader("🏦 Generar Acta de Préstamo")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede generar actas de préstamo")
        return
    
    # Obtener préstamos aprobados recientemente
    prestamos = obtener_prestamos_para_acta(st.session_state.id_grupo)
    
    if not prestamos:
        st.info("ℹ️ No hay préstamos pendientes de acta")
        return
    
    prestamo_seleccionado = st.selectbox(
        "Seleccionar Préstamo",
        options=[(p['id_prestamo'], f"{p['nombre']} {p['apellido']} - ${p['monto_solicitado']:,.2f}") for p in prestamos],
        format_func=lambda x: x[1],
        key="select_prestamo_acta"
    )
    
    if not prestamo_seleccionado:
        return
    
    id_prestamo = prestamo_seleccionado[0]
    
    # Obtener datos del préstamo
    datos_prestamo = obtener_datos_prestamo(id_prestamo)
    
    if not datos_prestamo:
        st.error("❌ No se pudieron obtener los datos del préstamo")
        return
    
    # Generar acta automáticamente
    st.markdown("### 📋 Acta de Aprobación de Préstamo")
    
    # Previsualización
    acta_html = generar_html_acta_prestamo(datos_prestamo)
    st.markdown(acta_html, unsafe_allow_html=True)
    
    # Firmas digitales
    st.markdown("#### ✍️ Firmas de Autorización")
    
    with st.form("form_acta_prestamo"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            firma_solicitante = st.text_input("Firma Solicitante", 
                                            value=f"{datos_prestamo['nombre']} {datos_prestamo['apellido']}")
        
        with col2:
            firma_presidenta = st.text_input("Firma Presidenta")
        
        with col3:
            firma_tesorera = st.text_input("Firma Tesorera")
        
        if st.form_submit_button("📄 Generar Acta de Préstamo"):
            if firma_solicitante and firma_presidenta and firma_tesorera:
                if guardar_acta_prestamo(id_prestamo, firma_solicitante, firma_presidenta, firma_tesorera):
                    st.success("✅ Acta de préstamo generada exitosamente")
                    
                    if st.button("📥 Descargar Acta en PDF"):
                        generar_acta_prestamo_pdf(datos_prestamo)
                else:
                    st.error("❌ Error al guardar el acta")
            else:
                st.error("❌ Complete todas las firmas")

def acta_cierre():
    """Consultar y descargar actas de cierre"""
    
    st.subheader("🔚 Actas de Cierre de Ciclo")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver actas de cierre")
        return
    
    # Obtener actas de cierre existentes
    actas = obtener_actas_cierre(st.session_state.id_grupo)
    
    if not actas:
        st.info("ℹ️ No hay actas de cierre generadas")
        return
    
    for acta in actas:
        with st.expander(f"📅 Acta de Cierre - {acta['fecha_cierre'].strftime('%d/%m/%Y')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Fecha de cierre:** {acta['fecha_cierre'].strftime('%d/%m/%Y')}")
                st.write(f"**Ahorro total:** ${acta['total_ahorro_grupo']:,.2f}")
            
            with col2:
                st.write(f"**Utilidades:** ${acta['total_ganancia_grupo']:,.2f}")
                st.write(f"**Saldo caja:** ${acta['saldo_cierre_caja']:,.2f}")
            
            with col3:
                st.write(f"**Firmas:**")
                st.write(f"- Presidenta: {acta['firma_presidenta']}")
                st.write(f"- Secretaria: {acta['firma_secretaria']}")
                st.write(f"- Tesorera: {acta['firma_tesorera']}")
            
            # Botones de acción
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Descargar PDF", key=f"pdf_{acta['id_ciclo']}"):
                    generar_acta_cierre_pdf(acta)
            
            with col2:
                if st.button("👁️ Ver Detalle", key=f"detalle_{acta['id_ciclo']}"):
                    mostrar_detalle_acta_cierre(acta['id_ciclo'])

def historial_actas():
    """Historial completo de actas"""
    
    st.subheader("📚 Historial de Actas y Documentos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva puede ver el historial de actas")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_acta = st.selectbox("Tipo de Acta", ["Todas", "Reuniones", "Préstamos", "Cierres"])
    
    with col2:
        fecha_inicio = st.date_input("Desde", datetime.now().replace(day=1), key="actas_desde")
        fecha_fin = st.date_input("Hasta", datetime.now(), key="actas_hasta")
    
    # Obtener historial
    historial = obtener_historial_actas(st.session_state.id_grupo, tipo_acta, fecha_inicio, fecha_fin)
    
    if historial:
        st.dataframe(historial, use_container_width=True)
    else:
        st.info("ℹ️ No hay actas que coincidan con los filtros")

# =============================================================================
# FUNCIONES AUXILIARES - ACTAS
# =============================================================================

def obtener_reuniones_sin_acta(id_grupo):
    """Obtener reuniones sin acta generada"""
    query = """
        SELECT s.id_sesion, s.fecha_sesion, s.total_presentes
        FROM sesion s
        WHERE s.id_grupo = %s
        AND s.fecha_sesion <= CURDATE()
        AND NOT EXISTS (
            SELECT 1 FROM actas_reunion ar WHERE ar.id_sesion = s.id_sesion
        )
        ORDER BY s.fecha_sesion DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_datos_reunion(id_sesion):
    """Obtener datos completos de una reunión"""
    query = """
        SELECT 
            s.id_sesion,
            s.fecha_sesion,
            s.total_presentes,
            g.nombre_grupo,
            g.lugar_reunion,
            (SELECT COUNT(*) FROM socios WHERE id_grupo = g.id_grupo) as total_socios,
            COALESCE(a.total_ingresos, 0) as total_ahorro,
            COALESCE(a.saldo_cierre, 0) as saldo_cierre
        FROM sesion s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        LEFT JOIN ahorro a ON s.id_sesion = a.id_sesion
        WHERE s.id_sesion = %s
    """
    resultado = ejecutar_consulta(query, (id_sesion,))
    return resultado[0] if resultado else None

def guardar_acta_reunion(id_sesion, temas, acuerdos, firma_presidenta, firma_secretaria, firma_tesorera):
    """Guardar acta de reunión en base de datos"""
    query = """
        INSERT INTO actas_reunion (
            id_sesion, temas_tratados, acuerdos, firma_presidenta, 
            firma_secretaria, firma_tesorera, fecha_creacion
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return ejecutar_comando(query, (id_sesion, temas, acuerdos, firma_presidenta, firma_secretaria, firma_tesorera, datetime.now()))

def obtener_prestamos_para_acta(id_grupo):
    """Obtener préstamos pendientes de acta"""
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            p.monto_solicitado,
            p.fecha_aprobacion,
            p.plazo_meses
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND p.id_estado_prestamo = 2  -- Aprobado
        AND NOT EXISTS (
            SELECT 1 FROM actas_prestamo ap WHERE ap.id_prestamo = p.id_prestamo
        )
        ORDER BY p.fecha_aprobacion DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_datos_prestamo(id_prestamo):
    """Obtener datos completos de un préstamo"""
    query = """
        SELECT 
            p.id_prestamo,
            s.nombre,
            s.apellido,
            s.telefono,
            s.direccion,
            p.monto_solicitado,
            p.plazo_meses,
            p.fecha_aprobacion,
            p.fecha_vencimiento,
            (p.monto_solicitado * (SELECT interes FROM reglas_del_grupo WHERE id_grupo = s.id_grupo) / 100) as interes_anual,
            (p.monto_solicitado + (p.monto_solicitado * (SELECT interes FROM reglas_del_grupo WHERE id_grupo = s.id_grupo) / 100)) as total_pagar,
            g.nombre_grupo
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        JOIN grupos g ON s.id_grupo = g.id_grupo
        WHERE p.id_prestamo = %s
    """
    resultado = ejecutar_consulta(query, (id_prestamo,))
    return resultado[0] if resultado else None

def generar_html_acta_prestamo(datos):
    """Generar HTML para acta de préstamo"""
    
    cuota_mensual = datos['total_pagar'] / datos['plazo_meses']
    
    html = f"""
    <div style="border: 1px solid #333; padding: 20px; border-radius: 5px; background-color: #f9f9f9;">
        <h2 style="text-align: center; color: #2c3e50;">ACTA DE PRÉSTAMO APROBADO</h2>
        <hr>
        
        <p><strong>Grupo:</strong> {datos['nombre_grupo']}</p>
        <p><strong>Fecha de aprobación:</strong> {datos['fecha_aprobacion'].strftime('%d/%m/%Y')}</p>
        
        <h4>DATOS DEL SOLICITANTE</h4>
        <p><strong>Nombre:</strong> {datos['nombre']} {datos['apellido']}</p>
        <p><strong>Teléfono:</strong> {datos['telefono']}</p>
        <p><strong>Dirección:</strong> {datos['direccion']}</p>
        
        <h4>TÉRMINOS DEL PRÉSTAMO</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Monto Aprobado</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">${datos['monto_solicitado']:,.2f}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Plazo</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{datos['plazo_meses']} meses</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Interés Anual</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">${datos['interes_anual']:,.2f}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total a Pagar</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">${datos['total_pagar']:,.2f}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Cuota Mensual</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">${cuota_mensual:,.2f}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Fecha Vencimiento</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{datos['fecha_vencimiento'].strftime('%d/%m/%Y')}</td>
            </tr>
        </table>
        
        <br>
        <p><em>El solicitante se compromete a cumplir con los pagos puntuales según el calendario establecido.</em></p>
    </div>
    """
    
    return html

def guardar_acta_prestamo(id_prestamo, firma_solicitante, firma_presidenta, firma_tesorera):
    """Guardar acta de préstamo en base de datos"""
    query = """
        INSERT INTO actas_prestamo (
            id_prestamo, firma_solicitante, firma_presidenta, firma_tesorera, fecha_creacion
        ) VALUES (%s, %s, %s, %s, %s)
    """
    return ejecutar_comando(query, (id_prestamo, firma_solicitante, firma_presidenta, firma_tesorera, datetime.now()))

def obtener_actas_cierre(id_grupo):
    """Obtener actas de cierre del grupo"""
    query = """
        SELECT 
            id_ciclo,
            fecha_cierre,
            total_ahorro_grupo,
            total_ganancia_grupo,
            saldo_cierre_caja,
            firma_presidenta,
            firma_secretaria,
            firma_tesorera
        FROM cierre_de_ciclo
        WHERE id_grupo = %s
        ORDER BY fecha_cierre DESC
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_historial_actas(id_grupo, tipo_acta, fecha_inicio, fecha_fin):
    """Obtener historial de actas"""
    import pandas as pd
    
    # Esta es una implementación simplificada
    # En una implementación real, se unirían las tablas de actas
    query = """
        SELECT 
            'Reunión' as tipo,
            ar.fecha_creacion as fecha,
            CONCAT('Acta de reunión - ', s.fecha_sesion) as descripcion
        FROM actas_reunion ar
        JOIN sesion s ON ar.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        AND ar.fecha_creacion BETWEEN %s AND %s
        
        UNION ALL
        
        SELECT 
            'Préstamo' as tipo,
            ap.fecha_creacion as fecha,
            CONCAT('Acta de préstamo - ', s.nombre, ' ', s.apellido) as descripcion
        FROM actas_prestamo ap
        JOIN prestamo p ON ap.id_prestamo = p.id_prestamo
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND ap.fecha_creacion BETWEEN %s AND %s
        
        UNION ALL
        
        SELECT 
            'Cierre' as tipo,
            fecha_cierre as fecha,
            CONCAT('Acta de cierre - ', fecha_cierre) as descripcion
        FROM cierre_de_ciclo
        WHERE id_grupo = %s
        AND fecha_cierre BETWEEN %s AND %s
        
        ORDER BY fecha DESC
    """
    
    if tipo_acta != "Todas":
        # Filtrar por tipo específico
        pass
    
    resultado = ejecutar_consulta(query, (id_grupo, fecha_inicio, fecha_fin, id_grupo, fecha_inicio, fecha_fin, id_grupo, fecha_inicio, fecha_fin))
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

# Funciones placeholder para generación de PDF
def generar_acta_reunion_pdf(datos, temas, acuerdos):
    st.info("🔧 Generando PDF de acta de reunión...")

def generar_acta_prestamo_pdf(datos):
    st.info("🔧 Generando PDF de acta de préstamo...")

def generar_acta_cierre_pdf(acta):
    st.info("🔧 Generando PDF de acta de cierre...")

def mostrar_detalle_acta_cierre(id_ciclo):
    st.info(f"🔧 Mostrando detalle de acta de cierre #{id_ciclo}")