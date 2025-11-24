import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime
import pandas as pd

def modulo_cierre_ciclo():
    """Módulo principal para el cierre de ciclo"""
    
    st.header("🔚 Cierre de Ciclo")
    
    tab1, tab2, tab3 = st.tabs(["📋 Verificación Preliminar", "📊 Cálculo de Utilidades", "📄 Acta de Cierre"])
    
    with tab1:
        verificacion_preliminar()
    
    with tab2:
        calculo_utilidades()
    
    with tab3:
        acta_cierre()

def verificacion_preliminar():
    """Verificación preliminar para cierre de ciclo"""
    
    st.subheader("Verificación Preliminar")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede realizar el cierre de ciclo")
        return
    
    # Verificar préstamos pendientes
    prestamos_pendientes = verificar_prestamos_pendientes(st.session_state.id_grupo)
    
    if prestamos_pendientes:
        st.error(f"❌ No se puede cerrar el ciclo. Existen {len(prestamos_pendientes)} préstamos pendientes.")
        
        st.markdown("### Préstamos Pendientes")
        for prestamo in prestamos_pendientes:
            st.write(f"• {prestamo['nombre']} {prestamo['apellido']} - ${prestamo['saldo_actual']:,.2f} - {prestamo['dias_mora']} días en mora")
        
        return
    
    st.success("✅ No hay préstamos pendientes. Puede proceder con el cierre de ciclo.")
    
    # Verificar otras condiciones
    st.markdown("### Otras Verificaciones")
    
    # Verificar si hay multas pendientes
    multas_pendientes = verificar_multas_pendientes(st.session_state.id_grupo)
    if multas_pendientes:
        st.warning(f"⚠️ Existen {len(multas_pendientes)} multas pendientes de pago.")
    else:
        st.success("✅ No hay multas pendientes.")
    
    # Verificar si el ciclo está en fecha de cierre
    ciclo_info = obtener_info_ciclo(st.session_state.id_grupo)
    if ciclo_info:
        hoy = datetime.now().date()
        if hoy < ciclo_info['fecha_fin_ciclo']:
            st.warning(f"⚠️ El ciclo termina el {ciclo_info['fecha_fin_ciclo'].strftime('%d/%m/%Y')}. ¿Desea cerrar anticipadamente?")
        else:
            st.success("✅ El ciclo ha llegado a su fecha de finalización.")
    
    # Botón para proceder
    if st.button("✅ Proceder con Cierre de Ciclo"):
        st.session_state.cierre_habilitado = True
        st.rerun()

def calculo_utilidades():
    """Cálculo y distribución de utilidades"""
    
    st.subheader("Cálculo de Utilidades")
    
    if not st.session_state.get('cierre_habilitado', False):
        st.warning("ℹ️ Complete la verificación preliminar primero.")
        return
    
    if not st.session_state.id_grupo:
        return
    
    # Obtener datos para el cálculo
    datos_ciclo = obtener_datos_ciclo(st.session_state.id_grupo)
    
    if not datos_ciclo:
        st.error("❌ No se pudieron obtener los datos del ciclo.")
        return
    
    st.markdown("### Resumen Financiero del Ciclo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Ahorro Total", f"${datos_ciclo['total_ahorro']:,.2f}")
    
    with col2:
        st.metric("📈 Intereses Cobrados", f"${datos_ciclo['total_intereses']:,.2f}")
    
    with col3:
        st.metric("⚖️ Multas Cobradas", f"${datos_ciclo['total_multas']:,.2f}")
    
    with col4:
        st.metric("🎯 Utilidades Netas", f"${datos_ciclo['utilidades_netas']:,.2f}")
    
    # Distribución de utilidades
    st.markdown("### Distribución de Utilidades")
    
    distribucion = calcular_distribucion_utilidades(st.session_state.id_grupo, datos_ciclo['utilidades_netas'])
    
    if distribucion:
        # Mostrar tabla de distribución
        df_distribucion = pd.DataFrame(distribucion)
        st.dataframe(df_distribucion, use_container_width=True)
        
        # Mostrar resumen de distribución
        st.markdown("#### Resumen de Distribución")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Total a distribuir:** ${datos_ciclo['utilidades_netas']:,.2f}")
            st.write(f"**Número de socios:** {len(distribucion)}")
        
        with col2:
            promedio = datos_ciclo['utilidades_netas'] / len(distribucion) if distribucion else 0
            st.write(f"**Promedio por socio:** ${promedio:,.2f}")
            st.write(f"**Socio con mayor utilidad:** ${max([d['utilidad'] for d in distribucion]):,.2f}")
        
        # Botón para confirmar distribución
        if st.button("💾 Confirmar Distribución"):
            if guardar_distribucion_utilidades(st.session_state.id_grupo, distribucion):
                st.success("✅ Distribución de utilidades guardada exitosamente")
                st.session_state.distribucion_guardada = True
            else:
                st.error("❌ Error al guardar la distribución")
    else:
        st.error("❌ No se pudo calcular la distribución de utilidades")

def acta_cierre():
    """Generación del acta de cierre"""
    
    st.subheader("Acta de Cierre de Ciclo")
    
    if not st.session_state.get('distribucion_guardada', False):
        st.warning("ℹ️ Complete el cálculo de utilidades primero.")
        return
    
    if not st.session_state.id_grupo:
        return
    
    # Obtener información del grupo y ciclo
    grupo_info = obtener_info_grupo_cierre(st.session_state.id_grupo)
    distribucion = obtener_distribucion_guardada(st.session_state.id_grupo)
    
    if not grupo_info or not distribucion:
        st.error("❌ No se pudo obtener la información para generar el acta.")
        return
    
    # Mostrar previsualización del acta
    st.markdown("### Previsualización del Acta")
    
    acta_html = generar_acta_cierre_html(grupo_info, distribucion)
    st.markdown(acta_html, unsafe_allow_html=True)
    
    # Firmas
    st.markdown("### Firmas de Validación")
    
    with st.form("form_firmas_acta"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            firma_presidenta = st.text_input("👑 Firma Presidenta")
        
        with col2:
            firma_secretaria = st.text_input("📝 Firma Secretaria")
        
        with col3:
            firma_tesorera = st.text_input("💰 Firma Tesorera")
        
        if st.form_submit_button("📄 Generar Acta de Cierre"):
            if firma_presidenta and firma_secretaria and firma_tesorera:
                # Guardar acta con firmas
                if guardar_acta_cierre(st.session_state.id_grupo, grupo_info, distribucion, firma_presidenta, firma_secretaria, firma_tesorera):
                    st.success("🎉 Acta de cierre generada y guardada exitosamente")
                    
                    # Marcar ciclo como cerrado
                    if marcar_ciclo_cerrado(st.session_state.id_grupo):
                        st.balloons()
                        st.success("✅ Ciclo cerrado exitosamente. ¡Felicidades!")
                else:
                    st.error("❌ Error al guardar el acta de cierre")
            else:
                st.error("❌ Todas las firmas son obligatorias")

# =============================================================================
# FUNCIONES AUXILIARES - CIERRE DE CICLO
# =============================================================================

def verificar_prestamos_pendientes(id_grupo):
    """Verificar si hay préstamos pendientes en el grupo"""
    query = """
        SELECT 
            s.nombre,
            s.apellido,
            (p.monto_solicitado - COALESCE(SUM(dp.capital_pagado), 0)) as saldo_actual,
            DATEDIFF(CURDATE(), p.fecha_vencimiento) as dias_mora
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE s.id_grupo = %s
        AND p.id_estado_prestamo IN (2, 5)  -- Aprobado o En Mora
        GROUP BY p.id_prestamo
        HAVING saldo_actual > 0
    """
    return ejecutar_consulta(query, (id_grupo,))

def verificar_multas_pendientes(id_grupo):
    """Verificar si hay multas pendientes de pago"""
    query = """
        SELECT COUNT(*) as total
        FROM multa m
        JOIN socios s ON m.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND m.monto_pagado < m.monto_a_pagar
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0

def obtener_info_ciclo(id_grupo):
    """Obtener información del ciclo actual"""
    query = """
        SELECT fecha_inicio_ciclo, fecha_fin_ciclo, duracion_ciclo_meses
        FROM reglas_del_grupo
        WHERE id_grupo = %s
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0] if resultado else None

def obtener_datos_ciclo(id_grupo):
    """Obtener datos financieros del ciclo"""
    
    # Ahorro total
    ahorro_total = ejecutar_consulta("""
        SELECT COALESCE(SUM(saldo_cierre), 0) as total
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        AND s.fecha_sesion BETWEEN (SELECT fecha_inicio_ciclo FROM reglas_del_grupo WHERE id_grupo = %s) 
                            AND CURDATE()
    """, (id_grupo, id_grupo))
    
    # Intereses cobrados
    intereses_cobrados = ejecutar_consulta("""
        SELECT COALESCE(SUM(interes_pagado), 0) as total
        FROM `detalle de pagos` dp
        JOIN prestamo p ON dp.id_prestamo = p.id_prestamo
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND dp.fecha_pago BETWEEN (SELECT fecha_inicio_ciclo FROM reglas_del_grupo WHERE id_grupo = %s) 
                          AND CURDATE()
    """, (id_grupo, id_grupo))
    
    # Multas cobradas
    multas_cobradas = ejecutar_consulta("""
        SELECT COALESCE(SUM(monto_pagado), 0) as total
        FROM multa m
        JOIN socios s ON m.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND m.fecha_pago_real BETWEEN (SELECT fecha_inicio_ciclo FROM reglas_del_grupo WHERE id_grupo = %s) 
                              AND CURDATE()
    """, (id_grupo, id_grupo))
    
    # Gastos operativos (simplificado)
    gastos_operativos = ejecutar_consulta("""
        SELECT COALESCE(SUM(monto), 0) as total
        FROM movimiento_de_caja mc
        JOIN caja c ON mc.id_caja = c.id_caja
        JOIN sesion s ON c.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        AND mc.id_tipomovimiento IN (3, 6, 7)  -- Egresos
        AND s.fecha_sesion BETWEEN (SELECT fecha_inicio_ciclo FROM reglas_del_grupo WHERE id_grupo = %s) 
                            AND CURDATE()
    """, (id_grupo, id_grupo))
    
    total_ahorro = ahorro_total[0]['total'] if ahorro_total else 0
    total_intereses = intereses_cobrados[0]['total'] if intereses_cobrados else 0
    total_multas = multas_cobradas[0]['total'] if multas_cobradas else 0
    total_gastos = gastos_operativos[0]['total'] if gastos_operativos else 0
    
    utilidades_netas = total_intereses + total_multas - total_gastos
    
    return {
        'total_ahorro': total_ahorro,
        'total_intereses': total_intereses,
        'total_multas': total_multas,
        'total_gastos': total_gastos,
        'utilidades_netas': max(0, utilidades_netas)  # No negativas
    }

def calcular_distribucion_utilidades(id_grupo, utilidades_netas):
    """Calcular distribución proporcional de utilidades"""
    
    # Obtener el ahorro individual de cada socio al cierre
    ahorros_socios = ejecutar_consulta("""
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
    """, (id_grupo,))
    
    if not ahorros_socios:
        return None
    
    # Calcular total de ahorro
    total_ahorro = sum(socio['ahorro_individual'] for socio in ahorros_socios)
    
    if total_ahorro == 0:
        return None
    
    # Calcular distribución proporcional
    distribucion = []
    for socio in ahorros_socios:
        proporcion = socio['ahorro_individual'] / total_ahorro
        utilidad = utilidades_netas * proporcion
        
        distribucion.append({
            'id_socio': socio['id_socio'],
            'nombre': socio['nombre'],
            'apellido': socio['apellido'],
            'ahorro_individual': socio['ahorro_individual'],
            'proporcion': round(proporcion * 100, 2),
            'utilidad': round(utilidad, 2)
        })
    
    return distribucion

def guardar_distribucion_utilidades(id_grupo, distribucion):
    """Guardar la distribución de utilidades en la base de datos"""
    
    # Primero, crear el registro de cierre de ciclo
   