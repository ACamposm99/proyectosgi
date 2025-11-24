import mysql.connector
import streamlit as st
from mysql.connector import Error

def conectar_bd():
    """Establecer conexión con la base de datos"""
    try:
        conn = mysql.connector.connect(
            host=st.secrets["db"]["host"],
            user=st.secrets["db"]["user"],
            password=st.secrets["db"]["password"],
            database=st.secrets["db"]["database"],
            charset='utf8'
        )
        return conn
    except Error as e:
        st.error(f"❌ Error de conexión a la base de datos: {e}")
        return None

def ejecutar_consulta(query, params=None):
    """Ejecutar consulta SELECT y retornar resultados"""
    try:
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            resultado = cursor.fetchall()
            cursor.close()
            conn.close()
            return resultado
    except Error as e:
        st.error(f"❌ Error en consulta: {e}")
    return None

def ejecutar_comando(query, params=None):
    """Ejecutar comando INSERT, UPDATE, DELETE"""
    try:
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            id_generado = cursor.lastrowid
            cursor.close()
            conn.close()
            return id_generado
    except Error as e:
        st.error(f"❌ Error ejecutando comando: {e}")
    return None

def inicializar_bd():
    """Inicializar tablas necesarias si no existen"""
    try:
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor()
            
            # Verificar si existen datos básicos
            cursor.execute("SELECT COUNT(*) as count FROM distrito")
            resultado = cursor.fetchone()
            
            if resultado[0] == 0:
                # Insertar datos básicos
                datos_iniciales = [
                    # Distritos
                    "INSERT INTO distrito (nombre_distrito, municipio) VALUES ('Distrito Central', 'Tegucigalpa')",
                    "INSERT INTO distrito (nombre_distrito, municipio) VALUES ('Distrito Norte', 'San Pedro Sula')",
                    "INSERT INTO distrito (nombre_distrito, municipio) VALUES ('Distrito Sur', 'Choluteca')",
                    
                    # Frecuencias
                    "INSERT INTO frecuencia (tipo_frecuencia) VALUES ('Semanal')",
                    "INSERT INTO frecuencia (tipo_frecuencia) VALUES ('Quincenal')",
                    "INSERT INTO frecuencia (tipo_frecuencia) VALUES ('Mensual')",
                    
                    # Roles de directiva
                    "INSERT INTO roles (tipo_rol, funcion) VALUES ('Presidente/a', 'Dirige las reuniones y representa al grupo')",
                    "INSERT INTO roles (tipo_rol, funcion) VALUES ('Tesorero/a', 'Administra el dinero y lleva registros')",
                    "INSERT INTO roles (tipo_rol, funcion) VALUES ('Secretario/a', 'Lleva actas y control de documentos')",
                    
                    # Estados de directiva
                    "INSERT INTO estado_directiva (clave, estado) VALUES ('ACTIVO', 'Activo')",
                    "INSERT INTO estado_directiva (clave, estado) VALUES ('INACTIVO', 'Inactivo')",
                    
                    # Estados de préstamo
                    "INSERT INTO estado_del_prestamo (estados) VALUES ('Pendiente')",
                    "INSERT INTO estado_del_prestamo (estados) VALUES ('Aprobado')",
                    "INSERT INTO estado_del_prestamo (estados) VALUES ('Rechazado')",
                    "INSERT INTO estado_del_prestamo (estados) VALUES ('Pagado')",
                    "INSERT INTO estado_del_prestamo (estados) VALUES ('Mora')",
                    
                    # Tipos de movimiento de caja
                    "INSERT INTO tipo_de_movimiento_de_caja (nombre_movimiento, descripcion) VALUES ('Ahorro', 'Aportes de ahorro de socios')",
                    "INSERT INTO tipo_de_movimiento_de_caja (nombre_movimiento, descripcion) VALUES ('Préstamo', 'Desembolso de préstamo')",
                    "INSERT INTO tipo_de_movimiento_de_caja (nombre_movimiento, descripcion) VALUES ('Pago Préstamo', 'Pago de cuota de préstamo')",
                    "INSERT INTO tipo_de_movimiento_de_caja (nombre_movimiento, descripcion) VALUES ('Multa', 'Multa por inasistencia o mora')",
                    "INSERT INTO tipo_de_movimiento_de_caja (nombre_movimiento, descripcion) VALUES ('Otros Ingresos', 'Ingresos por actividades especiales')"
                ]
                
                for comando in datos_iniciales:
                    try:
                        cursor.execute(comando)
                    except Error as e:
                        st.warning(f"Advertencia al insertar datos: {e}")
                
                conn.commit()
                st.success("✅ Base de datos inicializada con datos básicos")
            
            cursor.close()
            conn.close()
            
    except Error as e:
        st.error(f"❌ Error inicializando BD: {e}")