# app.py
import streamlit as st
import pandas as pd

from db import fetch_all, fetch_one, execute
from auth import require_login, require_role, logout_button

st.set_page_config(
    page_title="GAPC - Gestión de Grupos de Ahorro",
    layout="wide",
)


# ---------- Helpers ----------
def get_current_user():
    return st.session_state["auth"]


def select_grupo_for_user():
    """Devuelve ID_Grupo seleccionado, según rol (Directiva/Promotora/Admin)."""
    user = get_current_user()
    rol = user["rol"]

    if rol == "DIRECTIVA":
        grupos = fetch_all(
            """
            SELECT DISTINCT g.ID_Grupo, g.Nombre_grupo
            FROM grupos g
            JOIN directiva_grupo dg ON dg.ID_Grupo = g.ID_Grupo
            WHERE dg.ID_Socio = %s
            """,
            (user["id_socio"],),
        )
    elif rol == "PROMOTORA":
        grupos = fetch_all(
            """
            SELECT g.ID_Grupo, g.Nombre_grupo
            FROM grupos g
            WHERE g.ID_Promotor = %s
            """,
            (user["id_promotor"],),
        )
    else:  # ADMIN
        grupos = fetch_all("SELECT ID_Grupo, Nombre_grupo FROM grupos")

    if not grupos:
        st.warning("No hay grupos asociados a tu usuario.")
        return None

    opciones = {f"{g['Nombre_grupo']} (ID {g['ID_Grupo']})": g["ID_Grupo"] for g in grupos}
    etiqueta = st.sidebar.selectbox("Selecciona un grupo", list(opciones.keys()))
    return opciones[etiqueta]


# ---------- Páginas ----------
def pagina_dashboard():
    require_login()
    st.title("Panel principal")

    user = get_current_user()
    st.write(f"Usuario: **{user['username']}** | Rol: **{user['rol']}**")

    total_grupos = fetch_one("SELECT COUNT(*) AS c FROM grupos")["c"]
    total_socios = fetch_one("SELECT COUNT(*) AS c FROM socios")["c"]
    total_prestamos = fetch_one("SELECT COUNT(*) AS c FROM prestamo")["c"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Grupos activos", total_grupos)
    col2.metric("Socios registrados", total_socios)
    col3.metric("Préstamos registrados", total_prestamos)


def pagina_grupos_y_reglas():
    require_role(["ADMIN", "PROMOTORA"])
    st.title("1. Conformación del grupo y reglas básicas")

    col1, col2 = st.columns(2)

    # ---- Crear grupo ----
    with col1:
        st.subheader("Registrar nuevo grupo")
        distritos = fetch_all("SELECT ID_Distrito, Nombre_distrito FROM distrito")
        promotores = fetch_all("SELECT ID_Promotor, Nombre, Apellido FROM promotores")
        frecuencias = fetch_all("SELECT ID_Frecuencia, Tipo_frecuencia FROM frecuencia")

        nombre_grupo = st.text_input("Nombre del grupo")
        distrito_sel = (
            st.selectbox("Distrito", distritos, format_func=lambda d: d["Nombre_distrito"])
            if distritos
            else None
        )
        promotor_sel = (
            st.selectbox(
                "Promotor/a",
                promotores,
                format_func=lambda p: f"{p['Nombre']} {p['Apellido']}",
            )
            if promotores
            else None
        )
        frecuencia_sel = (
            st.selectbox(
                "Frecuencia de reunión",
                frecuencias,
                format_func=lambda f: f["Tipo_frecuencia"],
            )
            if frecuencias
            else None
        )

        fecha_creacion = st.date_input("Fecha de inicio del ciclo")
        hora_reunion = st.time_input("Hora de reunión")
        lugar_reunion = st.text_input("Lugar de reunión")
        dia_reunion = st.text_input("Día de reunión (texto)", value="Lunes")
        meta_social = st.text_input("Meta social (opcional)")
        otras_reglas = st.text_area("Otras reglas (opcional)")

        if st.button("Crear grupo"):
            if not (nombre_grupo and distrito_sel and promotor_sel and frecuencia_sel):
                st.error("Complete todos los campos obligatorios.")
            else:
                execute(
                    """
                    INSERT INTO grupos
                    (Nombre_grupo, ID_Distrito, Fecha_creacion, ID_Promotor,
                     ID_Frecuencia, Hora_reunion, Lugar_reunion, Dia_reunion,
                     Meta_social, Otras_reglas)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        nombre_grupo,
                        distrito_sel["ID_Distrito"],
                        fecha_creacion,
                        promotor_sel["ID_Promotor"],
                        frecuencia_sel["ID_Frecuencia"],
                        hora_reunion,
                        lugar_reunion,
                        dia_reunion,
                        meta_social,
                        otras_reglas,
                    ),
                )
                st.success("Grupo creado correctamente.")
                st.rerun()

    # ---- Reglas de ciclo ----
    with col2:
        st.subheader("Configurar reglas del grupo (ciclo)")
        grupos = fetch_all("SELECT ID_Grupo, Nombre_grupo FROM grupos")
        if not grupos:
            st.info("Primero crea al menos un grupo.")
            return

        g_sel = st.selectbox("Grupo", grupos, format_func=lambda g: g["Nombre_grupo"])

        cantidad_multa = st.number_input(
            "Monto de multa por falta", min_value=0.0, value=1.0, step=0.5
        )
        interes_por_10 = st.number_input(
            "Interés por 10 (según programa)", min_value=0.0, value=2.0, step=0.5
        )
        monto_max_prestamo = st.number_input(
            "Monto máximo de préstamo", min_value=0.0, value=100.0, step=10.0
        )
        un_prestamo_vez = st.checkbox(
            "Solo un préstamo a la vez por socio", value=True
        )
        fecha_inicio = st.date_input("Fecha inicio ciclo")
        fecha_fin = st.date_input("Fecha fin ciclo")
        duracion_meses = st.number_input(
            "Duración del ciclo (meses)", min_value=1, value=6
        )

        if st.button("Guardar reglas del ciclo"):
            execute(
                """
                INSERT INTO reglas_grupo
                (ID_Grupo, Cantidad_multa_falta, Interes_por_10, MontoMaxPrestamo,
                 UnPrestamoALaVez, Fecha_inicio_ciclo, Fecha_fin_ciclo, Duracion_ciclo_meses)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    g_sel["ID_Grupo"],
                    cantidad_multa,
                    interes_por_10,
                    monto_max_prestamo,
                    1 if un_prestamo_vez else 0,
                    fecha_inicio,
                    fecha_fin,
                    duracion_meses,
                ),
            )
            st.success("Reglas del ciclo registradas.")


def pagina_socios_y_asistencia():
    require_role(["DIRECTIVA", "ADMIN"])
    st.title("2. Afiliación de miembros y asistencia")

    grupo_id = select_grupo_for_user()
    if not grupo_id:
        return

    col1, col2 = st.columns(2)

    # ---- Registro de socio ----
    with col1:
        st.subheader("Registrar nuevo miembro")
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        telefono = st.text_input("Teléfono")
        direccion = st.text_input("Dirección")

        distrito = fetch_one(
            """
            SELECT d.ID_Distrito
            FROM grupos g
            JOIN distrito d ON d.ID_Distrito = g.ID_Distrito
            WHERE g.ID_Grupo = %s
            """,
            (grupo_id,),
        )

        if st.button("Guardar socio"):
            if not (nombre and apellido):
                st.error("Nombre y apellido son obligatorios.")
            else:
                execute(
                    """
                    INSERT INTO socios
                    (Nombre, Apellido, Telefono, Direccion, ID_Grupo, ID_Distrito)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        nombre,
                        apellido,
                        telefono,
                        direccion,
                        grupo_id,
                        distrito["ID_Distrito"],
                    ),
                )
                st.success("Socio registrado.")
                st.rerun()

    # ---- Asistencia ----
    with col2:
        st.subheader("Registrar asistencia a reunión")
        fecha_sesion = st.date_input("Fecha de sesión")

        if st.button("Crear/abrir sesión de hoy"):
            sesion = fetch_one(
                "SELECT ID_Sesion FROM sesion WHERE ID_Grupo=%s AND Fecha_sesion=%s",
                (grupo_id, fecha_sesion),
            )
            if not sesion:
                sesion_id = execute(
                    "INSERT INTO sesion (ID_Grupo, Fecha_sesion, Total_presentes) VALUES (%s,%s,%s)",
                    (grupo_id, fecha_sesion, 0),
                )
            else:
                sesion_id = sesion["ID_Sesion"]
            st.success(f"Sesión abierta ID {sesion_id}")
            st.rerun()

        sesiones = fetch_all(
            "SELECT ID_Sesion, Fecha_sesion FROM sesion WHERE ID_Grupo=%s ORDER BY Fecha_sesion DESC",
            (grupo_id,),
        )
        if sesiones:
            sesion_sel = st.selectbox(
                "Selecciona sesión",
                sesiones,
                format_func=lambda s: f"{s['ID_Sesion']} - {s['Fecha_sesion']}",
            )
            socios = fetch_all(
                "SELECT ID_Socio, Nombre, Apellido FROM socios WHERE ID_Grupo=%s",
                (grupo_id,),
            )

            st.write("Marca asistencia:")
            presentes_ids = []
            for socio in socios:
                presente = st.checkbox(
                    f"{socio['Nombre']} {socio['Apellido']}",
                    key=f"pres_{sesion_sel['ID_Sesion']}_{socio['ID_Socio']}",
                    value=True,
                )
                if presente:
                    presentes_ids.append(socio["ID_Socio"])

            if st.button("Guardar asistencia"):
                execute("DELETE FROM asistencia WHERE ID_Sesion=%s", (sesion_sel["ID_Sesion"],))

                for socio in socios:
                    presente = socio["ID_Socio"] in presentes_ids
                    execute(
                        "INSERT INTO asistencia (ID_Sesion, ID_Socio, Presencial) VALUES (%s,%s,%s)",
                        (
                            sesion_sel["ID_Sesion"],
                            socio["ID_Socio"],
                            1 if presente else 0,
                        ),
                    )

                    if not presente:
                        regla = fetch_one(
                            """
                            SELECT Cantidad_multa_falta
                            FROM reglas_grupo
                            WHERE ID_Grupo=%s
                            ORDER BY Fecha_inicio_ciclo DESC
                            LIMIT 1
                            """,
                            (grupo_id,),
                        )
                        if regla:
                            execute(
                                """
                                INSERT INTO multa
                                (ID_Sesion, ID_Socio, Monto_a_pagar, Monto_pagado, Fecha_vencimiento)
                                VALUES (%s,%s,%s,0,%s)
                                """,
                                (
                                    sesion_sel["ID_Sesion"],
                                    socio["ID_Socio"],
                                    regla["Cantidad_multa_falta"],
                                    sesion_sel["Fecha_sesion"],
                                ),
                            )

                execute(
                    "UPDATE sesion SET Total_presentes=%s WHERE ID_Sesion=%s",
                    (len(presentes_ids), sesion_sel["ID_Sesion"]),
                )
                st.success("Asistencia y multas registradas.")
                st.rerun()


def pagina_ahorros():
    require_role(["DIRECTIVA", "ADMIN"])
    st.title("3. Reuniones y aportes de ahorro")

    grupo_id = select_grupo_for_user()
    if not grupo_id:
        return

    sesiones = fetch_all(
        "SELECT ID_Sesion, Fecha_sesion FROM sesion WHERE ID_Grupo=%s ORDER BY Fecha_sesion DESC",
        (grupo_id,),
    )
    if not sesiones:
        st.info("No hay sesiones aún. Registra una desde la página de asistencia.")
        return

    sesion_sel = st.selectbox(
        "Selecciona sesión",
        sesiones,
        format_func=lambda s: f"{s['ID_Sesion']} - {s['Fecha_sesion']}",
    )

    ahorro = fetch_one("SELECT * FROM ahorro WHERE ID_Sesion=%s", (sesion_sel["ID_Sesion"],))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resumen de ahorro de la sesión")
        if ahorro:
            st.write(f"Saldo apertura: {ahorro['Saldo_apertura']}")
            st.write(f"Total ingresos: {ahorro['Total_ingresos']}")
            st.write(f"Saldo cierre: {ahorro['Saldo_cierre']}")
        else:
            saldo_apertura = st.number_input(
                "Saldo apertura", min_value=0.0, value=0.0, step=1.0
            )
            if st.button("Crear resumen de ahorro"):
                execute(
                    """
                    INSERT INTO ahorro
                    (ID_Sesion, Saldo_apertura, Total_ingresos, Saldo_cierre)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (sesion_sel["ID_Sesion"], saldo_apertura, 0.0, saldo_apertura),
                )
                st.success("Resumen de ahorro creado.")
                st.rerun()

    with col2:
        st.subheader("Registrar aportes por socio")
        ahorro = fetch_one("SELECT * FROM ahorro WHERE ID_Sesion=%s", (sesion_sel["ID_Sesion"],))
        if not ahorro:
            st.info("Primero crea el resumen de ahorro de la sesión.")
            return

        socios = fetch_all(
            "SELECT ID_Socio, Nombre, Apellido FROM socios WHERE ID_Grupo=%s",
            (grupo_id,),
        )

        total_ingresos = 0.0
        for socio in socios:
            valor = st.number_input(
                f"Aporte - {socio['Nombre']} {socio['Apellido']}",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"ah_{sesion_sel['ID_Sesion']}_{socio['ID_Socio']}",
            )
            if valor > 0:
                total_ingresos += valor

        if st.button("Guardar aportes"):
            execute(
                """
                DELETE ad FROM ahorro_detalle ad
                JOIN ahorro a ON a.ID_Ahorro = ad.ID_Ahorro
                WHERE a.ID_Sesion=%s
                """,
                (sesion_sel["ID_Sesion"],),
            )

            for socio in socios:
                aporte = st.session_state.get(
                    f"ah_{sesion_sel['ID_Sesion']}_{socio['ID_Socio']}", 0.0
                )
                if aporte <= 0:
                    continue

                saldo_prev = fetch_one(
                    """
                    SELECT COALESCE(SUM(Saldo_final),0) AS saldo
                    FROM ahorro_detalle ad
                    JOIN ahorro a ON a.ID_Ahorro = ad.ID_Ahorro
                    WHERE a.ID_Sesion < %s AND ad.ID_Socio=%s
                    """,
                    (sesion_sel["ID_Sesion"], socio["ID_Socio"]),
                )["saldo"]

                saldo_final = saldo_prev + aporte
                execute(
                    """
                    INSERT INTO ahorro_detalle
                    (ID_Socio, ID_Ahorro, Saldo_ahorro, Saldo_ingresado, Otras_actividades, Saldo_final)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        socio["ID_Socio"],
                        ahorro["ID_Ahorro"],
                        saldo_prev,
                        aporte,
                        0.0,
                        saldo_final,
                    ),
                )

            execute(
                """
                UPDATE ahorro
                SET Total_ingresos = Total_ingresos + %s,
                    Saldo_cierre   = Saldo_cierre + %s
                WHERE ID_Ahorro=%s
                """,
                (total_ingresos, total_ingresos, ahorro["ID_Ahorro"]),
            )
            st.success("Aportes guardados y saldos actualizados.")
            st.rerun()


def pagina_prestamos():
    require_role(["DIRECTIVA", "ADMIN"])
    st.title("4. Gestión de préstamos internos")

    grupo_id = select_grupo_for_user()
    if not grupo_id:
        return

    socios = fetch_all(
        "SELECT ID_Socio, Nombre, Apellido FROM socios WHERE ID_Grupo=%s",
        (grupo_id,),
    )
    if not socios:
        st.info("No hay socios en el grupo.")
        return

    socio_sel = st.selectbox(
        "Socio/a", socios, format_func=lambda s: f"{s['Nombre']} {s['Apellido']}"
    )

    col1, col2 = st.columns(2)

    # ---- Nuevo préstamo ----
    with col1:
        st.subheader("Nuevo préstamo")
        monto = st.number_input("Monto a prestar", min_value=0.0, value=50.0, step=5.0)
        fecha_desembolso = st.date_input("Fecha de desembolso")
        fecha_venc = st.date_input("Fecha de vencimiento")
        tasa_interes = st.number_input(
            "Tasa de interés (% total del ciclo)", min_value=0.0, value=10.0, step=1.0
        )
        cuotas = st.number_input("Número de cuotas", min_value=1, value=4)

        estado = fetch_one(
            "SELECT ID_Estado_Prestamo FROM estado_prestamo ORDER BY ID_Estado_Prestamo LIMIT 1"
        )

        if st.button("Registrar préstamo"):
            regla = fetch_one(
                """
                SELECT UnPrestamoALaVez, MontoMaxPrestamo
                FROM reglas_grupo
                WHERE ID_Grupo=%s
                ORDER BY Fecha_inicio_ciclo DESC
                LIMIT 1
                """,
                (grupo_id,),
            )

            if regla and regla["UnPrestamoALaVez"]:
                prest_activo = fetch_one(
                    """
                    SELECT COUNT(*) AS c
                    FROM prestamo
                    WHERE ID_Socio=%s
                    """,
                    (socio_sel["ID_Socio"],),
                )
                if prest_activo and prest_activo["c"] > 0:
                    st.error("El socio ya tiene un préstamo activo.")
                    st.stop()

            if regla and monto > regla["MontoMaxPrestamo"]:
                st.error(
                    f"El monto excede el máximo permitido ({regla['MontoMaxPrestamo']})."
                )
            else:
                sesion = fetch_one(
                    """
                    SELECT ID_Sesion FROM sesion
                    WHERE ID_Grupo=%s
                    ORDER BY Fecha_sesion DESC LIMIT 1
                    """,
                    (grupo_id,),
                )
                if not sesion:
                    st.error(
                        "No hay sesiones registradas; crea una sesión antes de otorgar préstamos."
                    )
                else:
                    prest_id = execute(
                        """
                        INSERT INTO prestamo
                        (ID_Socio, Fecha_Desembolso, Monto_Desembolso,
                         Fecha_Vencimiento, ID_Estado_Prestamo, ID_Sesion)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            socio_sel["ID_Socio"],
                            fecha_desembolso,
                            monto,
                            fecha_venc,
                            estado["ID_Estado_Prestamo"],
                            sesion["ID_Sesion"],
                        ),
                    )

                    capital_por_cuota = monto / cuotas
                    interes_total = monto * (tasa_interes / 100.0)
                    interes_por_cuota = interes_total / cuotas

                    for _ in range(cuotas):
                        execute(
                            """
                            INSERT INTO detalles_pagos
                            (ID_Socio, Fecha_Programada, Capital_Pagado,
                             Interes_Pagado, ID_Prestamo, Interes, Total_Pagado)
                            VALUES (%s,%s,0,0,%s,%s,0)
                            """,
                            (
                                socio_sel["ID_Socio"],
                                fecha_desembolso,
                                prest_id,
                                interes_por_cuota,
                            ),
                        )

                    st.success(
                        f"Préstamo registrado (ID {prest_id}) con plan de {cuotas} cuotas."
                    )
                    st.rerun()

    # ---- Registrar pagos ----
    with col2:
        st.subheader("Registrar pago de cuota")

        prestamos = fetch_all(
            """
            SELECT p.ID_Prestamo, p.Monto_Desembolso, p.Fecha_Desembolso
            FROM prestamo p
            WHERE p.ID_Socio=%s
            ORDER BY p.ID_Prestamo DESC
            """,
            (socio_sel["ID_Socio"],),
        )
        if not prestamos:
            st.info("Este socio no tiene préstamos.")
        else:
            prest_sel = st.selectbox(
                "Préstamo",
                prestamos,
                format_func=lambda p: f"ID {p['ID_Prestamo']} - Monto {p['Monto_Desembolso']}",
            )

            cuotas_pend = fetch_all(
                """
                SELECT ID_Pago, Fecha_Programada, Capital_Pagado, Interes_Pagado, Total_Pagado, Interes
                FROM detalles_pagos
                WHERE ID_Prestamo=%s
                ORDER BY ID_Pago
                """,
                (prest_sel["ID_Prestamo"],),
            )

            for cuota in cuotas_pend:
                st.write(
                    f"Cuota ID {cuota['ID_Pago']} - Programada: {cuota['Fecha_Programada']}"
                )
                capital_pag = st.number_input(
                    f"Capital pagado (ID {cuota['ID_Pago']})",
                    min_value=0.0,
                    value=cuota["Capital_Pagado"] or 0.0,
                    step=1.0,
                    key=f"cap_{cuota['ID_Pago']}",
                )
                interes_pag = st.number_input(
                    f"Interés pagado (ID {cuota['ID_Pago']})",
                    min_value=0.0,
                    value=cuota["Interes_Pagado"] or 0.0,
                    step=1.0,
                    key=f"int_{cuota['ID_Pago']}",
                )

            if st.button("Guardar pagos"):
                for cuota in cuotas_pend:
                    cap = st.session_state.get(f"cap_{cuota['ID_Pago']}", 0.0)
                    inte = st.session_state.get(f"int_{cuota['ID_Pago']}", 0.0)
                    total = cap + inte

                    execute(
                        """
                        UPDATE detalles_pagos
                        SET Capital_Pagado=%s,
                            Interes_Pagado=%s,
                            Fecha_Pago_Real=CURDATE(),
                            Total_Pagado=%s
                        WHERE ID_Pago=%s
                        """,
                        (cap, inte, total, cuota["ID_Pago"]),
                    )

                st.success("Pagos actualizados.")
                st.rerun()


def pagina_caja():
    require_role(["DIRECTIVA", "ADMIN"])
    st.title("4. Gestión de caja")

    grupo_id = select_grupo_for_user()
    if not grupo_id:
        return

    sesiones = fetch_all(
        "SELECT ID_Sesion, Fecha_sesion FROM sesion WHERE ID_Grupo=%s ORDER BY Fecha_sesion DESC",
        (grupo_id,),
    )
    if not sesiones:
        st.info("No hay sesiones registradas.")
        return

    sesion_sel = st.selectbox(
        "Selecciona sesión para caja",
        sesiones,
        format_func=lambda s: f"{s['ID_Sesion']} - {s['Fecha_sesion']}",
    )

    caja = fetch_one("SELECT * FROM caja WHERE ID_Sesion=%s", (sesion_sel["ID_Sesion"],))
    if not caja:
        saldo_apertura = st.number_input(
            "Saldo apertura caja", min_value=0.0, value=0.0, step=1.0
        )
        if st.button("Crear caja para sesión"):
            caja_id = execute(
                """
                INSERT INTO caja
                (ID_Sesion, Saldo_apertura, Total_ingresos, Total_egresos, Saldo_cierre)
                VALUES (%s,%s,0,0,%s)
                """,
                (sesion_sel["ID_Sesion"], saldo_apertura, saldo_apertura),
            )
            st.success(f"Caja creada (ID {caja_id}).")
            st.rerun()
        return

    st.subheader(f"Caja ID {caja['ID_Caja']}")
    st.write(f"Saldo apertura: {caja['Saldo_apertura']}")
    st.write(f"Ingresos: {caja['Total_ingresos']}")
    st.write(f"Egresos: {caja['Total_egresos']}")
    st.write(f"Saldo cierre: {caja['Saldo_cierre']}")

    st.markdown("---")
    st.subheader("Registrar movimiento de caja")

    tipos = fetch_all("SELECT ID_TipoDeMovimiento, Nombre_movimiento FROM tipo_movimiento")
    tipo_sel = (
        st.selectbox(
            "Tipo de movimiento",
            tipos,
            format_func=lambda t: t["Nombre_movimiento"],
        )
        if tipos
        else None
    )

    socios = fetch_all(
        "SELECT ID_Socio, Nombre, Apellido FROM socios WHERE ID_Grupo=%s",
        (grupo_id,),
    )
    socio_sel = st.selectbox(
        "Socio (opcional)",
        ["Ninguno"] + [f"{s['ID_Socio']} - {s['Nombre']} {s['Apellido']}" for s in socios],
    )
    socio_id = None
    if socio_sel != "Ninguno":
        socio_id = int(socio_sel.split(" - ")[0])

    monto = st.number_input("Monto", min_value=0.0, value=0.0, step=1.0)
    descripcion = st.text_input("Descripción")

    if st.button("Guardar movimiento"):
        if not (tipo_sel and monto > 0):
            st.error("Selecciona tipo y monto.")
        else:
            execute(
                """
                INSERT INTO movimiento_caja
                (ID_Caja, ID_TipoDeMovimiento, ID_Socio, Monto, Descripcion, HoraRegistro)
                VALUES (%s,%s,%s,%s,%s,NOW())
                """,
                (caja["ID_Caja"], tipo_sel["ID_TipoDeMovimiento"], socio_id, monto, descripcion),
            )

            if "egreso" in tipo_sel["Nombre_movimiento"].lower():
                execute(
                    """
                    UPDATE caja
                    SET Total_egresos = Total_egresos + %s,
                        Saldo_cierre   = Saldo_cierre - %s
                    WHERE ID_Caja=%s
                    """,
                    (monto, monto, caja["ID_Caja"]),
                )
            else:
                execute(
                    """
                    UPDATE caja
                    SET Total_ingresos = Total_ingresos + %s,
                        Saldo_cierre   = Saldo_cierre + %s
                    WHERE ID_Caja=%s
                    """,
                    (monto, monto, caja["ID_Caja"]),
                )

            st.success("Movimiento registrado.")
            st.rerun()

    st.markdown("### Movimientos de la sesión")
    movs = fetch_all(
        """
        SELECT mc.*, tm.Nombre_movimiento
        FROM movimiento_caja mc
        JOIN tipo_movimiento tm ON tm.ID_TipoDeMovimiento = mc.ID_TipoDeMovimiento
        WHERE mc.ID_Caja=%s
        ORDER BY mc.HoraRegistro
        """,
        (caja["ID_Caja"],),
    )

    if movs:
        df = pd.DataFrame(movs)
        st.dataframe(df)
    else:
        st.write("Sin movimientos.")


def pagina_cierre_ciclo():
    require_role(["DIRECTIVA", "ADMIN"])
    st.title("5. Cierre del ciclo")

    grupo_id = select_grupo_for_user()
    if not grupo_id:
        return

    pendientes = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM prestamo p
        JOIN sesion s ON s.ID_Sesion = p.ID_Sesion
        WHERE s.ID_Grupo=%s
        """,
        (grupo_id,),
    )["c"]

    st.write(
        f"Préstamos asociados al grupo (no distinguimos estado aún): {pendientes}."
    )

    if st.button("Calcular y registrar cierre"):
        saldos = fetch_all(
            """
            SELECT ad.ID_Socio,
                   SUM(ad.Saldo_final) AS SaldoFinalAhorro
            FROM ahorro_detalle ad
            JOIN ahorro a ON a.ID_Ahorro = ad.ID_Ahorro
            JOIN sesion s ON s.ID_Sesion = a.ID_Sesion
            WHERE s.ID_Grupo=%s
            GROUP BY ad.ID_Socio
            """,
            (grupo_id,),
        )

        if not saldos:
            st.error("No hay información de ahorro para este grupo.")
            return

        total_ahorro = sum(s["SaldoFinalAhorro"] for s in saldos)

        total_multas = fetch_one(
            """
            SELECT COALESCE(SUM(Monto_pagado),0) AS m
            FROM multa m
            JOIN sesion s ON s.ID_Sesion = m.ID_Sesion
            WHERE s.ID_Grupo=%s
            """,
            (grupo_id,),
        )["m"]

        total_intereses = fetch_one(
            """
            SELECT COALESCE(SUM(Interes_Pagado),0) AS i
            FROM detalles_pagos dp
            JOIN prestamo p ON p.ID_Prestamo = dp.ID_Prestamo
            JOIN sesion s ON s.ID_Sesion = p.ID_Sesion
            WHERE s.ID_Grupo=%s
            """,
            (grupo_id,),
        )["i"]

        otros_ingresos = 0.0
        utilidades = total_multas + total_intereses + otros_ingresos

        st.write(f"Total ahorro grupo: {total_ahorro}")
        st.write(f"Utilidades del grupo: {utilidades}")

        fecha_cierre = st.date_input("Fecha de cierre de ciclo")
        saldo_caja_cierre = fetch_one(
            """
            SELECT COALESCE(SUM(c.Saldo_cierre),0) AS sc
            FROM caja c
            JOIN sesion s ON s.ID_Sesion = c.ID_Sesion
            WHERE s.ID_Grupo=%s
            """,
            (grupo_id,),
        )["sc"]

        if st.button("Confirmar cierre"):
            ciclo_id = execute(
                """
                INSERT INTO cierre_ciclo
                (ID_Grupo, Fecha_cierre, TotalAhorroGrupo, TotalGananciaGrupo, SaldoCierreCaja)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (grupo_id, fecha_cierre, total_ahorro, utilidades, saldo_caja_cierre),
            )

            for s in saldos:
                proporcion = (
                    s["SaldoFinalAhorro"] / total_ahorro if total_ahorro > 0 else 0
                )
                porcion_utilidad = utilidades * proporcion
                retiro_final = s["SaldoFinalAhorro"] + porcion_utilidad

                execute(
                    """
                    INSERT INTO cierre_ciclo_detalle
                    (ID_Ciclo, ID_Socio, SaldoFinalAhorro, PorcionFondoGrupo, RetiroFinal)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        ciclo_id,
                        s["ID_Socio"],
                        s["SaldoFinalAhorro"],
                        porcion_utilidad,
                        retiro_final,
                    ),
                )

            st.success(f"Cierre de ciclo registrado (ID {ciclo_id}).")


def pagina_reportes():
    require_role(["DIRECTIVA", "PROMOTORA", "ADMIN"])
    st.title("6. Reportes y transparencia")

    grupo_id = select_grupo_for_user()
    if not grupo_id:
        return

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Caja", "Ahorros y préstamos", "Cartera y mora", "Historial de reuniones"]
    )

    with tab1:
        st.subheader("Reporte de caja (ingresos/egresos)")
        movs = fetch_all(
            """
            SELECT s.Fecha_sesion, tm.Nombre_movimiento, mc.Monto, mc.Descripcion
            FROM movimiento_caja mc
            JOIN caja c   ON c.ID_Caja = mc.ID_Caja
            JOIN sesion s ON s.ID_Sesion = c.ID_Sesion
            JOIN tipo_movimiento tm ON tm.ID_TipoDeMovimiento = mc.ID_TipoDeMovimiento
            WHERE s.ID_Grupo=%s
            ORDER BY s.Fecha_sesion
            """,
            (grupo_id,),
        )
        if movs:
            st.dataframe(pd.DataFrame(movs))
        else:
            st.write("Sin movimientos registrados.")

    with tab2:
        st.subheader("Estado de ahorros por socio")
        ah = fetch_all(
            """
            SELECT so.Nombre, so.Apellido, SUM(ad.Saldo_final) AS saldo
            FROM ahorro_detalle ad
            JOIN ahorro a ON a.ID_Ahorro = ad.ID_Ahorro
            JOIN sesion s ON s.ID_Sesion = a.ID_Sesion
            JOIN socios so ON so.ID_Socio = ad.ID_Socio
            WHERE s.ID_Grupo=%s
            GROUP BY so.ID_Socio
            """,
            (grupo_id,),
        )
        if ah:
            st.dataframe(pd.DataFrame(ah))
        else:
            st.write("Aún no hay ahorros.")

    with tab3:
        st.subheader("Cartera de préstamos y porcentaje de mora (simple)")
        cartera = fetch_all(
            """
            SELECT so.Nombre, so.Apellido,
                   p.ID_Prestamo,
                   p.Monto_Desembolso,
                   COALESCE(SUM(dp.Total_Pagado),0) AS TotalPagado
            FROM prestamo p
            JOIN socios so ON so.ID_Socio = p.ID_Socio
            JOIN sesion s ON s.ID_Sesion = p.ID_Sesion
            LEFT JOIN detalles_pagos dp ON dp.ID_Prestamo = p.ID_Prestamo
            WHERE s.ID_Grupo=%s
            GROUP BY p.ID_Prestamo
            """,
            (grupo_id,),
        )
        if cartera:
            df = pd.DataFrame(cartera)
            df["SaldoPendiente"] = df["Monto_Desembolso"] - df["TotalPagado"]
            st.dataframe(df)

            total_prestado = df["Monto_Desembolso"].sum()
            total_pend = df["SaldoPendiente"].sum()
            mora_pct = (total_pend / total_prestado) * 100 if total_prestado > 0 else 0
            st.write(f"Total prestado: {total_prestado:.2f}")
            st.write(f"Saldo pendiente: {total_pend:.2f}")
            st.write(f"Porcentaje de mora (aprox): {mora_pct:.2f}%")
        else:
            st.write("No hay préstamos registrados en este grupo.")

    with tab4:
        st.subheader("Historial de reuniones y actas (resumen)")
        sesiones = fetch_all(
            """
            SELECT s.ID_Sesion, s.Fecha_sesion, s.Total_presentes
            FROM sesion s
            WHERE s.ID_Grupo=%s
            ORDER BY s.Fecha_sesion
            """,
            (grupo_id,),
        )
        if sesiones:
            st.dataframe(pd.DataFrame(sesiones))
        else:
            st.write("No hay reuniones registradas.")


# ---------- Main ----------
def main():
    require_login()
    user = get_current_user()

    st.sidebar.title("Menú")
    logout_button()

    opciones = ["Dashboard"]

    if user["rol"] in ("ADMIN", "PROMOTORA"):
        opciones.append("Grupos y reglas")
    if user["rol"] in ("DIRECTIVA", "ADMIN"):
        opciones.extend(["Socios y asistencia", "Ahorros", "Préstamos", "Caja", "Cierre de ciclo"])
    if user["rol"] in ("DIRECTIVA", "PROMOTORA", "ADMIN"):
        opciones.append("Reportes")

    page = st.sidebar.radio("Ir a", opciones)

    if page == "Dashboard":
        pagina_dashboard()
    elif page == "Grupos y reglas":
        pagina_grupos_y_reglas()
    elif page == "Socios y asistencia":
        pagina_socios_y_asistencia()
    elif page == "Ahorros":
        pagina_ahorros()
    elif page == "Préstamos":
        pagina_prestamos()
    elif page == "Caja":
        pagina_caja()
    elif page == "Cierre de ciclo":
        pagina_cierre_ciclo()
    elif page == "Reportes":
        pagina_reportes()


if __name__ == "__main__":
    main()
