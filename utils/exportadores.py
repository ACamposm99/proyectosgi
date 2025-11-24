import streamlit as st
import pandas as pd
from datetime import datetime
import io

def generar_pdf_acta_cierre(grupo_info, datos_ciclo, distribucion):
    """Generar PDF del acta de cierre (placeholder)"""
    
    # En una implementación real, aquí se usaría una librería como ReportLab
    # Para esta demo, generamos un Excel como alternativa
    
    return generar_excel_acta_cierre(grupo_info, datos_ciclo, distribucion)

def generar_excel_acta_cierre(grupo_info, datos_ciclo, distribucion):
    """Generar Excel del acta de cierre"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Hoja de resumen
        resumen_data = {
            'Concepto': [
                'Grupo',
                'Fecha de Cierre', 
                'Período del Ciclo',
                'Ahorro Total',
                'Intereses Cobrados',
                'Multas Cobradas',
                'Gastos Operativos',
                'Utilidades Netas'
            ],
            'Valor': [
                grupo_info['nombre_grupo'],
                datetime.now().strftime("%d/%m/%Y"),
                f"{datos_ciclo['fecha_inicio'].strftime('%d/%m/%Y')} - {datos_ciclo['fecha_fin'].strftime('%d/%m/%Y')}",
                f"${datos_ciclo['ahorro_total']:,.2f}",
                f"${datos_ciclo['intereses_cobrados']:,.2f}",
                f"${datos_ciclo['multas_cobradas']:,.2f}",
                f"${datos_ciclo['gastos_operativos']:,.2f}",
                f"${sum(d['utilidad'] for d in distribucion):,.2f}"
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
        
        # Hoja de distribución
        df_distribucion = pd.DataFrame(distribucion)
        df_distribucion.to_excel(writer, sheet_name='Distribución por Socio', index=False)
        
        # Formatear el Excel
        workbook = writer.book
        format_currency = workbook.add_format({'num_format': '$#,##0.00'})
        
        worksheet = writer.sheets['Distribución por Socio']
        worksheet.set_column('D:F', 15, format_currency)
    
    output.seek(0)
    
    # Descargar el archivo
    st.download_button(
        label="📥 Descargar Acta de Cierre (Excel)",
        data=output,
        file_name=f"acta_cierre_{grupo_info['nombre_grupo']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.ms-excel"
    )

def exportar_reporte_completo(datos):
    """Exportar reporte completo en múltiples formatos"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Exportar a Excel"):
            exportar_excel_completo(datos)
    
    with col2:
        if st.button("📄 Exportar a CSV"):
            exportar_csv_completo(datos)
    
    with col3:
        if st.button("📋 Exportar a JSON"):
            exportar_json_completo(datos)

def exportar_excel_completo(datos):
    """Exportar datos completos a Excel"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for hoja, df in datos.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Limitar nombre de hoja a 31 caracteres
                nombre_hoja = hoja[:31]
                df.to_excel(writer, sheet_name=nombre_hoja, index=False)
    
    output.seek(0)
    
    st.download_button(
        label="📥 Descargar Excel Completo",
        data=output,
        file_name=f"reporte_completo_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.ms-excel"
    )

def exportar_csv_completo(datos):
    """Exportar datos a múltiples archivos CSV"""
    
    for nombre, df in datos.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            csv = df.to_csv(index=False)
            
            st.download_button(
                label=f"📥 {nombre}.csv",
                data=csv,
                file_name=f"{nombre}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key=f"csv_{nombre}"
            )

def exportar_json_completo(datos):
    """Exportar datos a JSON"""
    import json
    
    datos_json = {}
    for nombre, df in datos.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            datos_json[nombre] = df.to_dict('records')
    
    json_str = json.dumps(datos_json, indent=2, default=str)
    
    st.download_button(
        label="📥 Descargar JSON Completo",
        data=json_str,
        file_name=f"reporte_completo_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )