import streamlit as st
from modules.database import ejecutar_consulta, ejecutar_comando
from datetime import datetime

def modulo_caja():
    """Módulo principal para gestión de caja"""
    
    st.header("💳 Gestión de Caja")
    
    tab1, tab2, tab3 = st.tabs(["📊 Estado de Caja", "📥 Ingresos", "📤 Egresos"])
    
    with tab1:
        estado_caja()
    
    with tab2:
        registrar_ingresos()
    
    with tab3:
        registrar_egresos()

def estado_caja():
    """Mostrar estado actual de la caja"""
    
    st.subheader("Estado Actual de Caja")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede ver el estado de caja")
        return
    
    # Obtener último registro de caja
    ultima_caja = obtener_ultimo_estado_caja(st.session_state.id_grupo)
    
    if ultima_caja:
        caja = ultima_caja[0]
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Saldo Apertura", f"${caja['saldo_apertura']:,.2f}")
        
        with col2:
            st.metric("📥 Total Ingresos", f"${caja['total_ingresos']:,.2f}")
        
        with col3:
            st.metric("📤 Total Egresos", f"${caja['total_egresos']:,.2f}")
        
        with col4:
            st.metric("🏦 Saldo Cierre", f"${caja['saldo_cierre']:,.2f}")
        
        # Movimientos recientes
        st.markdown("### Movimientos Recientes")
        movimientos = obtener_movimientos_recientes(caja['id_caja'])
        
        if movimientos:
            for movimiento in movimientos:
                tipo_icono = "📥" if movimiento['tipo'] == 'INGRESO' else "📤"
                color = "green" if movimiento['tipo'] == 'INGRESO' else "red"
                
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding-left: 10px; margin: 5px 0;">
                    {tipo_icono} **${movimiento['monto']:,.2f}** - {movimiento['descripcion']}
                    <br><small>{movimiento['fecha'].strftime('%d/%m/%Y %H:%M')} | {movimiento['socio']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No hay movimientos registrados para esta sesión")
    
    else:
        st.info("ℹ️ No hay registros de caja para este grupo")

def registrar_ingresos():
    """Registrar ingresos a la caja"""
    
    st.subheader("Registrar Ingresos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede registrar ingresos")
        return
    
    with st.form("form_ingreso_caja"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_ingreso = st.selectbox(
                "Tipo de Ingreso",
                ["Ahorro", "Multa", "Donación", "Rifa", "Otros"]
            )
            
            monto = st.number_input("Monto", min_value=0.0, step=10.0)
            
            # Seleccionar socio si aplica
            socios = obtener_socios_grupo(st.session_state.id_grupo)
            socio_seleccionado = st.selectbox(
                "Socio (si aplica)",
                ["Seleccionar..."] + [f"{s['nombre']} {s['apellido']}" for s in socios]
            )
        
        with col2:
            descripcion = st.text_area("Descripción", placeholder="Descripción detallada del ingreso...")
            
            fecha_registro = st.date_input("Fecha", datetime.now().date())
        
        if st.form_submit_button("💾 Registrar Ingreso"):
            if monto > 0 and descripcion:
                # Obtener o crear registro de caja para la fecha
                id_caja = obtener_o_crear_caja(st.session_state.id_grupo, fecha_registro)
                
                if id_caja:
                    id_socio = None
                    if socio_seleccionado != "Seleccionar...":
                        # Extraer ID del socio seleccionado
                        for socio in socios:
                            if f"{socio['nombre']} {socio['apellido']}" == socio_seleccionado:
                                id_socio = socio['id_socio']
                                break
                    
                    if registrar_movimiento_caja(id_caja, 'INGRESO', id_socio, monto, descripcion):
                        st.success("✅ Ingreso registrado exitosamente")
                        
                        # Actualizar totales de caja
                        actualizar_totales_caja(id_caja)
                        st.rerun()
            else:
                st.error("❌ Complete todos los campos obligatorios")

def registrar_egresos():
    """Registrar egresos de la caja"""
    
    st.subheader("Registrar Egresos")
    
    if not st.session_state.id_grupo:
        st.warning("⚠️ Solo la directiva de un grupo puede registrar egresos")
        return
    
    with st.form("form_egreso_caja"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_egreso = st.selectbox(
                "Tipo de Egreso",
                ["Gastos Operativos", "Préstamo", "Devolución", "Otros"]
            )
            
            monto = st.number_input("Monto", min_value=0.0, step=10.0, key="egreso_monto")
            
            # Verificar saldo disponible
            saldo_disponible = obtener_saldo_disponible(st.session_state.id_grupo)
            st.info(f"Saldo disponible: ${saldo_disponible:,.2f}")
            
            if monto > saldo_disponible:
                st.error("❌ Monto superior al saldo disponible")
        
        with col2:
            descripcion = st.text_area("Descripción", placeholder="Descripción detallada del egreso...", key="egreso_desc")
            
            fecha_registro = st.date_input("Fecha", datetime.now().date(), key="egreso_fecha")
            
            beneficiario = st.text_input("Beneficiario", placeholder="Persona o concepto que recibe el pago")
        
        if st.form_submit_button("💾 Registrar Egreso"):
            if monto > 0 and descripcion and monto <= saldo_disponible:
                # Obtener o crear registro de caja para la fecha
                id_caja = obtener_o_crear_caja(st.session_state.id_grupo, fecha_registro)
                
                if id_caja:
                    if registrar_movimiento_caja(id_caja, 'EGRESO', None, monto, f"{descripcion} - {beneficiario}"):
                        st.success("✅ Egreso registrado exitosamente")
                        
                        # Actualizar totales de caja
                        actualizar_totales_caja(id_caja)
                        st.rerun()
            else:
                st.error("❌ Complete todos los campos y verifique el saldo")

# =============================================================================
# FUNCIONES AUXILIARES - CAJA
# =============================================================================

def obtener_ultimo_estado_caja(id_grupo):
    """Obtener el último estado de caja del grupo"""
    query = """
        SELECT c.*, s.fecha_sesion
        FROM caja c
        JOIN sesion s ON c.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """
    return ejecutar_consulta(query, (id_grupo,))

def obtener_movimientos_recientes(id_caja, limite=10):
    """Obtener movimientos recientes de caja"""
    query = """
        SELECT m.monto, m.descripcion, m.hora_registro as fecha,
               CASE WHEN m.id_tipomovimiento IN (1,2,4,5) THEN 'INGRESO' ELSE 'EGRESO' END as tipo,
               COALESCE(CONCAT(s.nombre, ' ', s.apellido), 'Grupo') as socio
        FROM movimiento_de_caja m
        LEFT JOIN socios s ON m.id_socio = s.id_socio
        WHERE m.id_caja = %s
        ORDER BY m.hora_registro DESC
        LIMIT %s
    """
    return ejecutar_consulta(query, (id_caja, limite))

def obtener_socios_grupo(id_grupo):
    """Obtener todos los socios de un grupo"""
    query = "SELECT id_socio, nombre, apellido FROM socios WHERE id_grupo = %s"
    return ejecutar_consulta(query, (id_grupo,))

def obtener_o_crear_caja(id_grupo, fecha):
    """Obtener o crear registro de caja para una fecha"""
    
    # Buscar sesión para esta fecha
    sesion = ejecutar_consulta(
        "SELECT id_sesion FROM sesion WHERE id_grupo = %s AND fecha_sesion = %s",
        (id_grupo, fecha)
    )
    
    if not sesion:
        # Crear sesión para esta fecha
        id_sesion = ejecutar_comando(
            "INSERT INTO sesion (id_grupo, fecha_sesion, total_presentes) VALUES (%s, %s, 0)",
            (id_grupo, fecha)
        )
    else:
        id_sesion = sesion[0]['id_sesion']
    
    # Buscar caja para esta sesión
    caja = ejecutar_consulta("SELECT id_caja FROM caja WHERE id_sesion = %s", (id_sesion,))
    
    if not caja:
        # Obtener último saldo de caja
        ultimo_saldo = obtener_ultimo_saldo_caja(id_grupo)
        
        # Crear nueva caja
        id_caja = ejecutar_comando("""
            INSERT INTO caja (id_sesion, saldo_apertura, total_ingresos, total_egresos, saldo_cierre, firma_tesorera, firma_presidenta)
            VALUES (%s, %s, 0, 0, %s, '', '')
        """, (id_sesion, ultimo_saldo, ultimo_saldo))
        
        return id_caja
    else:
        return caja[0]['id_caja']

def obtener_ultimo_saldo_caja(id_grupo):
    """Obtener el último saldo de caja del grupo"""
    query = """
        SELECT c.saldo_cierre 
        FROM caja c
        JOIN sesion s ON c.id_sesion = s.id_sesion
        WHERE s.id_grupo = %s
        ORDER BY s.fecha_sesion DESC
        LIMIT 1
    """
    
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['saldo_cierre'] if resultado else 0

def registrar_movimiento_caja(id_caja, tipo, id_socio, monto, descripcion):
    """Registrar movimiento de caja"""
    
    # Determinar tipo de movimiento
    id_tipomovimiento = 1 if tipo == 'INGRESO' else 3  # Simplificado
    
    query = """
        INSERT INTO movimiento_de_caja (id_caja, id_tipomovimiento, id_socio, monto, descripcion, hora_registro)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    return ejecutar_comando(query, (id_caja, id_tipomovimiento, id_socio, monto, descripcion, datetime.now()))

def actualizar_totales_caja(id_caja):
    """Actualizar totales en el registro de caja"""
    
    # Calcular totales
    total_ingresos = ejecutar_consulta("""
        SELECT COALESCE(SUM(monto), 0) as total 
        FROM movimiento_de_caja 
        WHERE id_caja = %s AND id_tipomovimiento IN (1,2,4,5)
    """, (id_caja,))[0]['total']
    
    total_egresos = ejecutar_consulta("""
        SELECT COALESCE(SUM(monto), 0) as total 
        FROM movimiento_de_caja 
        WHERE id_caja = %s AND id_tipomovimiento IN (3,6,7)
    """, (id_caja,))[0]['total']
    
    # Obtener saldo apertura
    saldo_apertura = ejecutar_consulta("SELECT saldo_apertura FROM caja WHERE id_caja = %s", (id_caja,))[0]['saldo_apertura']
    
    # Calcular saldo cierre
    saldo_cierre = saldo_apertura + total_ingresos - total_egresos
    
    # Actualizar caja
    query = """
        UPDATE caja 
        SET total_ingresos = %s, total_egresos = %s, saldo_cierre = %s 
        WHERE id_caja = %s
    """
    
    return ejecutar_comando(query, (total_ingresos, total_egresos, saldo_cierre, id_caja))

def obtener_saldo_disponible(id_grupo):
    """Obtener saldo disponible en caja"""
    ultima_caja = obtener_ultimo_estado_caja(id_grupo)
    return ultima_caja[0]['saldo_cierre'] if ultima_caja else 0