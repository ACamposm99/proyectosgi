import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
import json

def generar_pdf_acta(tipo_acta, datos):
    """Función unificada para generar PDF de actas"""
    if tipo_acta == "cierre":
        return generar_pdf_acta_cierre(datos)
    elif tipo_acta == "reunion":
        return generar_pdf_acta_reunion(datos)
    elif tipo_acta == "prestamo":
        return generar_pdf_acta_prestamo(datos)
    else:
        st.error("Tipo de acta no soportado")
        return None

def generar_pdf_acta_cierre(grupo_info, datos_ciclo, distribucion):
    """Generar PDF del acta de cierre"""
    try:
        # Crear buffer para el PDF
        buffer = io.BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = styles['Heading1']
        title_style.alignment = 1  # Centrado
        title = Paragraph("ACTA DE CIERRE DE CICLO", title_style)
        elements.append(title)
        
        elements.append(Spacer(1, 12))
        
        # Información del grupo
        info_text = f"""
        <b>Grupo:</b> {grupo_info['nombre_grupo']}<br/>
        <b>Fecha de Cierre:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
        <b>Período:</b> {datos_ciclo['fecha_inicio'].strftime('%d/%m/%Y')} - {datos_ciclo['fecha_fin'].strftime('%d/%m/%Y')}<br/>
        <b>Lugar:</b> {grupo_info['lugar_reunion']}
        """
        info_paragraph = Paragraph(info_text, styles['Normal'])
        elements.append(info_paragraph)
        
        elements.append(Spacer(1, 20))
        
        # Resumen financiero
        elements.append(Paragraph("RESUMEN FINANCIERO", styles['Heading2']))
        
        resumen_data = [
            ['Concepto', 'Monto'],
            ['Ahorro Total Acumulado', f"${datos_ciclo['ahorro_total']:,.2f}"],
            ['Intereses Cobrados', f"${datos_ciclo['intereses_cobrados']:,.2f}"],
            ['Multas Cobradas', f"${datos_ciclo['multas_cobradas']:,.2f}"],
            ['Gastos Operativos', f"${datos_ciclo['gastos_operativos']:,.2f}"],
            ['Utilidades Netas', f"${sum(d['utilidad'] for d in distribucion):,.2f}"]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[300, 150])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(resumen_table)
        
        elements.append(Spacer(1, 20))
        
        # Distribución por socio
        elements.append(Paragraph("DISTRIBUCIÓN POR SOCIO", styles['Heading2']))
        
        distrib_data = [['Socio', 'Ahorro', 'Utilidad', 'Total a Retirar']]
        for socio in distribucion:
            distrib_data.append([
                f"{socio['nombre']} {socio['apellido']}",
                f"${socio['ahorro_individual']:,.2f}",
                f"${socio['utilidad']:,.2f}",
                f"${socio['total_retiro']:,.2f}"
            ])
        
        distrib_table = Table(distrib_data, colWidths=[200, 100, 100, 120])
        distrib_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        elements.append(distrib_table)
        
        elements.append(Spacer(1, 30))
        
        # Firmas
        firmas_text = """
        <b>FIRMAS DE VALIDACIÓN</b><br/><br/>
        
        _________________________<br/>
        <b>Presidente/a</b><br/><br/>
        
        _________________________<br/>
        <b>Secretario/a</b><br/><br/>
        
        _________________________<br/>
        <b>Tesorero/a</b><br/><br/>
        
        <i>Acta generada automáticamente por el Sistema GAPC</i>
        """
        firmas_paragraph = Paragraph(firmas_text, styles['Normal'])
        elements.append(firmas_paragraph)
        
        # Construir PDF
        doc.build(elements)
        
        # Obtener el PDF del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Crear botón de descarga
        b64 = base64.b64encode(pdf).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="acta_cierre_{grupo_info["nombre_grupo"]}_{datetime.now().strftime("%Y%m%d")}.pdf">📥 Descargar Acta de Cierre (PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        return pdf
        
    except Exception as e:
        st.error(f"Error generando PDF: {e}")
        # Fallback a Excel si hay error con PDF
        return generar_excel_acta_cierre(grupo_info, datos_ciclo, distribucion)

def generar_pdf_acta_reunion(datos_reunion, temas, acuerdos):
    """Generar PDF para acta de reunión"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("ACTA DE REUNIÓN", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información de la reunión
        info_text = f"""
        <b>Grupo:</b> {datos_reunion['nombre_grupo']}<br/>
        <b>Fecha:</b> {datos_reunion['fecha_sesion'].strftime('%d/%m/%Y')}<br/>
        <b>Lugar:</b> {datos_reunion['lugar_reunion']}<br/>
        <b>Asistentes:</b> {datos_reunion['total_presentes']} de {datos_reunion['total_socios']} ({datos_reunion['total_presentes']/datos_reunion['total_socios']*100:.1f}%)<br/>
        <b>Ahorro registrado:</b> ${datos_reunion.get('total_ahorro', 0):,.2f}
        """
        info_paragraph = Paragraph(info_text, styles['Normal'])
        elements.append(info_paragraph)
        
        elements.append(Spacer(1, 20))
        
        # Temas tratados
        if temas:
            elements.append(Paragraph("TEMAS TRATADOS", styles['Heading2']))
            temas_paragraph = Paragraph(temas.replace('\n', '<br/>'), styles['Normal'])
            elements.append(temas_paragraph)
            elements.append(Spacer(1, 12))
        
        # Acuerdos
        if acuerdos:
            elements.append(Paragraph("ACUERDOS Y DECISIONES", styles['Heading2']))
            acuerdos_paragraph = Paragraph(acuerdos.replace('\n', '<br/>'), styles['Normal'])
            elements.append(acuerdos_paragraph)
        
        elements.append(Spacer(1, 30))
        
        # Firmas
        firmas_text = """
        <b>FIRMAS DE VALIDACIÓN</b><br/><br/>
        
        _________________________<br/>
        <b>Presidente/a</b><br/><br/>
        
        _________________________<br/>
        <b>Secretario/a</b><br/><br/>
        
        _________________________<br/>
        <b>Tesorero/a</b><br/>
        """
        firmas_paragraph = Paragraph(firmas_text, styles['Normal'])
        elements.append(firmas_paragraph)
        
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        b64 = base64.b64encode(pdf).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="acta_reunion_{datos_reunion["nombre_grupo"]}_{datos_reunion["fecha_sesion"].strftime("%Y%m%d")}.pdf">📥 Descargar Acta de Reunión (PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        return pdf
        
    except Exception as e:
        st.error(f"Error generando PDF de reunión: {e}")
        return None

def generar_pdf_acta_prestamo(datos_prestamo):
    """Generar PDF para acta de préstamo"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("ACTA DE APROBACIÓN DE PRÉSTAMO", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información del préstamo
        info_text = f"""
        <b>Grupo:</b> {datos_prestamo['nombre_grupo']}<br/>
        <b>Fecha de Aprobación:</b> {datos_prestamo['fecha_aprobacion'].strftime('%d/%m/%Y')}<br/>
        <b>Solicitante:</b> {datos_prestamo['nombre']} {datos_prestamo['apellido']}<br/>
        <b>Teléfono:</b> {datos_prestamo['telefono']}<br/>
        <b>Dirección:</b> {datos_prestamo['direccion']}
        """
        info_paragraph = Paragraph(info_text, styles['Normal'])
        elements.append(info_paragraph)
        
        elements.append(Spacer(1, 20))
        
        # Términos del préstamo
        elements.append(Paragraph("TÉRMINOS DEL PRÉSTAMO", styles['Heading2']))
        
        cuota_mensual = datos_prestamo['total_pagar'] / datos_prestamo['plazo_meses']
        
        prestamo_data = [
            ['Concepto', 'Valor'],
            ['Monto Aprobado', f"${datos_prestamo['monto_solicitado']:,.2f}"],
            ['Plazo', f"{datos_prestamo['plazo_meses']} meses"],
            ['Interés Anual', f"${datos_prestamo['interes_anual']:,.2f}"],
            ['Total a Pagar', f"${datos_prestamo['total_pagar']:,.2f}"],
            ['Cuota Mensual', f"${cuota_mensual:,.2f}"],
            ['Fecha de Vencimiento', datos_prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')]
        ]
        
        prestamo_table = Table(prestamo_data, colWidths=[300, 150])
        prestamo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(prestamo_table)
        
        elements.append(Spacer(1, 20))
        
        # Nota importante
        nota_text = """
        <b>NOTA IMPORTANTE:</b><br/>
        El solicitante se compromete a cumplir con los pagos puntuales según el calendario establecido. 
        El incumplimiento en los pagos generará multas según las reglas del grupo.
        """
        nota_paragraph = Paragraph(nota_text, styles['Normal'])
        elements.append(nota_paragraph)
        
        elements.append(Spacer(1, 30))
        
        # Firmas
        firmas_text = """
        <b>FIRMAS DE AUTORIZACIÓN</b><br/><br/>
        
        _________________________<br/>
        <b>Solicitante</b><br/><br/>
        
        _________________________<br/>
        <b>Presidente/a</b><br/><br/>
        
        _________________________<br/>
        <b>Tesorero/a</b><br/>
        """
        firmas_paragraph = Paragraph(firmas_text, styles['Normal'])
        elements.append(firmas_paragraph)
        
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        b64 = base64.b64encode(pdf).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="acta_prestamo_{datos_prestamo["nombre"]}_{datos_prestamo["apellido"]}_{datetime.now().strftime("%Y%m%d")}.pdf">📥 Descargar Acta de Préstamo (PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        return pdf
        
    except Exception as e:
        st.error(f"Error generando PDF de préstamo: {e}")
        return None

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
    
    return output.getvalue()

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