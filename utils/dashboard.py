import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def mostrar_dashboard_personalizado(rol, id_grupo=None):
    """Mostrar dashboard personalizado según el rol"""
    
    if rol == "DIRECTIVA":
        return dashboard_directiva(id_grupo)
    elif rol == "PROMOTORA":
        return dashboard_promotora()
    else:  # ADMIN
        return dashboard_admin()

def dashboard_directiva(id_grupo):
    """Dashboard para directiva de grupo"""
    
    st.title(f"📊 Dashboard Directiva - {st.session_state.nombre_grupo}")
    
    # Métricas en tiempo real
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_socios = obtener_metricas_grupo("COUNT(*)", "socios", id_grupo)
        st.metric("👥 Total Socios", total_socios)
    
    with col2:
        ahorro_total = obtener_ahorro_actual(id_grupo)
        st.metric("💰 Ahorro Actual", f"${ahorro_total:,.2f}")
    
    with col3:
        prestamos_activos = obtener_prestamos_activos(id_grupo)
        st.metric("🏦 Préstamos Activos", prestamos_activos)
    
    with col4:
        tasa_mora = obtener_tasa_mora(id_grupo)
        st.metric("⚠️ Tasa de Mora", f"{tasa_mora:.1f}%")
    
    # Gráficos principales
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Evolución de ahorro
        st.subheader("📈 Evolución del Ahorro")
        datos_ahorro = obtener_evolucion_ahorro(id_grupo)
        if not datos_ahorro.empty:
            fig = px.line(datos_ahorro, x='fecha', y='ahorro', 
                         title='Crecimiento del Ahorro',
                         labels={'fecha': 'Fecha', 'ahorro': 'Ahorro ($)'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        # Estado de préstamos
        st.subheader("🏦 Estado de Préstamos")
        datos_prestamos = obtener_estado_prestamos(id_grupo)
        if not datos_prestamos.empty:
            fig = px.pie(datos_prestamos, values='cantidad', names='estado',
                        title='Distribución por Estado')
            st.plotly_chart(fig, use_container_width=True)
    
    # Alertas y acciones
    st.subheader("🚨 Alertas y Acciones Prioritarias")
    alertas = generar_alertas_directiva(id_grupo)
    
    for alerta in alertas:
        if alerta['nivel'] == 'ALTO':
            st.error(f"🔴 {alerta['mensaje']}")
        elif alerta['nivel'] == 'MEDIO':
            st.warning(f"🟡 {alerta['mensaje']}")
        else:
            st.info(f"🔵 {alerta['mensaje']}")

def dashboard_promotora():
    """Dashboard para promotoras"""
    
    st.title("👩‍💼 Dashboard Promotora")
    
    # Métricas de supervisión
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        grupos_supervisados = obtener_total_grupos_supervisados()
        st.metric("🏢 Grupos Supervisados", grupos_supervisados)
    
    with col2:
        total_socios = obtener_total_socios_supervisados()
        st.metric("👥 Total Socios", total_socios)
    
    with col3:
        ahorro_total = obtener_ahorro_total_supervisado()
        st.metric("💰 Ahorro Total", f"${ahorro_total:,.2f}")
    
    with col4:
        grupos_mora = obtener_grupos_con_mora()
        st.metric("⚠️ Grupos en Mora", grupos_mora)
    
    # Gráficos de comparativa
    st.subheader("📊 Comparativa de Grupos")
    
    datos_comparativa = obtener_datos_comparativa_grupos()
    if not datos_comparativa.empty:
        fig = px.bar(datos_comparativa, x='grupo', y='ahorro', 
                    title='Ahorro por Grupo',
                    labels={'grupo': 'Grupo', 'ahorro': 'Ahorro ($)'})
        st.plotly_chart(fig, use_container_width=True)

def dashboard_admin():
    """Dashboard para administradores"""
    
    st.title("👑 Dashboard Administrador")
    
    # Métricas globales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_grupos = obtener_total_grupos()
        st.metric("🏢 Total Grupos", total_grupos)
    
    with col2:
        total_socios = obtener_total_socios()
        st.metric("👥 Total Socios", total_socios)
    
    with col3:
        ahorro_global = obtener_ahorro_global()
        st.metric("💰 Ahorro Global", f"${ahorro_global:,.2f}")
    
    with col4:
        prestamos_global = obtener_prestamos_global()
        st.metric("🏦 Préstamos Global", prestamos_global)
    
    # KPIs estratégicos
    st.subheader("🎯 KPIs Estratégicos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tasa_crecimiento = obtener_tasa_crecimiento_global()
        st.metric("📈 Tasa de Crecimiento", f"{tasa_crecimiento:.1f}%")
    
    with col2:
        rentabilidad_promedio = obtener_rentabilidad_promedio()
        st.metric("💸 Rentabilidad Promedio", f"{rentabilidad_promedio:.1f}%")
    
    with col3:
        satisfaccion = obtener_indice_satisfaccion()
        st.metric("⭐ Índice Satisfacción", f"{satisfaccion:.1f}/5")
    
    # Mapa de calor de desempeño
    st.subheader("🌡️ Mapa de Calor - Desempeño por Distrito")
    
    datos_desempeno = obtener_datos_desempeno_distritos()
    if not datos_desempeno.empty:
        fig = px.density_heatmap(datos_desempeno, x='distrito', y='metricas',
                               title='Desempeño por Distrito')
        st.plotly_chart(fig, use_container_width=True)

# Funciones auxiliares para los dashboards
def obtener_metricas_grupo(campo, tabla, id_grupo):
    """Obtener métricas específicas del grupo"""
    query = f"SELECT {campo} as valor FROM {tabla} WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['valor'] if resultado else 0

def obtener_ahorro_actual(id_grupo):
    """Obtener ahorro actual del grupo"""
    query = """
        SELECT COALESCE(saldo_cierre, 0) as ahorro
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['ahorro'] if resultado else 0

def obtener_prestamos_activos(id_grupo):
    """Obtener número de préstamos activos"""
    query = """
        SELECT COUNT(*) as total
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo IN (2, 5)
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0

def obtener_tasa_mora(id_grupo):
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
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['tasa'] if resultado else 0

def obtener_evolucion_ahorro(id_grupo):
    """Obtener evolución del ahorro"""
    query = """
        SELECT 
            s.fecha_sesion as fecha,
            a.saldo_cierre as ahorro
        FROM ahorro a
        JOIN sesion s ON a.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def obtener_estado_prestamos(id_grupo):
    """Obtener estado de préstamos"""
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
    resultado = ejecutar_consulta(query, (id_grupo,))
    return pd.DataFrame(resultado) if resultado else pd.DataFrame()

def generar_alertas_directiva(id_grupo):
    """Generar alertas para directiva"""
    alertas = []
    
    # Ejemplo de alertas
    prestamos_mora = obtener_prestamos_mora(id_grupo)
    if prestamos_mora > 0:
        alertas.append({
            'nivel': 'ALTO',
            'mensaje': f'{prestamos_mora} préstamos en mora requieren atención'
        })
    
    return alertas

# Placeholders para funciones de promotora y admin
def obtener_total_grupos_supervisados():
    return 0

def obtener_total_socios_supervisados():
    return 0

def obtener_ahorro_total_supervisado():
    return 0

def obtener_grupos_con_mora():
    return 0

def obtener_datos_comparativa_grupos():
    return pd.DataFrame()

def obtener_total_grupos():
    return 0

def obtener_total_socios():
    return 0

def obtener_ahorro_global():
    return 0

def obtener_prestamos_global():
    return 0

def obtener_tasa_crecimiento_global():
    return 0

def obtener_rentabilidad_promedio():
    return 0

def obtener_indice_satisfaccion():
    return 0

def obtener_datos_desempeno_distritos():
    return pd.DataFrame()

def obtener_prestamos_mora(id_grupo):
    """Obtener número de préstamos en mora"""
    query = """
        SELECT COUNT(*) as total
        FROM prestamo p
        JOIN socios s ON p.id_socio = s.id_socio
        WHERE s.id_grupo = %s AND p.id_estado_prestamo = 5
    """
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['total'] if resultado else 0