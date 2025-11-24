import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime, timedelta
import pandas as pd
from utils.exportadores import generar_pdf_acta_cierre

def modulo_cierre_ciclo():
    """Módulo principal para el cierre de ciclo"""
    
    st.header("🔚 Cierre de Ciclo del Grupo")
    
    # Verificar si el usuario pertenece a un grupo
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede realizar el cierre de ciclo")
        return
    
    # Proceso paso a paso
    st.markdown("### 📋 Proceso de Cierre de Ciclo")
    
    paso_actual = st.radio(
        "Seleccione el paso a ejecutar:",
        [
            "1. Verificación Preliminar",
            "2. Cálculo de Utilidades", 
            "3. Distribución a Socios",
            "4. Generar Acta de Cierre",
            "5. Confirmar Cierre"
        ],
        key="paso_cierre"
    )
    
    if "1. Verificación" in paso_actual:
        paso_verificacion_preliminar()
    elif "2. Cálculo" in paso_actual:
        paso_calculo_utilidades()
    elif "3. Distribución" in paso_actual:
        paso_distribucion_socios()
    elif "4. Generar" in paso_actual:
        paso_generar_acta()
    elif "5. Confirmar" in paso_actual:
        paso_confirmar_cierre()

def paso_verificacion_preliminar():
    """Paso 1: Verificación preliminar para cierre"""
    
    st.subheader("🔍 Verificación Preliminar")
    
    st.info("""
    **Requisitos para el cierre de ciclo:**
    - Todos los préstamos deben estar completamente pagados
    - No deben existir multas pendientes de pago
    - El ciclo debe haber alcanzado su fecha de finalización
    - Todas las reuniones deben estar registradas
    """)
    
    # Verificar préstamos pendientes
    prestamos_pendientes = verificar_prestamos_pendientes(st.session_state.id_grupo)
    
    if prestamos_pendientes:
        st.error(f"❌ **No se puede cerrar el ciclo:** Existen {len(prestamos_pendientes)} préstamos pendientes")
        
        st.markdown("#### Préstamos Pendientes")
        for prestamo in prestamos_pendientes:
            st.write(f"• {prestamo['nombre']} {prestamo['apellido']} - Saldo: ${prestamo['saldo_pendiente']:,.2f}")
        
        return False
    
    # Verificar multas pendientes
    multas_pendientes = verificar_multas_pendientes(st.session_state.id_grupo)
    
    if multas_pendientes > 0:
        st.warning(f"⚠️ Existen {multas_pendientes} multas pendientes de pago")
    
    # Verificar fecha de ciclo
    info_ciclo = obtener_info_ciclo_actual(st.session_state.id_grupo)
    
    if info_ciclo:
        hoy = datetime.now().date()
        if hoy < info_ciclo['fecha_fin_ciclo']:
            st.warning(f"⚠️ El ciclo finaliza el {info_ciclo['fecha_fin_ciclo'].strftime('%d/%m/%Y')}. ¿Desea cerrar anticipadamente?")
    
    # Verificar reuniones pendientes
    reuniones_pendientes = verificar_reuniones_pendientes(st.session_state.id_grupo)
    
    if reuniones_pendientes:
        st.warning(f"⚠️ Existen {reuniones_pendientes} reuniones pendientes de registro")
    
    st.success("✅ **Verificación completada:** Puede proceder con el cierre de ciclo")
    
    # Guardar estado de verificación
    if st.button("✅ Continuar al Cálculo de Utilidades"):
        st.session_state.verificacion_completada = True
        st.rerun()
    
    return True

def paso_calculo_utilidades():
    """Paso 2: Cálculo de utilidades del ciclo"""
    
    st.subheader("💰 Cálculo de Utilidades")
    
    if not st.session_state.get('verificacion_completada', False):
        st.warning("ℹ️ Complete la verificación preliminar primero")
        return
    
    # Obtener datos financieros del ciclo
    datos_ciclo = calcular_datos_ciclo(st.session_state.id_grupo)
    
    if not datos_ciclo:
        st.error("❌ No se pudieron calcular los datos del ciclo")
        return
    
    st.markdown("#### 📊 Resumen Financiero del Ciclo")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Ahorro Acumulado", f"${datos_ciclo['ahorro_total']:,.2f}")
    
    with col2:
        st.metric("📈 Intereses Cobrados", f"${datos_ciclo['intereses_cobrados']:,.2f}")
    
    with col3:
        st.metric("⚖️ Multas Cobradas", f"${datos_ciclo['multas_cobradas']:,.2f}")
    
    with col4:
        st.metric("💸 Gastos Operativos", f"${datos_ciclo['gastos_operativos']:,.2f}")
    
    st.markdown("---")
    
    # Cálculo de utilidades netas
    utilidades_netas = (datos_ciclo['intereses_cobrados'] + 
                       datos_ciclo['multas_cobradas'] - 
                       datos_ciclo['gastos_operativos'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🎯 Utilidades Brutas", 
                 f"${datos_ciclo['intereses_cobrados'] + datos_ciclo['multas_cobradas']:,.2f}")
    
    with col2:
        color = "green" if utilidades_netas >= 0 else "red"
        st.markdown(f"<h3 style='color: {color};'>🏆 Utilidades Netas: ${utilidades_netas:,.2f}</h3>", 
                   unsafe_allow_html=True)
    
    # Detalle de cálculos
    with st.expander("📋 Ver Detalle de Cálculos"):
        st.write(f"**Intereses por préstamos:** ${datos_ciclo['intereses_cobrados']:,.2f}")
        st.write(f"**Multas por mora/inasistencia:** ${datos_ciclo['multas_cobradas']:,.2f}")
        st.write(f"**Gastos operativos:** ${datos_ciclo['gastos_operativos']:,.2f}")
        st.write(f"**Utilidades netas:** ${utilidades_netas:,.2f}")
    
    # Guardar cálculos
    st.session_state.datos_ciclo = datos_ciclo
    st.session_state.utilidades_netas = utilidades_netas
    
    if st.button("✅ Continuar a Distribución"):
        st.session_state.calculo_completado = True
        st.rerun()

def paso_distribucion_socios():
    """Paso 3: Distribución de utilidades a socios"""
    
    st.subheader("📊 Distribución de Utilidades")
    
    if not st.session_state.get('calculo_completado', False):
        st.warning("ℹ️ Complete el cálculo de utilidades primero")
        return
    
    utilidades_netas = st.session_state.utilidades_netas
    
    if utilidades_netas <= 0:
        st.error("❌ No hay utilidades para distribuir")
        return
    
    st.info(f"**Total de utilidades a distribuir:** ${utilidades_netas:,.2f}")
    
    # Obtener socios y sus aportes
    socios_ahorro = obtener_socios_con_ahorro(st.session_state.id_grupo)
    
    if not socios_ahorro:
        st.error("❌ No se pudieron obtener los datos de los socios")
        return
    
    # Calcular distribución proporcional
    distribucion = calcular_distribucion_proporcional(socios_ahorro, utilidades_netas)
    
    st.markdown("#### 📈 Distribución Proporcional por Socio")
    
    # Mostrar tabla de distribución
    df_distribucion = pd.DataFrame(distribucion)
    st.dataframe(df_distribucion, use_container_width=True)
    
    # Resumen de distribución
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("👥 Total de Socios", len(distribucion))
    
    with col2:
        promedio_utilidad = utilidades_netas / len(distribucion)
        st.metric("📊 Promedio por Socio", f"${promedio_utilidad:,.2f}")
    
    with col3:
        max_utilidad = max(d['utilidad'] for d in distribucion)
        st.metric("🏆 Máxima Utilidad", f"${max_utilidad:,.2f}")
    
    # Gráfico de distribución
    st.markdown("#### 📊 Distribución Gráfica")
    
    # Preparar datos para gráfico
    nombres = [f"{d['nombre']} {d['apellido'][0]}." for d in distribucion]
    utilidades = [d['utilidad'] for d in distribucion]
    
    chart_data = pd.DataFrame({
        'Socio': nombres,
        'Utilidad': utilidades
    })
    
    st.bar_chart(chart_data.set_index('Socio'))
    
    # Guardar distribución
    st.session_state.distribucion = distribucion
    
    if st.button("✅ Continuar a Generación de Acta"):
        st.session_state.distribucion_completada = True
        st.rerun()

def paso_generar_acta():
    """Paso 4: Generación del acta de cierre"""
    
    st.subheader("📄 Generación de Acta de Cierre")
    
    if not st.session_state.get('distribucion_completada', False):
        st.warning("ℹ️ Complete la distribución de utilidades primero")
        return
    
    # Obtener información del grupo
    grupo_info = obtener_info_grupo(st.session_state.id_grupo)
    datos_ciclo = st.session_state.datos_ciclo
    distribucion = st.session_state.distribucion
    
    # Previsualización del acta
    st.markdown("#### 📋 Previsualización del Acta")
    
    acta_html = generar_html_acta_cierre(grupo_info, datos_ciclo, distribucion)
    st.markdown(acta_html, unsafe_allow_html=True)
    
    # Firmas digitales
    st.markdown("#### ✍️ Firmas de Validación")
    
    with st.form("form_firmas_acta"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            firma_presidenta = st.text_input("👑 Firma Presidenta", placeholder="Nombre completo")
        
        with col2:
            firma_secretaria = st.text_input("📝 Firma Secretaria", placeholder="Nombre completo")
        
        with col3:
            firma_tesorera = st.text_input("💰 Firma Tesorera", placeholder="Nombre completo")
        
        # Verificación final
        st.markdown("#### ✅ Verificación Final")
        verificado = st.checkbox("✅ Confirmo que toda la información es correcta y verificada")
        
        if st.form_submit_button("📄 Generar Acta de Cierre Definitiva"):
            if firma_presidenta and firma_secretaria and firma_tesorera and verificado:
                # Guardar acta en base de datos
                if guardar_acta_cierre(
                    st.session_state.id_grupo,
                    grupo_info,
                    datos_ciclo,
                    distribucion,
                    firma_presidenta,
                    firma_secretaria,
                    firma_tesorera
                ):
                    st.success("✅ Acta de cierre generada y guardada exitosamente")
                    st.session_state.acta_generada = True
                    
                    # Opción para descargar PDF
                    if st.button("📥 Descargar Acta en PDF"):
                        generar_pdf_acta_cierre(grupo_info, datos_ciclo, distribucion)
                else:
                    st.error("❌ Error al guardar el acta de cierre")
            else:
                st.error("❌ Complete todas las firmas y verificaciones")

def paso_confirmar_cierre():
    """Paso 5: Confirmación final del cierre"""
    
    st.subheader("🎉 Confirmación de Cierre de Ciclo")
    
    if not st.session_state.get('acta_generada', False):
        st.warning("ℹ️ Genere el acta de cierre primero")
        return
    
    st.success("""
    ### ¡Felicidades! 🎊
    
    Ha completado todos los pasos para el cierre del ciclo. 
    **El sistema está listo para finalizar el ciclo actual.**
    """)
    
    st.warning("""
    ⚠️ **Advertencia:** Esta acción es irreversible. Una vez confirmado el cierre:
    - Todos los saldos de ahorro se resetearán
    - Se archivarán los datos del ciclo
    - Se iniciará un nuevo ciclo automáticamente
    """)
    
    # Resumen final
    st.markdown("#### 📋 Resumen Final del Cierre")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("💰 Ahorro Total", f"${st.session_state.datos_ciclo['ahorro_total']:,.2f}")
        st.metric("📈 Utilidades", f"${st.session_state.utilidades_netas:,.2f}")
    
    with col2:
        st.metric("👥 Socios Beneficiados", len(st.session_state.distribucion))
        st.metric("📅 Fecha de Cierre", datetime.now().strftime("%d/%m/%Y"))
    
    # Confirmación final
    if st.button("🔒 CONFIRMAR CIERRE DEFINITIVO", type="primary"):
        if ejecutar_cierre_definitivo(st.session_state.id_grupo):
            st.balloons()
            st.success("""
            # 🎉 ¡Ciclo Cerrado Exitosamente!
            
            El ciclo ha sido cerrado y se ha iniciado automáticamente un nuevo ciclo.
            **¡Gracias por su gestión transparente!**
            """)
            
            # Reiniciar estado para nuevo ciclo
            st.session_state.verificacion_completada = False
            st.session_state.calculo_completado = False
            st.session_state.distribucion_completada = False
            st.session_state.acta_generada = False
        else:
            st.error("❌ Error al ejecutar el cierre definitivo")

# =============================================================================
# FUNCIONES AUXILIARES - CIERRE DE CICLO
# =============================================================================

def verificar_prestamos_pendientes(id_grupo):
    """Verificar si existen préstamos pendientes en el grupo"""
    query = """
        SELECT 
            s.nombre,
            s.apellido,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_pendiente
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s
        AND p.id_estado_prestamo IN (2, 5)  -- Aprobado o En Mora
        GROUP BY p.id_prestamo
        HAVING saldo_pendiente > 0
    """
    return ejecutar_consulta(query, (id_grupo,))

def verificar_multas_pendientes(id_grupo):
    """Verificar multas pendientes de pago"""
    query = """
        SELECT COUNT(*) as total
        FROM multa m
        JOIN socios s ON m.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND m.monto_pagado < m.monto_a_pagar
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0

def obtener_info_ciclo_actual(id_grupo):
    """Obtener información del ciclo actual"""
    query = """
        SELECT fecha_inicio_ciclo, fecha_fin_ciclo, duracion_ciclo_meses
        FROM reglas_del_grupo
        WHERE id_grupo = %s
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0] if resultado else None

def verificar_reuniones_pendientes(id_grupo):
    """Verificar reuniones pendientes de registro"""
    # Esta función asume reuniones semanales
    query = """
        SELECT COUNT(*) as total
        FROM sesion 
        WHERE id_grupo = %s 
        AND fecha_sesion < CURDATE()
        AND total_presentes = 0  -- Reuniones sin registrar
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0

def calcular_datos_ciclo(id_grupo):
    """Calcular datos financieros del ciclo completo"""
    
    # Obtener fechas del ciclo
    ciclo_info = obtener_info_ciclo_actual(id_grupo)
    if not ciclo_info:
        return None
    
    fecha_inicio = ciclo_info['fecha_inicio_ciclo']
    fecha_fin = ciclo_info['fecha_fin_ciclo']
    
    # Ahorro total acumulado
    ahorro_total = ejecutar_consulta("""
        SELECT COALESCE(SUM(saldo_cierre), 0) as total
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        AND s.fecha_sesion BETWEEN %s AND %s
    """, (id_grupo, fecha_inicio, fecha_fin))[0]['total']
    
    # Intereses cobrados
    intereses_cobrados = ejecutar_consulta("""
        SELECT COALESCE(SUM(interes_pagado), 0) as total
        FROM `detalle de pagos` dp
        JOIN prestamo p ON dp.id_prestamo = p.id_prestamo
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND dp.fecha_pago BETWEEN %s AND %s
    """, (id_grupo, fecha_inicio, fecha_fin))[0]['total']
    
    # Multas cobradas
    multas_cobradas = ejecutar_consulta("""
        SELECT COALESCE(SUM(monto_pagado), 0) as total
        FROM multa m
        JOIN socios s ON m.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND m.fecha_pago_real BETWEEN %s AND %s
    """, (id_grupo, fecha_inicio, fecha_fin))[0]['total']
    
    # Gastos operativos (egresos de caja)
    gastos_operativos = ejecutar_consulta("""
        SELECT COALESCE(SUM(monto), 0) as total
        FROM movimiento_de_caja mc
        JOIN caja c ON mc.id_caja = c.id_caja
        JOIN sesion s ON c.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        AND mc.id_tipomovimiento IN (3, 6, 7)  -- Tipos de egreso
        AND s.fecha_sesion BETWEEN %s AND %s
    """, (id_grupo, fecha_inicio, fecha_fin))[0]['total']
    
    return {
        'ahorro_total': ahorro_total,
        'intereses_cobrados': intereses_cobrados,
        'multas_cobradas': multas_cobradas,
        'gastos_operativos': abs(gastos_operativos),  # Valor absoluto
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }

def obtener_socios_con_ahorro(id_grupo):
    """Obtener socios con sus saldos de ahorro"""
    query = """
        SELECT 
            s.id_socio,
            s.nombre,
            s.apellido,
            COALESCE((
                SELECT saldo_final 
                FROM ahorro_detalle ad 
                JOIN ahorro a ON ad.id_ahorro = a.id_ahorro 
                JOIN sesion se ON a.id_sesion = se.id_sesion 
                WHERE ad.id_socio = s.id_socio 
                ORDER BY se.fecha_sesion DESC 
                LIMIT 1
            ), 0) as ahorro_individual
        FROM socios s
        WHERE s.id_grupo = %s
        AND s.id_socio IN (
            SELECT DISTINCT id_socio 
            FROM ahorro_detalle 
            WHERE saldo_final > 0
        )
    """
    return ejecutar_consulta(query, (id_grupo,))

def calcular_distribucion_proporcional(socios, utilidades_totales):
    """Calcular distribución proporcional de utilidades"""
    
    # Calcular total de ahorro
    total_ahorro = sum(socio['ahorro_individual'] for socio in socios)
    
    if total_ahorro == 0:
        return []
    
    distribucion = []
    for socio in socios:
        proporcion = socio['ahorro_individual'] / total_ahorro
        utilidad_asignada = utilidades_totales * proporcion
        
        distribucion.append({
            'id_socio': socio['id_socio'],
            'nombre': socio['nombre'],
            'apellido': socio['apellido'],
            'ahorro_individual': socio['ahorro_individual'],
            'proporcion': round(proporcion * 100, 2),
            'utilidad': round(utilidad_asignada, 2),
            'total_retiro': socio['ahorro_individual'] + utilidad_asignada
        })
    
    return distribucion

def obtener_info_grupo(id_grupo):
    """Obtener información del grupo"""
    query = """
        SELECT 
            nombre_grupo,
            fecha_creacion,
            lugar_reunion,
            dia_reunion,
            hora_reunion
        FROM grupos
        WHERE id_grupo = %s
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0] if resultado else None

def generar_html_acta_cierre(grupo_info, datos_ciclo, distribucion):
    """Generar HTML para el acta de cierre"""
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    total_utilidades = sum(d['utilidad'] for d in distribucion)
    total_retiros = sum(d['total_retiro'] for d in distribucion)
    
    html = f"""
    <div style="border: 2px solid #333; padding: 20px; border-radius: 10px; background-color: #f9f9f9; font-family: Arial, sans-serif;">
        <h1 style="text-align: center; color: #2c3e50; margin-bottom: 10px;">ACTA DE CIERRE DE CICLO</h1>
        <h2 style="text-align: center; color: #34495e; margin-top: 0;">Grupo: {grupo_info['nombre_grupo']}</h2>
        
        <hr style="border: 1px solid #bdc3c7;">
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
            <div>
                <p><strong>Fecha de Cierre:</strong> {fecha_actual}</p>
                <p><strong>Período del Ciclo:</strong> {datos_ciclo['fecha_inicio'].strftime('%d/%m/%Y')} - {datos_ciclo['fecha_fin'].strftime('%d/%m/%Y')}</p>
            </div>
            <div>
                <p><strong>Lugar de Reunión:</strong> {grupo_info['lugar_reunion']}</p>
                <p><strong>Día de Reunión:</strong> {grupo_info['dia_reunion']}</p>
            </div>
        </div>
        
        <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">RESUMEN FINANCIERO</h3>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #34495e; color: white;">
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Concepto</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Monto</th>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">Ahorro Total Acumulado</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;">${datos_ciclo['ahorro_total']:,.2f}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="border: 1px solid #ddd; padding: 10px;">Intereses Cobrados</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;">${datos_ciclo['intereses_cobrados']:,.2f}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">Multas Cobradas</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;">${datos_ciclo['multas_cobradas']:,.2f}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="border: 1px solid #ddd; padding: 10px;">Gastos Operativos</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;">(${datos_ciclo['gastos_operativos']:,.2f})</td>
            </tr>
            <tr style="background-color: #2ecc71; color: white; font-weight: bold;">
                <td style="border: 1px solid #ddd; padding: 12px;">UTILIDADES NETAS</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">${total_utilidades:,.2f}</td>
            </tr>
        </table>
        
        <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">DISTRIBUCIÓN POR SOCIO</h3>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #34495e; color: white;">
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Socio</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Ahorro</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Utilidad</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Total a Retirar</th>
            </tr>
    """
    
    for socio in distribucion:
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">{socio['nombre']} {socio['apellido']}</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;">${socio['ahorro_individual']:,.2f}</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;">${socio['utilidad']:,.2f}</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right; font-weight: bold;">${socio['total_retiro']:,.2f}</td>
            </tr>
        """
    
    html += f"""
            <tr style="background-color: #2c3e50; color: white; font-weight: bold;">
                <td style="border: 1px solid #ddd; padding: 12px;">TOTALES</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">${datos_ciclo['ahorro_total']:,.2f}</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">${total_utilidades:,.2f}</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">${total_retiros:,.2f}</td>
            </tr>
        </table>
        
        <div style="margin-top: 30px; border-top: 2px solid #bdc3c7; padding-top: 20px;">
            <div style="display: flex; justify-content: space-around;">
                <div style="text-align: center;">
                    <p style="border-top: 1px solid #333; width: 200px; padding-top: 5px;">Presidente/a</p>
                </div>
                <div style="text-align: center;">
                    <p style="border-top: 1px solid #333; width: 200px; padding-top: 5px;">Secretario/a</p>
                </div>
                <div style="text-align: center;">
                    <p style="border-top: 1px solid #333; width: 200px; padding-top: 5px;">Tesorero/a</p>
                </div>
            </div>
        </div>
        
        <p style="text-align: center; margin-top: 20px; font-style: italic; color: #7f8c8d;">
            Acta generada automáticamente por el Sistema GAPC - {fecha_actual}
        </p>
    </div>
    """
    
    return html

def guardar_acta_cierre(id_grupo, grupo_info, datos_ciclo, distribucion, firma_presidenta, firma_secretaria, firma_tesorera):
    """Guardar el acta de cierre en la base de datos"""
    
    # Crear registro de cierre
    query_cierre = """
        INSERT INTO cierre_de_ciclo (
            id_grupo, fecha_cierre, total_ahorro_grupo, total_ganancia_grupo,
            saldo_cierre_caja, firma_presidenta, firma_secretaria, firma_tesorera
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Obtener saldo final de caja
    saldo_caja = obtener_saldo_caja_actual(id_grupo)
    
    id_ciclo = ejecutar_comando(
        query_cierre,
        (
            id_grupo,
            datetime.now().date(),
            datos_ciclo['ahorro_total'],
            st.session_state.utilidades_netas,
            saldo_caja,
            firma_presidenta,
            firma_secretaria,
            firma_tesorera
        )
    )
    
    if not id_ciclo:
        return False
    
    # Guardar detalle por socio
    for distrib in distribucion:
        query_detalle = """
            INSERT INTO detalle_cierre_de_ciclo (
                id_ciclo, id_socio, saldo_final_ahorrado, porcion_fondo_grupo, retiro_final
            ) VALUES (%s, %s, %s, %s, %s)
        """
        
        ejecutar_comando(
            query_detalle,
            (
                id_ciclo,
                distrib['id_socio'],
                distrib['ahorro_individual'],
                distrib['utilidad'],
                distrib['total_retiro']
            )
        )
    
    return True

def obtener_saldo_caja_actual(id_grupo):
    """Obtener saldo actual de caja"""
    query = """
        SELECT saldo_cierre 
        FROM caja c
        JOIN sesion s ON c.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['saldo_cierre'] if resultado else 0

def ejecutar_cierre_definitivo(id_grupo):
    """Ejecutar el cierre definitivo del ciclo"""
    
    try:
        # 1. Marcar ciclo como cerrado en reglas
        ejecutar_comando("""
            UPDATE reglas_del_grupo 
            SET fecha_fin_ciclo = %s 
            WHERE id_grupo = %s
        """, (datetime.now().date(), id_grupo))
        
        # 2. Crear nuevo ciclo (iniciar nuevo período)
        nuevo_ciclo_inicio = datetime.now().date()
        nuevo_ciclo_fin = nuevo_ciclo_inicio + timedelta(days=180)  # 6 meses
        
        ejecutar_comando("""
            UPDATE reglas_del_grupo 
            SET fecha_inicio_ciclo = %s, fecha_fin_ciclo = %s 
            WHERE id_grupo = %s
        """, (nuevo_ciclo_inicio, nuevo_ciclo_fin, id_grupo))
        
        # 3. Resetear saldos de ahorro para nuevo ciclo
        ejecutar_comando("""
            UPDATE ahorro_detalle 
            SET saldo_ahorro = 0, saldo_ingresado = 0, otras_actividades = 0, saldo_final = 0
            WHERE id_socio IN (SELECT id_socio FROM socios WHERE id_grupo = %s)
        """, (id_grupo,))
        
        # 4. Archivar préstamos del ciclo anterior
        ejecutar_comando("""
            UPDATE prestamo 
            SET id_estado_prestamo = 4  -- Marcado como pagado/cerrado
            WHERE id_socio IN (SELECT id_socio FROM socios WHERE id_grupo = %s)
            AND id_estado_prestamo IN (2, 5)  -- Aprobado o En Mora
        """, (id_grupo,))
        
        return True
        
    except Exception as e:
        st.error(f"Error en cierre definitivo: {e}")
        return False