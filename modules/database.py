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
                # Insertar datos básicos con IDs explícitos
                datos_iniciales = [
                    # Distritos
                    "INSERT INTO distrito (id_distrito, nombre_distrito, municipio) VALUES (1, 'Distrito Central', 'Tegucigalpa')",
                    "INSERT INTO distrito (id_distrito, nombre_distrito, municipio) VALUES (2, 'Distrito Norte', 'San Pedro Sula')",
                    "INSERT INTO distrito (id_distrito, nombre_distrito, municipio) VALUES (3, 'Distrito Sur', 'Choluteca')",
                    
                    # Frecuencias
                    "INSERT INTO frecuencia (tipo_frecuencia) VALUES ('Semanal')",
                    "INSERT INTO frecuencia (tipo_frecuencia) VALUES ('Quincenal')",
                    "INSERT INTO frecuencia (tipo_frecuencia) VALUES ('Mensual')",
                    
                    # Roles de directiva
                    "INSERT INTO roles (id_rol, tipo_rol, funcion) VALUES (1, 'Presidente/a', 'Dirige las reuniones y representa al grupo')",
                    "INSERT INTO roles (id_rol, tipo_rol, funcion) VALUES (2, 'Tesorero/a', 'Administra el dinero y lleva registros')",
                    "INSERT INTO roles (id_rol, tipo_rol, funcion) VALUES (3, 'Secretario/a', 'Lleva actas y control de documentos')",
                    
                    # Estados de directiva
                    "INSERT INTO estado_directiva (id_estadodirectiva, clave, estado) VALUES (1, 'ACTIVO', 'Activo')",
                    "INSERT INTO estado_directiva (id_estadodirectiva, clave, estado) VALUES (2, 'INACTIVO', 'Inactivo')",
                    
                    # Estados de préstamo
                    "INSERT INTO estado_del_prestamo (id_estadoprestamo, estados) VALUES (1, 'Pendiente')",
                    "INSERT INTO estado_del_prestamo (id_estadoprestamo, estados) VALUES (2, 'Aprobado')",
                    "INSERT INTO estado_del_prestamo (id_estadoprestamo, estados) VALUES (3, 'Rechazado')",
                    "INSERT INTO estado_del_prestamo (id_estadoprestamo, estados) VALUES (4, 'Pagado')",
                    "INSERT INTO estado_del_prestamo (id_estadoprestamo, estados) VALUES (5, 'Mora')",
                    
                    # Tipos de movimiento de caja
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (1, 'Ahorro', 'Aportes de ahorro de socios')",
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (2, 'Préstamo', 'Desembolso de préstamo')",
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (3, 'Pago Préstamo', 'Pago de cuota de préstamo')",
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (4, 'Multa', 'Multa por inasistencia o mora')",
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (5, 'Otros Ingresos', 'Ingresos por actividades especiales')",
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (6, 'Gastos Operativos', 'Gastos administrativos del grupo')",
                    "INSERT INTO tipo_de_movimiento_de_caja (id_tipomovimiento, nombre_movimiento, descripcion) VALUES (7, 'Devolución', 'Devolución de fondos')",
                    
                    # Promotor por defecto
                    "INSERT INTO promotores (id_promotor, nombre, apellido, tele, direccion, id_distrito) VALUES (1, 'Promotor', 'Demo', 99999999, 'Dirección demo', 1)"
                ]
                
                for comando in datos_iniciales:
                    try:
                        cursor.execute(comando)
                    except Error as e:
                        # Si ya existe el registro, ignorar el error
                        if "Duplicate entry" not in str(e):
                            st.warning(f"Advertencia al insertar datos: {e}")
                
                conn.commit()
                st.success("✅ Base de datos inicializada con datos básicos")
            
            cursor.close()
            conn.close()
            
    except Error as e:
        st.error(f"❌ Error inicializando BD: {e}")