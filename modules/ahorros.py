import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime
from modules.reuniones import obtener_reuniones_recientes, obtener_total_socios_grupo
from decimal import Decimal
import pandas as pd
import tempfile
import os

def modulo_ahorros():
    """Módulo principal para gestión de ahorros"""
    
    st.header("💰 Aportes de Ahorro")
    
    tab1, tab2, tab3 = st.tabs(["📥 Registrar Aportes", "💳 Cierre de Caja Ahorro", "📊 Estado de Ahorros"])
    
    with tab1:
        registrar_aportes()
    
    with tab2:
        cierre_caja_ahorro()
    
    with tab3:
        estado_ahorros()

def registrar_aportes():
    """Registrar aportes de ahorro en una reunión"""
    
    st.subheader("Registrar Aportes de Ahorro")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede registrar aportes")
        return
    
    # Obtener reuniones recientes
    reuniones = obtener_reuniones_recientes(st.session_state.id_grupo, 5)
    
    if not reuniones:
        st.info("ℹ️ No hay reuniones creadas. Cree una reunión primero.")
        return
    
    # Seleccionar reunión
    sesion_seleccionada = st.selectbox(
        "Seleccione la reunión para registrar aportes",
        options=[(r['id_sesion'], r['fecha_sesion']) for r in reuniones],
        format_func=lambda x: f"Reunión del {x[1].strftime('%d/%m/%Y')}",
        key="select_sesion_ahorro"
    )
    
    if not sesion_seleccionada:
        return
    
    id_sesion, fecha_sesion = sesion_seleccionada
    
    st.markdown(f"### Registrar Aportes - Reunión del {fecha_sesion.strftime('%d/%m/%Y')}")
    
    # Verificar si ya existe registro de ahorro para esta sesión
    ahorro_existente = ejecutar_consulta("SELECT id_ahorro FROM ahorro WHERE id_sesion = %s", (id_sesion,))
    
    if not ahorro_existente:
        # Crear registro inicial de ahorro para la sesión
        saldo_apertura = obtener_ultimo_saldo_cierre(st.session_state.id_grupo)
        id_ahorro = crear_registro_ahorro(id_sesion, saldo_apertura)
        st.info(f"📋 Registro de ahorro inicial creado (Saldo apertura: ${saldo_apertura:,.2f})")
    else:
        id_ahorro = ahorro_existente[0]['id_ahorro']
    
    # Obtener socios con sus saldos actuales
    socios_con_saldo = obtener_socios_con_saldo_actual(st.session_state.id_grupo, id_ahorro)
    
    if not socios_con_saldo:
        st.error("❌ No hay socios en este grupo")
        return
    
    # Formulario para registrar aportes
    st.markdown("#### Aportes Individuales")
    st.caption("Ingrese los montos de aporte para cada socio presente")
    
    total_ingresos = Decimal('0.0')
    aportes_registrados = {}
    
    with st.form("form_aportes_ahorro"):
        for socio in socios_con_saldo:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.write(f"**{socio['nombre']} {socio['apellido']}**")
            
            with col2:
                st.write(f"Saldo anterior: **${socio['saldo_actual']:,.2f}**")
            
            with col3:
                # Campo para aporte de ahorro
                aporte_ahorro = st.number_input(
                    "Aporte Ahorro",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    key=f"ahorro_{socio['id_socio']}"
                )
            
            with col4:
                # Campo para otros ingresos (rifas, actividades, etc.)
                otros_ingresos = st.number_input(
                    "Otros ingresos",
                    min_value=0.0,
                    value=0.0,
                    step=5.0,
                    key=f"otros_{socio['id_socio']}"
                )
            
            # Convertir a Decimal para evitar problemas de tipo
            aporte_ahorro_decimal = Decimal(str(aporte_ahorro))
            otros_ingresos_decimal = Decimal(str(otros_ingresos))
            saldo_actual_decimal = Decimal(str(socio['saldo_actual']))
            
            # Calcular total para este socio
            total_socio = aporte_ahorro_decimal + otros_ingresos_decimal
            saldo_final = saldo_actual_decimal + total_socio
            total_ingresos += total_socio
            
            # Guardar datos para procesar después
            aportes_registrados[socio['id_socio']] = {
                'aporte_ahorro': aporte_ahorro_decimal,
                'otros_ingresos': otros_ingresos_decimal,
                'saldo_anterior': saldo_actual_decimal,
                'saldo_final': saldo_final
            }
        
        # Resumen antes de guardar
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Total de Ingresos", f"${float(total_ingresos):,.2f}")
        
        with col2:
            saldo_actual = Decimal(str(obtener_ultimo_saldo_cierre(st.session_state.id_grupo)))
            st.metric("📊 Saldo Actual", f"${float(saldo_actual):,.2f}")
        
        with col3:
            saldo_proyectado = saldo_actual + total_ingresos
            st.metric("🎯 Saldo Proyectado", f"${float(saldo_proyectado):,.2f}")
        
        # Botón para guardar - CORREGIDO: usar st.form_submit_button correctamente
        submitted = st.form_submit_button("💾 Guardar Todos los Aportes")
        
        if submitted:
            if total_ingresos > 0:
                # Guardar cada aporte individual
                for id_socio, datos in aportes_registrados.items():
                    if datos['aporte_ahorro'] > 0 or datos['otros_ingresos'] > 0:
                        guardar_aporte_individual(
                            id_socio, id_ahorro, float(datos['saldo_anterior']),
                            float(datos['aporte_ahorro']), float(datos['otros_ingresos']), float(datos['saldo_final'])
                        )
                
                # Actualizar totales en registro de ahorro
                actualizar_totales_ahorro(id_ahorro, float(total_ingresos), float(saldo_proyectado))
                
                st.success("✅ Todos los aportes han sido guardados exitosamente")
                st.rerun()
                
                # Generar comprobantes opcionales
                if st.checkbox("🖨️ Generar comprobantes individuales"):
                    generar_comprobantes_individuales(id_ahorro)
            else:
                st.warning("⚠️ No se registraron aportes. Ingrese montos mayores a 0.")

def cierre_caja_ahorro():
    """Cierre de caja de ahorro con firmas"""
    
    st.subheader("Cierre de Caja - Ahorro")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede cerrar caja")
        return
    
    # Obtener última sesión con ahorro
    ultima_sesion = ejecutar_consulta("""
        SELECT s.id_sesion, s.fecha_sesion, a.saldo_cierre, a.total_ingresos
        FROM sesion s
        JOIN ahorro a ON s.id_sesion = a.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """, (st.session_state.id_grupo,))
    
    if not ultima_sesion:
        st.info("ℹ️ No hay registros de ahorro para cerrar")
        return
    
    sesion = ultima_sesion[0]
    
    st.markdown(f"### Cierre de Caja - Reunión del {sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
    
    # Mostrar resumen
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Ingresos", f"${float(sesion['total_ingresos']):,.2f}")
    
    with col2:
        st.metric("🏦 Saldo Cierre", f"${float(sesion['saldo_cierre']):,.2f}")
    
    with col3:
        total_socios = obtener_total_socios_grupo(st.session_state.id_grupo)
        st.metric("👥 Socios", total_socios)
    
    # Firmas digitales
    st.markdown("### Firmas de Validación")
    
    with st.form("form_cierre_ahorro"):
        col1, col2 = st.columns(2)
        
        with col1:
            firma_tesorera = st.text_input("🤵 Firma Tesorera", placeholder="Nombre completo de la tesorera")
        
        with col2:
            firma_presidenta = st.text_input("👑 Firma Presidenta", placeholder="Nombre completo de la presidenta")
        
        # Verificación
        st.markdown("### Verificación de Cierre")
        verificado = st.checkbox("✅ Confirmo que los montos han sido verificados y son correctos")
        
        # CORREGIDO: Botón de envío dentro del formulario
        submit_cierre = st.form_submit_button("🔒 Cerrar Caja de Ahorro")
        
        if submit_cierre:
            if firma_tesorera and firma_presidenta and verificado:
                if actualizar_firmas_ahorro(sesion['id_sesion'], firma_tesorera, firma_presidenta):
                    st.success("🎉 Caja de ahorro cerrada exitosamente con firmas")
                    st.rerun()
                    
                    # Generar acta de cierre
                    if st.button("📄 Generar Acta de Cierre"):
                        generar_acta_cierre_ahorro(sesion['id_sesion'])
            else:
                st.error("❌ Complete todas las firmas y verificaciones")

def estado_ahorros():
    """Estado de ahorros individuales y del grupo"""
    
    st.subheader("Estado de Ahorros")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede ver estos reportes")
        return
    
    # Obtener estado actual de ahorros
    estado_ahorros = obtener_estado_ahorros_grupo(st.session_state.id_grupo)
    
    if estado_ahorros:
        # Convertir a DataFrame para mejor visualización
        df = pd.DataFrame(estado_ahorros)
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ahorro = df['saldo_final'].sum()
            st.metric("💰 Ahorro Total", f"${total_ahorro:,.2f}")
        
        with col2:
            promedio_ahorro = df['saldo_final'].mean()
            st.metric("📊 Promedio por Socio", f"${promedio_ahorro:,.2f}")
        
        with col3:
            max_ahorro = df['saldo_final'].max()
            st.metric("🏆 Máximo Ahorro", f"${max_ahorro:,.2f}")
        
        with col4:
            min_ahorro = df['saldo_final'].min()
            st.metric("📉 Mínimo Ahorro", f"${min_ahorro:,.2f}")
        
        # Tabla detallada
        st.markdown("### Detalle por Socio")
        
        # Formatear DataFrame para mostrar
        df_display = df[['nombre', 'apellido', 'saldo_anterior', 'aporte_actual', 'otros_ingresos', 'saldo_final']]
        df_display.columns = ['Nombre', 'Apellido', 'Saldo Anterior', 'Aporte Actual', 'Otros', 'Saldo Final']
        
        st.dataframe(df_display, use_container_width=True)
        
        # Gráfico de distribución
        st.markdown("### Distribución de Ahorros")
        if not df.empty:
            chart_data = df[['nombre', 'apellido', 'saldo_final']].copy()
            chart_data['socio'] = chart_data['nombre'] + ' ' + chart_data['apellido'].str[0] + '.'
            
            st.bar_chart(chart_data.set_index('socio')['saldo_final'])
        
        # Opción de exportar
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="📤 Exportar a CSV",
            data=csv,
            file_name=f"estado_ahorros_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ No hay registros de ahorro para este grupo")

# =============================================================================
# FUNCIONES AUXILIARES - AHORROS (TODAS IMPLEMENTADAS)
# =============================================================================

def obtener_ultimo_saldo_cierre(id_grupo):
    """Obtener el último saldo de cierre de ahorro del grupo"""
    query = """
        SELECT a.saldo_cierre 
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """
    
    resultado = ejecutar_consulta(query, (id_grupo,))
    return Decimal(str(resultado[0]['saldo_cierre'])) if resultado else Decimal('0.0')

def crear_registro_ahorro(id_sesion, saldo_apertura):
    """Crear registro inicial de ahorro para una sesión"""
    query = """
        INSERT INTO ahorro (id_sesion, saldo_apertura, total_ingresos, saldo_cierre, firma_tesorera, firma_presidenta)
        VALUES (%s, %s, 0, %s, '', '')
    """
    return ejecutar_comando(query, (id_sesion, saldo_apertura, saldo_apertura))

def obtener_socios_con_saldo_actual(id_grupo, id_ahorro):
    """Obtener socios con su saldo actual de ahorro"""
    
    # Primero obtener todos los socios del grupo
    socios = ejecutar_consulta(
        "SELECT id_socio, nombre, apellido FROM socios WHERE id_grupo = %s ORDER BY apellido, nombre",
        (id_grupo,)
    )
    
    resultado = []
    for socio in socios:
        # Buscar último saldo del socio
        ultimo_saldo = ejecutar_consulta("""
            SELECT saldo_final 
            FROM ahorro_detalle 
            WHERE id_socio = %s 
            ORDER BY id_ahorro_detalle DESC 
            LIMIT 1
        """, (socio['id_socio'],))
        
        saldo_actual = ultimo_saldo[0]['saldo_final'] if ultimo_saldo else 0
        
        # Verificar si ya tiene registro en esta sesión
        registro_actual = ejecutar_consulta(
            "SELECT * FROM ahorro_detalle WHERE id_socio = %s AND id_ahorro = %s",
            (socio['id_socio'], id_ahorro)
        )
        
        resultado.append({
            **socio,
            'saldo_actual': saldo_actual,
            'tiene_registro': bool(registro_actual)
        })
    
    return resultado

def guardar_aporte_individual(id_socio, id_ahorro, saldo_anterior, aporte_ahorro, otros_ingresos, saldo_final):
    """Guardar aporte individual de un socio"""
    
    # Verificar si ya existe registro
    existe = ejecutar_consulta(
        "SELECT id_ahorro_detalle FROM ahorro_detalle WHERE id_socio = %s AND id_ahorro = %s",
        (id_socio, id_ahorro)
    )
    
    if existe:
        # Actualizar registro existente
        query = """
            UPDATE ahorro_detalle 
            SET saldo_ahorro = %s, saldo_ingresado = %s, otras_actividades = %s, saldo_final = %s
            WHERE id_socio = %s AND id_ahorro = %s
        """
        return ejecutar_comando(query, (saldo_anterior, aporte_ahorro, otros_ingresos, saldo_final, id_socio, id_ahorro))
    else:
        # Crear nuevo registro
        query = """
            INSERT INTO ahorro_detalle (id_socio, id_ahorro, saldo_ahorro, saldo_ingresado, otras_actividades, saldo_final)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return ejecutar_comando(query, (id_socio, id_ahorro, saldo_anterior, aporte_ahorro, otros_ingresos, saldo_final))

def actualizar_totales_ahorro(id_ahorro, total_ingresos, saldo_cierre):
    """Actualizar totales en el registro principal de ahorro"""
    query = """
        UPDATE ahorro 
        SET total_ingresos = %s, saldo_cierre = %s 
        WHERE id_ahorro = %s
    """
    return ejecutar_comando(query, (total_ingresos, saldo_cierre, id_ahorro))

def actualizar_firmas_ahorro(id_sesion, firma_tesorera, firma_presidenta):
    """Actualizar firmas en el registro de ahorro"""
    query = """
        UPDATE ahorro 
        SET firma_tesorera = %s, firma_presidenta = %s 
        WHERE id_sesion = %s
    """
    return ejecutar_comando(query, (firma_tesorera, firma_presidenta, id_sesion))

def obtener_estado_ahorros_grupo(id_grupo):
    """Obtener el estado actual de ahorros de todos los socios del grupo"""
    
    # Obtener el último registro de ahorro del grupo
    ultimo_ahorro = ejecutar_consulta("""
        SELECT a.id_ahorro 
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """, (id_grupo,))
    
    if not ultimo_ahorro:
        return []
    
    id_ahorro = ultimo_ahorro[0]['id_ahorro']
    
    # Obtener detalle de ahorros
    query = """
        SELECT s.nombre, s.apellido, ad.saldo_ahorro as saldo_anterior, 
               ad.saldo_ingresado as aporte_actual, ad.otras_actividades as otros_ingresos,
               ad.saldo_final
        FROM ahorro_detalle ad
        JOIN socios s ON ad.id_socio = s.id_socio
        WHERE ad.id_ahorro = %s
        ORDER BY s.apellido, s.nombre
    """
    
    return ejecutar_consulta(query, (id_ahorro,))

def generar_comprobantes_individuales(id_ahorro):
    """Generar comprobantes individuales para todos los socios - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener datos de la sesión y socios
    datos_sesion = ejecutar_consulta("""
        SELECT s.fecha_sesion, g.nombre_grupo, a.total_ingresos, a.saldo_cierre
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        JOIN grupos g ON s.id_grupo = g.id_grupo
        WHERE a.id_ahorro = %s
    """, (id_ahorro,))
    
    if not datos_sesion:
        st.error("❌ No se encontraron datos de la sesión")
        return
    
    sesion = datos_sesion[0]
    detalles_socios = obtener_estado_ahorros_grupo_por_ahorro(id_ahorro)
    
    if not detalles_socios:
        st.error("❌ No hay datos de socios para generar comprobantes")
        return
    
    st.subheader("🖨️ Comprobantes Individuales de Ahorro")
    st.markdown(f"**Reunión:** {sesion['nombre_grupo']} - {sesion['fecha_sesion'].strftime('%d/%m/%Y')}")
    
    # Generar comprobante para cada socio
    for socio in detalles_socios:
        with st.expander(f"Comprobante: {socio['nombre']} {socio['apellido']}"):
            st.markdown(f"""
            ### 📄 Comprobante de Ahorro
            
            **Grupo:** {sesion['nombre_grupo']}
            **Fecha:** {sesion['fecha_sesion'].strftime('%d/%m/%Y')}
            **Socio:** {socio['nombre']} {socio['apellido']}
            
            ---
            
            **Saldo Anterior:** ${socio['saldo_anterior']:,.2f}
            **Aporte Actual:** ${socio['aporte_actual']:,.2f}
            **Otros Ingresos:** ${socio['otros_ingresos']:,.2f}
            
            **💵 TOTAL AHORRO ACTUAL:** ${socio['saldo_final']:,.2f}
            
            ---
            
            *Firma del Tesorero/a:* _________________________
            
            *Fecha de emisión:* {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """)
            
            # Opción para descargar comprobante individual
            comprobante_texto = f"""
            COMPROBANTE DE AHORRO
            =====================
            
            Grupo: {sesion['nombre_grupo']}
            Fecha: {sesion['fecha_sesion'].strftime('%d/%m/%Y')}
            Socio: {socio['nombre']} {socio['apellido']}
            
            Saldo Anterior: ${socio['saldo_anterior']:,.2f}
            Aporte Actual: ${socio['aporte_actual']:,.2f}
            Otros Ingresos: ${socio['otros_ingresos']:,.2f}
            
            TOTAL AHORRO ACTUAL: ${socio['saldo_final']:,.2f}
            
            Firma del Tesorero/a: _________________________
            
            Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """
            
            st.download_button(
                label=f"📥 Descargar Comprobante - {socio['nombre']}",
                data=comprobante_texto,
                file_name=f"comprobante_ahorro_{socio['nombre']}_{socio['apellido']}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                key=f"comprobante_{socio['id_socio']}"
            )
    
    # Generar archivo consolidado
    st.markdown("---")
    if st.button("📦 Generar Archivo Consolidado de Todos los Comprobantes"):
        generar_archivo_consolidado_comprobantes(detalles_socios, sesion)

def generar_acta_cierre_ahorro(id_sesion):
    """Generar acta de cierre de ahorro - FUNCIÓN IMPLEMENTADA"""
    
    # Obtener datos completos de la sesión
    datos_sesion = ejecutar_consulta("""
        SELECT s.fecha_sesion, g.nombre_grupo, a.total_ingresos, a.saldo_cierre,
               a.firma_tesorera, a.firma_presidenta, a.saldo_apertura
        FROM sesion s
        JOIN grupos g ON s.id_grupo = g.id_grupo
        JOIN ahorro a ON s.id_sesion = a.id_sesion
        WHERE s.id_sesion = %s
    """, (id_sesion,))
    
    if not datos_sesion:
        st.error("❌ No se encontraron datos para el acta de cierre")
        return
    
    sesion = datos_sesion[0]
    detalles_socios = obtener_estado_ahorros_grupo_por_sesion(id_sesion)
    
    st.subheader("📄 Acta de Cierre de Caja - Ahorro")
    
    # Mostrar previsualización del acta
    st.markdown(f"""
    ### ACTA DE CIERRE DE CAJA - AHORRO
    
    **Grupo:** {sesion['nombre_grupo']}
    **Fecha de la reunión:** {sesion['fecha_sesion'].strftime('%d/%m/%Y')}
    **Fecha de cierre:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    ---
    
    **RESUMEN FINANCIERO:**
    
    - Saldo de Apertura: ${sesion['saldo_apertura']:,.2f}
    - Total de Ingresos: ${sesion['total_ingresos']:,.2f}
    - **Saldo de Cierre: ${sesion['saldo_cierre']:,.2f}**
    
    ---
    
    **DETALLE POR SOCIO:**
    """)
    
    # Tabla de detalle
    if detalles_socios:
        df_detalle = pd.DataFrame(detalles_socios)
        df_detalle_display = df_detalle[['nombre', 'apellido', 'saldo_anterior', 'aporte_actual', 'otros_ingresos', 'saldo_final']]
        df_detalle_display.columns = ['Nombre', 'Apellido', 'Saldo Anterior', 'Aporte', 'Otros', 'Saldo Final']
        st.dataframe(df_detalle_display, use_container_width=True)
    
    st.markdown(f"""
    ---
    
    **FIRMAS:**
    
    Tesorera: {sesion['firma_tesorera'] or "_________________________"}
    
    Presidenta: {sesion['firma_presidenta'] or "_________________________"}
    
    ---
    
    *Este acta certifica que el cierre de caja de ahorro ha sido verificado y aprobado por la directiva del grupo.*
    """)
    
    # Generar archivo del acta
    acta_texto = f"""
    ACTA DE CIERRE DE CAJA - AHORRO
    ================================
    
    Grupo: {sesion['nombre_grupo']}
    Fecha de la reunión: {sesion['fecha_sesion'].strftime('%d/%m/%Y')}
    Fecha de cierre: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    RESUMEN FINANCIERO:
    -------------------
    Saldo de Apertura: ${sesion['saldo_apertura']:,.2f}
    Total de Ingresos: ${sesion['total_ingresos']:,.2f}
    Saldo de Cierre: ${sesion['saldo_cierre']:,.2f}
    
    DETALLE POR SOCIO:
    ------------------
    """
    
    # Agregar detalle de socios
    for socio in detalles_socios:
        acta_texto += f"""
        - {socio['nombre']} {socio['apellido']}:
          Saldo Anterior: ${socio['saldo_anterior']:,.2f}
          Aporte: ${socio['aporte_actual']:,.2f}
          Otros: ${socio['otros_ingresos']:,.2f}
          Saldo Final: ${socio['saldo_final']:,.2f}
        """
    
    acta_texto += f"""
    
    FIRMAS:
    -------
    Tesorera: {sesion['firma_tesorera'] or "_________________________"}
    Presidenta: {sesion['firma_presidenta'] or "_________________________"}
    
    Este acta certifica que el cierre de caja de ahorro ha sido verificado y aprobado por la directiva del grupo.
    """
    
    st.download_button(
        label="📥 Descargar Acta de Cierre Completa",
        data=acta_texto,
        file_name=f"acta_cierre_ahorro_{sesion['nombre_grupo']}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

# =============================================================================
# FUNCIONES ADICIONALES IMPLEMENTADAS
# =============================================================================

def obtener_estado_ahorros_grupo_por_ahorro(id_ahorro):
    """Obtener estado de ahorros por ID de ahorro"""
    query = """
        SELECT s.id_socio, s.nombre, s.apellido, ad.saldo_ahorro as saldo_anterior, 
               ad.saldo_ingresado as aporte_actual, ad.otras_actividades as otros_ingresos,
               ad.saldo_final
        FROM ahorro_detalle ad
        JOIN socios s ON ad.id_socio = s.id_socio
        WHERE ad.id_ahorro = %s
        ORDER BY s.apellido, s.nombre
    """
    return ejecutar_consulta(query, (id_ahorro,))

def obtener_estado_ahorros_grupo_por_sesion(id_sesion):
    """Obtener estado de ahorros por ID de sesión"""
    query = """
        SELECT s.id_socio, s.nombre, s.apellido, ad.saldo_ahorro as saldo_anterior, 
               ad.saldo_ingresado as aporte_actual, ad.otras_actividades as otros_ingresos,
               ad.saldo_final
        FROM ahorro_detalle ad
        JOIN socios s ON ad.id_socio = s.id_socio
        JOIN ahorro a ON ad.id_ahorro = a.id_ahorro
        WHERE a.id_sesion = %s
        ORDER BY s.apellido, s.nombre
    """
    return ejecutar_consulta(query, (id_sesion,))

def generar_archivo_consolidado_comprobantes(detalles_socios, datos_sesion):
    """Generar archivo consolidado con todos los comprobantes"""
    
    contenido_consolidado = f"""
    COMPROBANTES CONSOLIDADOS DE AHORRO
    ====================================
    
    Grupo: {datos_sesion['nombre_grupo']}
    Fecha de reunión: {datos_sesion['fecha_sesion'].strftime('%d/%m/%Y')}
    Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    """
    
    for socio in detalles_socios:
        contenido_consolidado += f"""
        --- COMPROBANTE INDIVIDUAL ---
        Socio: {socio['nombre']} {socio['apellido']}
        Saldo Anterior: ${socio['saldo_anterior']:,.2f}
        Aporte Actual: ${socio['aporte_actual']:,.2f}
        Otros Ingresos: ${socio['otros_ingresos']:,.2f}
        TOTAL AHORRO: ${socio['saldo_final']:,.2f}
        
        """
    
    contenido_consolidado += f"""
    RESUMEN GENERAL:
    ----------------
    Total Socios: {len(detalles_socios)}
    Total Ahorro Grupo: ${sum(socio['saldo_final'] for socio in detalles_socios):,.2f}
    """
    
    st.download_button(
        label="📦 Descargar Archivo Consolidado",
        data=contenido_consolidado,
        file_name=f"comprobantes_consolidados_{datos_sesion['nombre_grupo']}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

# Reutilizar funciones de reuniones
from modules.reuniones import obtener_reuniones_recientes, obtener_total_socios_grupo