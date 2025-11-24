# db.py
import streamlit as st
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager


def get_db_config():
    """
    Lee la configuración desde st.secrets["mysql"].
    Asegúrate de tener la sección [mysql] en los secrets.
    """
    cfg = st.secrets["mysql"]
    base_cfg = {
        "host": cfg["host"],
        "user": cfg["user"],
        "password": cfg["password"],
        "database": cfg["database"],
        "port": int(cfg.get("port", 3306)),
    }

    # Si agregas ssl_ca en secrets, se usa automáticamente
    if "ssl_ca" in cfg:
        base_cfg["ssl_ca"] = cfg["ssl_ca"]

    return base_cfg


def get_connection():
    """
    Mantiene una conexión por sesión de usuario.
    En Streamlit Cloud cada usuario tiene su propio session_state.
    """
    if "db_conn" not in st.session_state or st.session_state["db_conn"] is None:
        cfg = get_db_config()
        st.session_state["db_conn"] = mysql.connector.connect(
            **cfg,
            autocommit=True,
        )
    return st.session_state["db_conn"]


@contextmanager
def get_cursor(dictionary=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
    finally:
        cursor.close()


def fetch_all(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchall()


def fetch_one(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchone()


def execute(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params or ())
        return cur.lastrowid
