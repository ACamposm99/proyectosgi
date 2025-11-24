# auth.py
import streamlit as st
import bcrypt
from db import fetch_one


def init_session():
    if "auth" not in st.session_state:
        st.session_state["auth"] = {
            "logged_in": False,
            "user_id": None,
            "username": None,
            "rol": None,
            "id_socio": None,
            "id_promotor": None,
        }


def authenticate(username, password):
    row = fetch_one(
        """
        SELECT ID_Usuario, Username, PasswordHash, Rol_Sistema, ID_Socio, ID_Promotor
        FROM usuarios
        WHERE Username=%s AND Activo=1
        """,
        (username,),
    )
    if not row:
        return None

    stored_hash = row["PasswordHash"].encode("utf-8")
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return row

    return None


def login_form():
    init_session()
    st.subheader("Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        user = authenticate(username, password)
        if user:
            st.session_state["auth"] = {
                "logged_in": True,
                "user_id": user["ID_Usuario"],
                "username": user["Username"],
                "rol": user["Rol_Sistema"],
                "id_socio": user["ID_Socio"],
                "id_promotor": user["ID_Promotor"],
            }
            st.success(f"Bienvenido, {user['Username']}")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


def require_login():
    init_session()
    if not st.session_state["auth"]["logged_in"]:
        login_form()
        st.stop()


def require_role(allowed_roles):
    require_login()
    rol = st.session_state["auth"]["rol"]
    if rol not in allowed_roles:
        st.error("No tienes permiso para acceder a esta sección.")
        st.stop()


def logout_button():
    if st.sidebar.button("Cerrar sesión"):
        st.session_state["auth"] = {
            "logged_in": False,
            "user_id": None,
            "username": None,
            "rol": None,
            "id_socio": None,
            "id_promotor": None,
        }
        st.rerun()


def hash_password(plain: str) -> str:
    """
    Útil si quieres crear hashes desde la propia app.
    No lo uses en producción expuesto al público.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")
