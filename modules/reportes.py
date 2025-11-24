import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def modulo_reportes():
    """Módulo principal de reportes ejecutivos"""
    
    st.header("📈 Reportes Ejecutivos")
    
    # Determinar tipo de reportes según rol
    if st.session_state.rol == "DIRECTIVA":
        reportes_directiva()
    elif st.session_state.rol == "PROMOTORA":
        reportes_promotora()
    else:  # ADMIN
        reportes_admin()

def reportes_directiva():
    """Reportes para directiva de grupo"""
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede ver estos reportes")
        return
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard Ejecutivo", "💰 Estado Financiero", "📈 Tendencia Ahorro", 
        "👥 Desempeño Socios", "📋 Reporte Detallado"
    ])
    
    with tab1:
        dashboard_ejecutivo_grupo()
    
    with tab2:
        reporte_estado_financiero()
    
    with tab3:
        reporte_tendencia_ahorro()
    
    with tab4:
        reporte_desempeno_socios()
    
    with tab5:
        reporte_detallado_grupo()

def reportes_promotora():
    """Reportes para promotoras"""
    
    st.header("👩‍💼 Reportes de Supervisión - Promotora")
    
    tab1, tab2, tab3 = st.tabs(["🌐 Grupos Supervisados", "📊 Comparativo Grupos", "📈 Tendencia Distrito"])
    
    with tab1:
        reporte_grupos_supervisados()
    
    with tab2:
        reporte_comparativo_grupos()
    
    with tab3:
        reporte_tendencia_distrito()

def reportes_admin():
    """Reportes para administradores"""
    
    st.header("👑 Reportes Gerenciales - Administrador")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Panorama General", "📈 Analytics", "📊 Métricas Clave", "🔍 Drill-Down"
    ])
    
    with tab1:
        reporte_panorama_general()
    
    with tab2:
        reporte_analytics_avanzado()
    
    with tab3:
        reporte_metricas_clave()
    
    with tab4:
        reporte_drill_down()

def dashboard_ejecutivo_grupo():
    """Dashboard ejecutivo para directiva"""
    
    st.subheader("📊 Dashboard Ejecutivo del Grupo")
    
    # Métricas clave en tiempo real
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_socios = obtener_metricas_grupo("COUNT(*)", "socios")
        st.metric("👥 Total Socios", total_socios)
    
    with col2:
        ahorro_total = obtener_metricas_grupo("COALESCE(SUM(saldo_cierre), 0)", "ahorro a JOIN sesion s ON a.id_sesion = s.id_sesion")
        st.metric("💰 Ahorro Total", f"${ahorro_total:,.2f}")
    
    with col3:
        prestamos_activos = obtener_metricas_grupo("COUNT(*)", "prestamo p JOIN socios s ON p.id_socio = s.id_socio WHERE p.id_estado_prestamo IN (2, 5)")
        st.metric("🏦 Préstamos Activos", prestamos_activos)
    
    with col4:
        tasa_mora = obtener_tasa_mora_grupo()
        st.metric("⚠️ Tasa de Mora", f"{tasa_mora:.1f}%")
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        asistencia_promedio = obtener_asistencia_promedio()
        st.metric("📅 Asistencia Promedio", f"{asistencia_promedio:.1f}%")
    
    with col2:
        total_multas = obtener_metricas_grupo("COALESCE(SUM(monto_a_pagar), 0)", "multa m JOIN socios s ON m.id_socio = s.id_socio")
        st.metric("⚖️ Multas Acumuladas", f"${total_multas:,.2f}")
    
    with col3:
        intereses_cobrados = obtener_intereses_cobrados()
        st.metric("📈 Intereses Cobrados", f"${intereses_cobrados:,.2f}")
    
    with col4:
        utilidades_proyectadas = calcular_utilidades_proyectadas()
        st.metric("🎯 Utilidades Proyectadas", f"${utilidades_proyectadas:,.2f}")
    
    # Gráficos principales
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Evolución de ahorro
        st.markdown("### 📈 Evolución del Ahorro")
        datos_ahorro = obtener_evolucion_ahorro()
        if not datos_ahorro.empty:
            fig = px.line(datos_ahorro, x='fecha', y='ahorro', 
                         title='Crecimiento del Ahorro del Grupo',
                         labels={'fecha': 'Fecha', 'ahorro': 'Ahorro Acumulado ($)'})
            fig.update_traces(line=dict(color='#2ecc71', width=3))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ahorro para mostrar")
    
    with col_right:
        # Distribución de préstamos
        st.markdown("### 🏦 Estado de Préstamos")
        datos_prestamos = obtener_estado_prestamos()
        if not datos_prestamos.empty:
            fig = px.pie(datos_prestamos, values='cantidad', names='estado',
                        title='Distribución de Préstamos por Estado',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de préstamos para mostrar")
    
    # Alertas y acciones recomendadas
    st.markdown("### 🚨 Alertas y Recomendaciones")
    
    alertas = generar_alertas_grupo()
    for alerta in alertas:
        if alerta['nivel'] == 'ALTO':
            st.error(f"🔴 {alerta['mensaje']}")
        elif alerta['nivel'] == 'MEDIO':
            st.warning(f"🟡 {alerta['mensaje']}")
        else:
            st.info(f"🔵 {alerta['mensaje']}")

def reporte_estado_financiero():
    """Reporte financiero detallado"""
    
    st.subheader("💰 Estado Financiero Detallado")
    
    # Selector de período
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Desde", datetime.now().replace(day=1), key="fin_desde")
    
    with col2:
        fecha_fin = st.date_input("Hasta", datetime.now(), key="fin_hasta")
    
    if st.button("🔄 Generar Reporte Financiero"):
        with st.spinner("Generando reporte financiero..."):
            datos_financieros = obtener_datos_financieros(fecha_inicio, fecha_fin)
            
            if datos_financieros:
                # Resumen ejecutivo
                st.markdown("### 📊 Resumen Ejecutivo")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📥 Total Ingresos", f"${datos_financieros['total_ingresos']:,.2f}")
                
                with col2:
                    st.metric("📤 Total Egresos", f"${datos_financieros['total_egresos']:,.2f}")
                
                with col3:
                    st.metric("📊 Saldo Neto", f"${datos_financieros['saldo_neto']:,.2f}")
                
                with col4:
                    st.metric("📈 Rentabilidad", f"{datos_financieros['rentabilidad']:.1f}%")
                
                # Gráfico de flujo de caja
                st.markdown("### 💸 Flujo de Caja")
                
                flujo_data = pd.DataFrame({
                    'Categoría': ['Ingresos', 'Egresos', 'Saldo Neto'],
                    'Monto': [
                        datos_financieros['total_ingresos'],
                        datos_financieros['total_egresos'],
                        datos_financieros['saldo_neto']
                    ]
                })
                
                fig = px.bar(flujo_data, x='Categoría', y='Monto',
                            title='Flujo de Caja del Período',
                            color='Categoría',
                            color_discrete_map={
                                'Ingresos': '#2ecc71',
                                'Egresos': '#e74c3c', 
                                'Saldo Neto': '#3498db'
                            })
                st.plotly_chart(fig, use_container_width=True)
                
                # Detalle de movimientos
                st.markdown("### 📋 Detalle de Movimientos")
                st.dataframe(datos_financieros['movimientos'], use_container_width=True)
                
                # Exportar opción
                csv = datos_financieros['movimientos'].to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"reporte_financiero_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.error("No se pudieron generar los datos financieros")

def reporte_tendencia_ahorro():
    """Reporte de tendencia de ahorro"""
    
    st.subheader("📈 Tendencia y Proyección de Ahorro")
    
    # Obtener datos históricos
    datos_historicos = obtener_datos_ahorro_historico()
    
    if datos_historicos.empty:
        st.info("No hay datos históricos de ahorro")
        return
    
    # Gráfico de tendencia
    fig = px.line(datos_historicos, x='fecha', y='ahorro_acumulado',
                 title='Tendencia de Ahorro Acumulado',
                 labels={'fecha': 'Fecha', 'ahorro_acumulado': 'Ahorro Acumulado ($)'})
    
    # Añadir línea de tendencia
    if len(datos_historicos) > 1:
        z = np.polyfit(range(len(datos_historicos)), datos_historicos['ahorro_acumulado'], 1)
        p = np.poly1d(z)
        datos_historicos['tendencia'] = p(range(len(datos_historicos)))
        
        fig.add_scatter(x=datos_historicos['fecha'], y=datos_historicos['tendencia'],
                       mode='lines', name='Tendencia', line=dict(dash='dash'))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Estadísticas de crecimiento
    st.markdown("### 📊 Estadísticas de Crecimiento")
    
    if len(datos_historicos) > 1:
        crecimiento_total = datos_historicos['ahorro_acumulado'].iloc[-1] - datos_historicos['ahorro_acumulado'].iloc[0]
        tasa_crecimiento = (crecimiento_total / datos_historicos['ahorro_acumulado'].iloc[0]) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Crecimiento Total", f"${crecimiento_total:,.2f}")
        
        with col2:
            st.metric("Tasa de Crecimiento", f"{tasa_crecimiento:.1f}%")
        
        with col3:
            # Proyección (simplificada)
            if len(datos_historicos) >= 3:
                crecimiento_promedio = datos_historicos['ahorro_acumulado'].diff().mean()
                proyeccion = datos_historicos['ahorro_acumulado'].iloc[-1] + (crecimiento_promedio * 6)  # 6 meses
                st.metric("Proyección 6 meses", f"${proyeccion:,.2f}")

def reporte_desempeno_socios():
    """Reporte de desempeño individual de socios"""
    
    st.subheader("👥 Desempeño Individual de Socios")
    
    # Obtener datos de socios
    datos_socios = obtener_datos_desempeno_socios()
    
    if datos_socios.empty:
        st.info("No hay datos de desempeño de socios")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        metricas = st.selectbox("Métrica a visualizar", 
                               ["Ahorro Acumulado", "Asistencia", "Préstamos", "Puntualidad Pagos"])
    
    with col2:
        top_n = st.slider("Mostrar top", 5, 20, 10)
    
    # Ranking de socios
    st.markdown(f"### 🏆 Top {top_n} Socios - {metricas}")
    
    if metricas == "Ahorro Acumulado":
        datos_ranking = datos_socios.nlargest(top_n, 'ahorro_acumulado')
        fig = px.bar(datos_ranking, x='ahorro_acumulado', y='nombre_completo',
                    orientation='h', title='Top Socios por Ahorro Acumulado')
    elif metricas == "Asistencia":
        datos_ranking = datos_socios.nlargest(top_n, 'porcentaje_asistencia')
        fig = px.bar(datos_ranking, x='porcentaje_asistencia', y='nombre_completo',
                    orientation='h', title='Top Socios por Asistencia')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla detallada
    st.markdown("### 📋 Detalle Completo de Socios")
    st.dataframe(datos_socios, use_container_width=True)

def reporte_detallado_grupo():
    """Reporte detallado del grupo"""
    
    st.subheader("📋 Reporte Detallado del Grupo")
    
    # Generar reporte completo
    if st.button("🔄 Generar Reporte Completo"):
        with st.spinner("Generando reporte detallado..."):
            reporte_completo = generar_reporte_completo_grupo()
            
            # Mostrar diferentes secciones del reporte
            for seccion, datos in reporte_completo.items():
                with st.expander(f"📖 {seccion}"):
                    if isinstance(datos, pd.DataFrame):
                        st.dataframe(datos, use_container_width=True)
                    else:
                        st.write(datos)

# =============================================================================
# FUNCIONES AUXILIARES - REPORTES
# =============================================================================

def obtener_metricas_grupo(campo, tabla_condicion):
    """Obtener métricas del grupo"""
    query = f"SELECT {campo} as valor FROM {tabla_condicion} WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (st.session_state.id_grupo,))
    return resultado[0]['valor'] if resultado else 0

def obtener_tasa_mora_grupo():
    """Calcular tasa de mora del grupo"""
    query = """
        SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN 0
                ELSE SUM(CASE WHEN p.id_estado_prestamo = 5 THEN 1 ELSE 0 END) / COUNT(*) * 100
            END as tasa
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo IN (2, 5)
    """
    resultado = ejecutar_consulta(query, (st.session_state.id_grupo,))
    return resultado[0]['tasa'] if resultado else 0

def obtener_asistencia_promedio():
    """Calcular asistencia promedio"""
    query = """
        SELECT AVG((total_presentes * 100) / (SELECT COUNT(*) FROM socios WHERE id_grupo = %s)) as promedio
        FROM sesion
        WHERE id_grupo = %s AND total_presentes > 0
    """
    resultado = ejecutar_consulta(query, (st.session_state.id_grupo, st.session_state.id_grupo))
    return resultado[0]['promedio'] if resultado else 0

def obtener_intereses_cobrados():
    """Obtener intereses cobrados en el ciclo"""
    ciclo_info = obtener_info_ciclo_actual(st.session_state.id_grupo)
    if not ciclo_info:
        return 0
    
    query = """
        SELECT COALESCE(SUM(interes_pagado), 0) as total
        FROM `detalle de pagos` dp
        JOIN prestamo p ON dp.id_prestamo = p.id_prestamo
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s
        AND dp.fecha_pago BETWEEN %s AND %s
    """
    resultado = ejecutar_consulta(query, (st.session_state.id_grupo, ciclo_info['fecha_inicio_ciclo'], ciclo_info['fecha_fin_ciclo']))
    return resultado[0]['total'] if resultado else 0

def calcular_utilidades_proyectadas():
    """Calcular utilidades proyectadas al cierre"""
    intereses = obtener_intereses_cobrados()
    multas = obtener_metricas_grupo("COALESCE(SUM(monto_a_pagar), 0)", "multa m JOIN socios s ON m.id_socio = s.id_socio")
    gastos = obtener_metricas_grupo("COALESCE(SUM(monto), 0)", "movimiento_de_caja mc JOIN caja c ON mc.id_caja = c.id_caja JOIN sesion s ON c.id_sesion = s.id_sesion WHERE mc.id_tipomovimiento IN (3, 6, 7)")
    
    return (intereses + multas) - abs(gastos)

def obtener_evolucion_ahorro():
    """Obtener evolución del ahorro del grupo"""
    query = """
        SELECT 
            s.fecha_sesion as fecha,
            a.saldo_cierre as ahorro
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion
    """
    resultado = ejecutar_consulta(query, (st.session_state.id_grupo,))
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def obtener_estado_prestamos():
    """Obtener estado de los préstamos"""
    query = """
        SELECT 
            ep.estados as estado,
            COUNT(*) as cantidad
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        JOIN estado_del_prestamo ep ON p.id_estado_prestamo = ep.id_estadoprestamo
        WHERE s.id_grupo = %s
        GROUP BY ep.estados
    """
    resultado = ejecutar_consulta(query, (st.session_state.id_grupo,))
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def generar_alertas_grupo():
    """Generar alertas para el grupo"""
    alertas = []
    
    # Verificar préstamos en mora
    prestamos_mora = obtener_metricas_grupo("COUNT(*)", "prestamo p JOIN socios s ON p.id_socio = s.id_socio WHERE p.id_estado_prestamo = 5")
    if prestamos_mora > 0:
        alertas.append({
            'nivel': 'ALTO',
            'mensaje': f'Existen {prestamos_mora} préstamos en mora que requieren atención inmediata'
        })
    
    # Verificar asistencia baja
    asistencia = obtener_asistencia_promedio()
    if asistencia < 70:
        alertas.append({
            'nivel': 'MEDIO',
            'mensaje': f'La asistencia promedio ({asistencia:.1f}%) está por debajo del 70% recomendado'
        })
    
    # Verificar ciclo próximo a vencer
    ciclo_info = obtener_info_ciclo_actual(st.session_state.id_grupo)
    if ciclo_info:
        dias_restantes = (ciclo_info['fecha_fin_ciclo'] - datetime.now().date()).days
        if dias_restantes < 30:
            alertas.append({
                'nivel': 'MEDIO',
                'mensaje': f'El ciclo actual finaliza en {dias_restantes} días. Prepare el cierre.'
            })
    
    return alertas

def obtener_datos_financieros(fecha_inicio, fecha_fin):
    """Obtener datos financieros para reporte"""
    
    query = """
        SELECT 
            s.fecha_sesion as fecha,
            tm.nombre_movimiento as tipo,
            m.monto,
            m.descripcion,
            COALESCE(CONCAT(soc.nombre, ' ', soc.apellido), 'Grupo') as socio,
            CASE WHEN m.monto > 0 THEN 'INGRESO' ELSE 'EGRESO' END as categoria
        FROM movimiento_de_caja m
        JOIN caja c ON m.id_caja = c.id_caja
        JOIN sesion s ON c.id_sesion = s.id_sesion
        JOIN tipo_de_movimiento_de_caja tm ON m.id_tipomovimiento = tm.id_tipomovimiento
        LEFT JOIN socios soc ON m.id_socio = soc.id_socio
        WHERE s.id_grupo = %s
        AND s.fecha_sesion BETWEEN %s AND %s
        ORDER BY s.fecha_sesion DESC
    """
    
    movimientos = ejecutar_consulta(query, (st.session_state.id_grupo, fecha_inicio, fecha_fin))
    
    if not movimientos:
        return None
    
    df_movimientos = pd.DataFrame(movimientos)
    
    # Calcular totales
    total_ingresos = df_movimientos[df_movimientos['categoria'] == 'INGRESO']['monto'].sum()
    total_egresos = df_movimientos[df_movimientos['categoria'] == 'EGRESO']['monto'].sum()
    saldo_neto = total_ingresos + total_egresos  # Los egresos son negativos
    
    rentabilidad = (saldo_neto / total_ingresos * 100) if total_ingresos > 0 else 0
    
    return {
        'total_ingresos': total_ingresos,
        'total_egresos': abs(total_egresos),
        'saldo_neto': saldo_neto,
        'rentabilidad': rentabilidad,
        'movimientos': df_movimientos
    }

# Las siguientes funciones son placeholders para los reportes de promotora y admin
def reporte_grupos_supervisados():
    st.info("🔧 Reporte de grupos supervisados - En desarrollo")

def reporte_comparativo_grupos():
    st.info("🔧 Reporte comparativo de grupos - En desarrollo")

def reporte_tendencia_distrito():
    st.info("🔧 Reporte de tendencia distrito - En desarrollo")

def reporte_panorama_general():
    st.info("🔧 Reporte panorama general - En desarrollo")

def reporte_analytics_avanzado():
    st.info("🔧 Analytics avanzado - En desarrollo")

def reporte_metricas_clave():
    st.info("🔧 Métricas clave - En desarrollo")

def reporte_drill_down():
    st.info("🔧 Drill-down - En desarrollo")

def obtener_datos_ahorro_historico():
    """Obtener datos históricos de ahorro"""
    return pd.DataFrame()

def obtener_datos_desempeno_socios():
    """Obtener datos de desempeño de socios"""
    return pd.DataFrame()

def generar_reporte_completo_grupo():
    """Generar reporte completo del grupo"""
    return {}

def obtener_info_ciclo_actual(id_grupo):
    """Obtener información del ciclo actual"""
    query = """
        SELECT fecha_inicio_ciclo, fecha_fin_ciclo
        FROM reglas_del_grupo
        WHERE id_grupo = %s
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0] if resultado else None