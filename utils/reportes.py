import streamlit as st
from modules.database import ejecutar_consulta
from datetime import datetime

def generar_comprobante_ahorro(id_socio, id_sesion):
    """Generar comprobante digital de ahorro para un socio"""
    
    # Obtener datos del socio y del ahorro
    query = """
        SELECT s.nombre, s.apellido, s.telefono, 
               ad.saldo_ahorro, ad.saldo_ingresado, ad.otras_actividades, ad.saldo_final,
               se.fecha_sesion, g.nombre_grupo
        FROM ahorro_detalle ad
        JOIN socios s ON ad.id_socio = s.id_socio
        JOIN ahorro a ON ad.id_ahorro = a.id_ahorro
        JOIN sesion se ON a.id_sesion = se.id_sesion
        JOIN grupos g ON se.id_grupo = g.id_grupo
        WHERE ad.id_socio = %s AND ad.id_ahorro IN (SELECT id_ahorro FROM ahorro WHERE id_sesion = %s)
    """
    
    datos = ejecutar_consulta(query, (id_socio, id_sesion))
    
    if not datos:
        st.error("❌ No se encontraron datos para generar el comprobante")
        return
    
    datos = datos[0]
    
    # Generar comprobante
    st.markdown(f"""
    <div style="border: 2px solid #4CAF50; padding: 20px; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="text-align: center; color: #4CAF50;">🏦 COMPROBANTE DE AHORRO</h2>
        <hr>
        <p><strong>Grupo:</strong> {datos['nombre_grupo']}</p>
        <p><strong>Fecha:</strong> {datos['fecha_sesion'].strftime('%d/%m/%Y')}</p>
        <p><strong>Socio:</strong> {datos['nombre']} {datos['apellido']}</p>
        <p><strong>Teléfono:</strong> {datos['telefono']}</p>
        <hr>
        <p><strong>Saldo Anterior:</strong> ${datos['saldo_ahorro']:,.2f}</p>
        <p><strong>Aporte Actual:</strong> ${datos['saldo_ingresado']:,.2f}</p>
        <p><strong>Otros Ingresos:</strong> ${datos['otras_actividades']:,.2f}</p>
        <p><strong>Nuevo Saldo:</strong> ${datos['saldo_final']:,.2f}</p>
        <hr>
        <p style="text-align: center;"><em>Comprobante generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón para imprimir o descargar
    # En una implementación real, podríamos generar un PDF aquí

def generar_reporte_asistencia(id_sesion):
    """Generar reporte de asistencia para una reunión"""
    
    query = """
        SELECT s.nombre, s.apellido, 
               CASE WHEN a.presencial = 1 THEN '✅ Presente' ELSE '❌ Ausente' END as estado
        FROM asistencia a
        JOIN socios s ON a.id_socio = s.id_socio
        WHERE a.id_sesion = %s
        ORDER BY s.apellido, s.nombre
    """
    
    datos = ejecutar_consulta(query, (id_sesion,))
    
    if datos:
        st.markdown("### 📊 Reporte de Asistencia")
        
        for dato in datos:
            st.write(f"- **{dato['nombre']} {dato['apellido']}**: {dato['estado']}")
    else:
        st.info("ℹ️ No hay datos de asistencia para esta reunión")