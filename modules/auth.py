import streamlit as st
import hashlib
from modules.database import conectar_bd, ejecutar_consulta

def autenticar_usuario(username, password, rol):
    """Autenticar usuario en el sistema"""
    
    # Hash de la contraseña
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Verificar credenciales en la base de datos
        query = """
            SELECT u.id_usuario, u.username, u.rol_sistema, 
                   COALESCE(s.id_socio, p.id_promotor) as id_relacionado,
                   COALESCE(g.id_grupo, NULL) as id_grupo,
                   COALESCE(g.nombre_grupo, '') as nombre_grupo
            FROM usuarios u
            LEFT JOIN socios s ON u.id_socio = s.id_socio
            LEFT JOIN promotores p ON u.id_Promotor = p.id_promotor
            LEFT JOIN grupos g ON s.id_grupo = g.id_grupo
            WHERE u.username = %s AND u.passwordhash = %s AND u.rol_sistema = %s AND u.activo = 1
        """
        
        resultado = ejecutar_consulta(query, (username, password_hash, rol))
        
        if resultado:
            usuario = resultado[0]
            st.session_state.autenticado = True
            st.session_state.usuario_id = usuario[0]
            st.session_state.usuario = usuario[1]
            st.session_state.rol = usuario[2]
            st.session_state.id_relacionado = usuario[3]
            st.session_state.id_grupo = usuario[4]
            st.session_state.nombre_grupo = usuario[5]
            return True
        
        # Usuario admin por defecto (solo para desarrollo)
        if username == st.secrets["admin"]["username"] and password == st.secrets["admin"]["password"] and rol == "ADMIN":
            st.session_state.autenticado = True
            st.session_state.usuario = "admin"
            st.session_state.rol = "ADMIN"
            return True
            
        return False
        
    except Exception as e:
        st.error(f"Error en autenticación: {e}")
        return False

def mostrar_login():
    """Interfaz de login"""
    
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: #f9f9f9;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.title("🏦 Sistema GAPC")
    st.markdown("**Grupos de Ahorro y Préstamo Comunitario**")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
        rol = st.selectbox("🎯 Rol", ["DIRECTIVA", "PROMOTORA", "ADMIN"])
        
        submitted = st.form_submit_button("🚀 Iniciar Sesión")
        
        if submitted:
            if not username or not password:
                st.error("❌ Por favor complete todos los campos")
            elif autenticar_usuario(username, password, rol):
                st.success("✅ ¡Autenticación exitosa!")
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas o usuario inactivo")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Información de demo (solo en desarrollo)
    with st.expander("ℹ️ Información de Demo"):
        st.write("**Usuario Admin:** admin / admin123")
        st.write("**Roles disponibles:** DIRECTIVA, PROMOTORA, ADMIN")

def cerrar_sesion():
    """Cerrar sesión del usuario"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()