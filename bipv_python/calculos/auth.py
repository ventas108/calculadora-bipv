# -*- coding: utf-8 -*-
"""
Autenticación y control de acceso — Calculadora BIPV.

- Usuarios en SQLite (datos/usuarios.db) con contraseña hasheada (PBKDF2-SHA256).
- Roles: 'admin' (acceso total + panel de administración) y 'cliente'.
- Planes: 'prueba', 'mensual', 'anual', 'ilimitado' (sin vencimiento).
- Sesión persistente vía token firmado en query param (?s=...) para que un
  refresco del navegador no pida la clave de nuevo.

Uso en cada página:
    from calculos.auth import requerir_login
    requerir_login()
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

_DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB = os.path.join(_DIR_BASE, "datos", "usuarios.db")

_PBKDF2_ITERS = 200_000
DIAS_TOKEN_SESION = 7           # vigencia del "recuérdame"; se rota en cada restauración
RUTA_CODIGO_SETUP = os.path.join(_DIR_BASE, "datos", "codigo_configuracion.txt")
PLANES = ("prueba", "mensual", "anual", "ilimitado")

CONTACTO_RENOVACION = (
    "Para activar o renovar tu plan escríbenos a **INNOVACION QUIMICA SAS** "
    "— WhatsApp/correo del administrador."
)


# ────────────────────────── infraestructura DB ──────────────────────────────
def _conn(ruta: str | None = None) -> sqlite3.Connection:
    ruta = ruta or RUTA_DB
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    con = sqlite3.connect(ruta, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    return con


def init_db(ruta: str | None = None) -> None:
    with _conn(ruta) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                empresa TEXT DEFAULT '',
                hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'cliente',
                plan TEXT NOT NULL DEFAULT 'prueba',
                fecha_vencimiento TEXT,          -- ISO 'YYYY-MM-DD' o NULL (sin vencimiento)
                activo INTEGER NOT NULL DEFAULT 1,
                creado TEXT NOT NULL,
                ultimo_acceso TEXT
            )""")
        con.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                token_hash TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expira TEXT NOT NULL             -- ISO datetime
            )""")


# ────────────────────────── contraseñas ─────────────────────────────────────
def _hash_password(password: str, salt_hex: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _PBKDF2_ITERS
    )
    return dk.hex()


def _password_ok(password: str, salt_hex: str, hash_hex: str) -> bool:
    return hmac.compare_digest(_hash_password(password, salt_hex), hash_hex)


# ────────────────────────── CRUD usuarios ───────────────────────────────────
def _norm_email(email: str) -> str:
    return (email or "").strip().lower()


def hay_usuarios(ruta: str | None = None) -> bool:
    init_db(ruta)
    with _conn(ruta) as con:
        return con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] > 0


def crear_usuario(email: str, password: str, nombre: str, *,
                  empresa: str = "", rol: str = "cliente",
                  plan: str = "prueba", dias_vigencia: Optional[int] = 14,
                  ruta: str | None = None) -> None:
    """dias_vigencia=None → sin vencimiento (ej. admin o plan ilimitado)."""
    email = _norm_email(email)
    if not email or "@" not in email:
        raise ValueError("Correo inválido.")
    if len(password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    if plan not in PLANES:
        raise ValueError(f"Plan inválido: {plan}")
    init_db(ruta)
    salt = secrets.token_hex(16)
    venc = (date.today() + timedelta(days=dias_vigencia)).isoformat() \
        if dias_vigencia is not None else None
    with _conn(ruta) as con:
        try:
            con.execute(
                "INSERT INTO usuarios (email,nombre,empresa,hash,salt,rol,plan,"
                "fecha_vencimiento,activo,creado) VALUES (?,?,?,?,?,?,?,?,1,?)",
                (email, nombre.strip(), empresa.strip(),
                 _hash_password(password, salt), salt, rol, plan, venc,
                 datetime.now().isoformat(timespec="seconds")))
        except sqlite3.IntegrityError:
            raise ValueError("Ya existe un usuario con ese correo.")


def obtener_usuario(email: str, ruta: str | None = None) -> Optional[dict]:
    init_db(ruta)
    with _conn(ruta) as con:
        row = con.execute("SELECT * FROM usuarios WHERE email=?",
                          (_norm_email(email),)).fetchone()
        return dict(row) if row else None


def listar_usuarios(ruta: str | None = None) -> list[dict]:
    init_db(ruta)
    with _conn(ruta) as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM usuarios ORDER BY rol DESC, creado DESC")]


def verificar_credenciales(email: str, password: str,
                           ruta: str | None = None) -> tuple[Optional[dict], str]:
    """Devuelve (usuario, "") si ok, o (None, motivo)."""
    u = obtener_usuario(email, ruta)
    if not u or not _password_ok(password, u["salt"], u["hash"]):
        return None, "Correo o contraseña incorrectos."
    if not u["activo"]:
        return None, "Tu cuenta está desactivada. " + CONTACTO_RENOVACION
    with _conn(ruta) as con:
        con.execute("UPDATE usuarios SET ultimo_acceso=? WHERE email=?",
                    (datetime.now().isoformat(timespec="seconds"), u["email"]))
    return u, ""


def dias_restantes(usuario: dict) -> Optional[int]:
    """None → sin vencimiento. Negativo → vencido."""
    if not usuario.get("fecha_vencimiento"):
        return None
    return (date.fromisoformat(usuario["fecha_vencimiento"]) - date.today()).days


def esta_vigente(usuario: dict) -> bool:
    d = dias_restantes(usuario)
    return d is None or d >= 0


def extender_vencimiento(email: str, dias: int, ruta: str | None = None) -> str:
    """Suma días desde hoy o desde el vencimiento futuro (lo que sea mayor).

    Transacción BEGIN IMMEDIATE: dos renovaciones concurrentes no pierden días.
    """
    email = _norm_email(email)
    con = _conn(ruta)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT fecha_vencimiento FROM usuarios WHERE email=?",
            (email,)).fetchone()
        if not row:
            raise ValueError("Usuario no encontrado.")
        base = date.today()
        if row["fecha_vencimiento"]:
            v = date.fromisoformat(row["fecha_vencimiento"])
            if v > base:
                base = v
        nuevo = (base + timedelta(days=dias)).isoformat()
        con.execute("UPDATE usuarios SET fecha_vencimiento=? WHERE email=?",
                    (nuevo, email))
        con.commit()
        return nuevo
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def actualizar_usuario(email: str, *, plan: str | None = None,
                       activo: bool | None = None,
                       sin_vencimiento: bool = False,
                       ruta: str | None = None) -> None:
    email = _norm_email(email)
    with _conn(ruta) as con:
        if plan is not None:
            if plan not in PLANES:
                raise ValueError(f"Plan inválido: {plan}")
            con.execute("UPDATE usuarios SET plan=? WHERE email=?", (plan, email))
        if activo is not None:
            con.execute("UPDATE usuarios SET activo=? WHERE email=?",
                        (1 if activo else 0, email))
            if not activo:
                con.execute("DELETE FROM sesiones WHERE email=?", (email,))
        if sin_vencimiento:
            con.execute("UPDATE usuarios SET fecha_vencimiento=NULL WHERE email=?",
                        (email,))


def cambiar_password(email: str, password_nuevo: str,
                     ruta: str | None = None) -> None:
    if len(password_nuevo) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    u = obtener_usuario(email, ruta)
    if not u:
        raise ValueError("Usuario no encontrado.")
    salt = secrets.token_hex(16)
    with _conn(ruta) as con:
        con.execute("UPDATE usuarios SET hash=?, salt=? WHERE email=?",
                    (_hash_password(password_nuevo, salt), salt, u["email"]))
        con.execute("DELETE FROM sesiones WHERE email=?", (u["email"],))


def eliminar_usuario(email: str, ruta: str | None = None) -> None:
    email = _norm_email(email)
    with _conn(ruta) as con:
        con.execute("DELETE FROM usuarios WHERE email=?", (email,))
        con.execute("DELETE FROM sesiones WHERE email=?", (email,))


# ────────────────────────── tokens de sesión ────────────────────────────────
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_token_sesion(email: str, ruta: str | None = None) -> str:
    token = secrets.token_urlsafe(32)
    expira = (datetime.now() + timedelta(days=DIAS_TOKEN_SESION)).isoformat(
        timespec="seconds")
    with _conn(ruta) as con:
        con.execute("INSERT OR REPLACE INTO sesiones VALUES (?,?,?)",
                    (_hash_token(token), _norm_email(email), expira))
        # higiene: borrar tokens expirados
        con.execute("DELETE FROM sesiones WHERE expira < ?",
                    (datetime.now().isoformat(timespec="seconds"),))
    return token


def usuario_por_token(token: str, ruta: str | None = None) -> Optional[dict]:
    if not token:
        return None
    init_db(ruta)
    with _conn(ruta) as con:
        row = con.execute("SELECT email, expira FROM sesiones WHERE token_hash=?",
                          (_hash_token(token),)).fetchone()
    if not row or row["expira"] < datetime.now().isoformat(timespec="seconds"):
        return None
    return obtener_usuario(row["email"], ruta)


def borrar_token(token: str, ruta: str | None = None) -> None:
    if not token:
        return
    with _conn(ruta) as con:
        con.execute("DELETE FROM sesiones WHERE token_hash=?", (_hash_token(token),))


# ────────────────────────── capa Streamlit ──────────────────────────────────
_ETIQUETA_PLAN = {"prueba": "🕐 Prueba gratuita", "mensual": "📅 Plan Mensual",
                  "anual": "🗓️ Plan Anual", "ilimitado": "♾️ Ilimitado"}


def _login_form(st) -> None:
    st.title("🔐 Calculadora BIPV — Acceso")
    st.caption("Software profesional de simulación fotovoltaica · "
               "INNOVACION QUIMICA SAS")
    with st.form("form_login"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        ok = st.form_submit_button("Ingresar", type="primary",
                                   use_container_width=True)
    if ok:
        u, motivo = verificar_credenciales(email, password)
        if u is None:
            st.error(motivo)
        else:
            st.session_state["auth_email"] = u["email"]
            token = crear_token_sesion(u["email"])
            st.query_params["s"] = token
            st.session_state["auth_token"] = token
            st.rerun()
    st.info("¿No tienes cuenta o venció tu acceso? " + CONTACTO_RENOVACION)


def _codigo_setup(ruta: str | None = None) -> str:
    """Código de un solo uso para el bootstrap del primer admin.

    Se genera aleatorio en datos/codigo_configuracion.txt (solo legible por
    quien tiene acceso SSH al servidor). Evita que un visitante cualquiera
    se cree la cuenta de administrador en el primer arranque.
    """
    path = ruta or RUTA_CODIGO_SETUP
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(4).upper())
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _form_primer_admin(st) -> None:
    st.title("⚙️ Configuración inicial")
    codigo_real = _codigo_setup()
    st.warning("No existe ningún usuario todavía. Crea la cuenta del "
               "**administrador** (tú). Esto solo se hace una vez.")
    st.info("Por seguridad necesitas el **código de configuración**. "
            "Léelo en el servidor con:\n\n"
            "`cat /var/www/bipv/calculadora-bipv/bipv_python/datos/codigo_configuracion.txt`")
    with st.form("form_admin_inicial"):
        codigo = st.text_input("Código de configuración")
        nombre = st.text_input("Tu nombre")
        email = st.text_input("Correo del administrador")
        p1 = st.text_input("Contraseña", type="password")
        p2 = st.text_input("Repite la contraseña", type="password")
        ok = st.form_submit_button("Crear administrador", type="primary")
    if ok:
        if not hmac.compare_digest(codigo.strip().upper(), codigo_real):
            st.error("Código de configuración incorrecto.")
            return
        if p1 != p2:
            st.error("Las contraseñas no coinciden.")
            return
        try:
            crear_usuario(email, p1, nombre or "Administrador",
                          rol="admin", plan="ilimitado", dias_vigencia=None)
            try:
                os.remove(RUTA_CODIGO_SETUP)   # código de un solo uso
            except OSError:
                pass
            st.success("Administrador creado. Ingresa con tu correo y contraseña.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))


def _bloqueo_vencido(st, usuario: dict) -> None:
    st.title("⏳ Tu acceso venció")
    venc = usuario.get("fecha_vencimiento", "")
    st.error(f"Tu plan **{_ETIQUETA_PLAN.get(usuario['plan'], usuario['plan'])}** "
             f"venció el **{venc}**. Tus proyectos están guardados y no se pierden.")
    st.info(CONTACTO_RENOVACION)
    if st.button("Cerrar sesión"):
        cerrar_sesion(st)


def cerrar_sesion(st) -> None:
    borrar_token(st.session_state.get("auth_token", ""))
    for k in ("auth_email", "auth_token"):
        st.session_state.pop(k, None)
    st.query_params.clear()
    st.rerun()


def usuario_actual(st) -> Optional[dict]:
    email = st.session_state.get("auth_email")
    return obtener_usuario(email) if email else None


def requerir_login(solo_admin: bool = False):
    """Portero de acceso. Llamar al inicio de app.py y de cada página.

    Detiene la ejecución (st.stop) si no hay sesión válida.
    Devuelve el dict del usuario autenticado.
    """
    import streamlit as st

    # Primer arranque: crear admin
    if not hay_usuarios():
        _form_primer_admin(st)
        st.stop()

    # Restaurar sesión por token en URL (sobrevive al refresco del navegador).
    # El token se ROTA en cada restauración: el que quedó en historial/logs
    # muere de inmediato y se emite uno nuevo.
    if "auth_email" not in st.session_state:
        token = st.query_params.get("s", "")
        u = usuario_por_token(token)
        if u and u["activo"]:
            borrar_token(token)
            nuevo = crear_token_sesion(u["email"])
            st.session_state["auth_email"] = u["email"]
            st.session_state["auth_token"] = nuevo
            st.query_params["s"] = nuevo

    if "auth_email" not in st.session_state:
        _login_form(st)
        st.stop()

    # Revocación efectiva: si el token de esta sesión ya no existe en la DB
    # (cambio de contraseña, desactivación, logout remoto), se cierra aquí.
    if usuario_por_token(st.session_state.get("auth_token", "")) is None:
        cerrar_sesion(st)
        st.stop()

    usuario = usuario_actual(st)
    if usuario is None or not usuario["activo"]:
        cerrar_sesion(st)          # hace st.rerun(); no continúa
        st.stop()

    if not esta_vigente(usuario) and usuario["rol"] != "admin":
        _bloqueo_vencido(st, usuario)
        st.stop()

    if solo_admin and usuario["rol"] != "admin":
        st.error("🔒 Esta sección es solo para el administrador.")
        st.stop()

    _sidebar_estado(st, usuario)
    return usuario


def _sidebar_estado(st, usuario: dict) -> None:
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"👤 **{usuario['nombre']}**")
        plan_txt = _ETIQUETA_PLAN.get(usuario["plan"], usuario["plan"])
        d = dias_restantes(usuario)
        if d is None:
            st.caption(plan_txt)
        elif d <= 3:
            st.warning(f"{plan_txt} — ⚠️ te quedan **{d} día(s)**. "
                       "Contacta al administrador para renovar.")
        elif d <= 7:
            st.caption(f"{plan_txt} — te quedan {d} días")
        else:
            st.caption(f"{plan_txt} — vence {usuario['fecha_vencimiento']}")
        if st.button("Cerrar sesión", key="btn_logout", use_container_width=True):
            cerrar_sesion(st)
