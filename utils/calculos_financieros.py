import streamlit as st
from modules.database import ejecutar_consulta

def calcular_cuotas_prestamo(monto, tasa_interes_anual, plazo_meses):
    """
    Calcular cuotas de préstamo usando sistema de amortización francés
    (cuota fija mensual)
    """
    
    # Convertir tasa anual a mensual
    tasa_mensual = tasa_interes_anual / 12
    
    # Fórmula de cuota fija
    if tasa_mensual == 0:
        cuota_mensual = monto / plazo_meses
    else:
        factor = (1 + tasa_mensual) ** plazo_meses
        cuota_mensual = monto * (tasa_mensual * factor) / (factor - 1)
    
    # Calcular tabla de amortización
    saldo = monto
    amortizacion = []
    interes_total = 0
    
    for mes in range(1, plazo_meses + 1):
        interes_mes = saldo * tasa_mensual
        capital_mes = cuota_mensual - interes_mes
        saldo -= capital_mes
        
        # Ajuste para el último mes
        if mes == plazo_meses:
            capital_mes += saldo  # Ajustar por redondeo
            saldo = 0
        
        amortizacion.append({
            'mes': mes,
            'cuota': cuota_mensual,
            'capital': capital_mes,
            'interes': interes_mes,
            'saldo': max(0, saldo)
        })
        
        interes_total += interes_mes
    
    return {
        'cuota_mensual': round(cuota_mensual, 2),
        'interes_total': round(interes_total, 2),
        'total_pagar': round(monto + interes_total, 2),
        'amortizacion': amortizacion
    }

def validar_capacidad_pago(id_socio, monto_solicitado, plazo_meses, id_grupo):
    """
    Validar capacidad de pago del socio para un nuevo préstamo
    """
    
    # Obtener información del socio
    query = """
        SELECT 
            COALESCE((
                SELECT saldo_final 
                FROM ahorro_detalle ad 
                JOIN ahorro a ON ad.id_ahorro = a.id_ahorro 
                JOIN sesion se ON a.id_sesion = se.id_sesion 
                WHERE ad.id_socio = s.id_socio 
                ORDER BY se.fecha_sesion DESC 
                LIMIT 1
            ), 0) as saldo_ahorro,
            (
                SELECT COUNT(*) 
                FROM prestamo 
                WHERE id_socio = s.id_socio 
                AND id_estado_prestamo IN (2, 5)  -- Aprobado o En Mora
            ) as prestamos_activos,
            (
                SELECT COALESCE(SUM(cuota_mensual), 0)
                FROM (
                    SELECT 
                        (capital_pagado + interes_pagado) as cuota_mensual
                    FROM `detalle de pagos` dp
                    JOIN prestamo p ON dp.id_prestamo = p.id_prestamo
                    WHERE p.id_socio = s.id_socio 
                    AND p.id_estado_prestamo IN (2, 5)
                    GROUP BY p.id_prestamo
                ) as cuotas
            ) as cuotas_actuales
        FROM socios s
        WHERE s.id_socio = %s
    """
    
    resultado = ejecutar_consulta(query, (id_socio,))
    
    if not resultado:
        return {'aprobado': False, 'mensaje': 'No se pudo obtener información del socio'}
    
    info_socio = resultado[0]
    
    # Calcular cuota del nuevo préstamo
    tasa_interes = obtener_tasa_interes_grupo(id_grupo)
    cuota_nueva = calcular_cuotas_prestamo(monto_solicitado, tasa_interes, plazo_meses)['cuota_mensual']
    
    # Reglas de validación
    cuota_total = info_socio['cuotas_actuales'] + cuota_nueva
    
    # Regla 1: Cuota no debe exceder el 40% del saldo de ahorro
    if cuota_total > info_socio['saldo_ahorro'] * 0.4:
        return {
            'aprobado': False, 
            'mensaje': f'La cuota total (${cuota_total:,.2f}) excede el 40% de su ahorro (${info_socio["saldo_ahorro"]:,.2f})'
        }
    
    # Regla 2: No más de un préstamo activo si la regla del grupo lo establece
    reglas_grupo = ejecutar_consulta(
        "SELECT unprestamo_alavez FROM reglas_del_grupo WHERE id_grupo = %s",
        (id_grupo,)
    )
    
    if reglas_grupo and reglas_grupo[0]['unprestamo_alavez'] and info_socio['prestamos_activos'] > 0:
        return {
            'aprobado': False,
            'mensaje': 'Ya tiene un préstamo activo y el grupo no permite múltiples préstamos'
        }
    
    # Regla 3: El monto no debe exceder cierto múltiplo del ahorro
    if monto_solicitado > info_socio['saldo_ahorro'] * 3:
        return {
            'aprobado': False,
            'mensaje': f'El monto solicitado excede 3 veces su ahorro actual (${info_socio["saldo_ahorro"]:,.2f})'
        }
    
    return {
        'aprobado': True,
        'mensaje': 'Capacidad de pago adecuada',
        'cuota_nueva': cuota_nueva,
        'cuota_total': cuota_total,
        'saldo_ahorro': info_socio['saldo_ahorro']
    }

def obtener_tasa_interes_grupo(id_grupo):
    """Obtener tasa de interés del grupo"""
    query = "SELECT interes FROM reglas_del_grupo WHERE id_grupo = %s"
    resultado = ejecutar_consulta(query, (id_grupo,))
    return resultado[0]['interes'] / 100 if resultado else 0.05  # 5% por defecto

def calcular_interes_mora(saldo_mora, dias_mora, tasa_mora_diaria=0.001):
    """
    Calcular interés por mora (tasa diaria por defecto: 0.1% diario)
    """
    return saldo_mora * tasa_mora_diaria * dias_mora

def simular_refinanciamiento(id_prestamo, nuevo_plazo):
    """
    Simular refinanciamiento de un préstamo
    """
    # Obtener información del préstamo actual
    query = """
        SELECT 
            monto_solicitado,
            (monto_solicitado - COALESCE(SUM(capital_pagado), 0)) as saldo_actual,
            interes
        FROM prestamo p
        LEFT JOIN `detalle de pagos` dp ON p.id_prestamo = dp.id_prestamo
        WHERE p.id_prestamo = %s
        GROUP BY p.id_prestamo
    """
    
    resultado = ejecutar_consulta(query, (id_prestamo,))
    
    if not resultado:
        return None
    
    prestamo_actual = resultado[0]
    saldo_actual = prestamo_actual['saldo_actual']
    tasa_interes = prestamo_actual['interes'] / 100
    
    # Calcular nuevas cuotas
    return calcular_cuotas_prestamo(saldo_actual, tasa_interes, nuevo_plazo)