# -*- coding: utf-8 -*-
"""Banco de pruebas del módulo de autenticación (calculos/auth.py).

Ejecutar:  python scripts/test_auth.py
No requiere streamlit (prueba solo la capa de datos).
"""
import os
import sys
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculos import auth

OKS, FALLOS = [], []


def check(nombre, cond):
    (OKS if cond else FALLOS).append(nombre)
    print(("✅" if cond else "❌"), nombre)


def main():
    tmp = tempfile.mktemp(suffix=".db")
    try:
        # 1. DB vacía
        check("DB nueva sin usuarios", not auth.hay_usuarios(tmp))

        # 2. Crear admin y cliente prueba
        auth.crear_usuario("Admin@Test.com", "clave123", "Admin",
                           rol="admin", plan="ilimitado", dias_vigencia=None, ruta=tmp)
        auth.crear_usuario("cliente@test.com", "secreta1", "Cliente",
                           empresa="ACME", plan="prueba", dias_vigencia=14, ruta=tmp)
        check("hay_usuarios tras crear", auth.hay_usuarios(tmp))
        check("email normalizado a minúsculas",
              auth.obtener_usuario("admin@test.com", tmp) is not None)

        # 3. Duplicado y validaciones
        try:
            auth.crear_usuario("cliente@test.com", "otraclave", "X", ruta=tmp)
            check("rechaza email duplicado", False)
        except ValueError:
            check("rechaza email duplicado", True)
        try:
            auth.crear_usuario("x@y.com", "123", "X", ruta=tmp)
            check("rechaza contraseña corta", False)
        except ValueError:
            check("rechaza contraseña corta", True)
        try:
            auth.crear_usuario("sinArroba", "clave123", "X", ruta=tmp)
            check("rechaza correo inválido", False)
        except ValueError:
            check("rechaza correo inválido", True)

        # 4. Login
        u, m = auth.verificar_credenciales("CLIENTE@test.com", "secreta1", tmp)
        check("login correcto", u is not None and u["empresa"] == "ACME")
        u2, m2 = auth.verificar_credenciales("cliente@test.com", "mala", tmp)
        check("login clave errada rechazado", u2 is None and "incorrect" in m2)
        u3, m3 = auth.verificar_credenciales("nadie@test.com", "x", tmp)
        check("login usuario inexistente rechazado", u3 is None)

        # 5. Vigencia
        adm = auth.obtener_usuario("admin@test.com", tmp)
        cli = auth.obtener_usuario("cliente@test.com", tmp)
        check("admin sin vencimiento", auth.dias_restantes(adm) is None)
        check("trial 14 días", auth.dias_restantes(cli) == 14)
        check("ambos vigentes", auth.esta_vigente(adm) and auth.esta_vigente(cli))

        # 6. Vencimiento en el pasado
        import sqlite3
        con = sqlite3.connect(tmp)
        ayer = (date.today() - timedelta(days=3)).isoformat()
        con.execute("UPDATE usuarios SET fecha_vencimiento=? WHERE email=?",
                    (ayer, "cliente@test.com"))
        con.commit(); con.close()
        cli = auth.obtener_usuario("cliente@test.com", tmp)
        check("vencido detectado", not auth.esta_vigente(cli)
              and auth.dias_restantes(cli) == -3)

        # 7. Extender desde vencido → cuenta desde hoy
        nuevo = auth.extender_vencimiento("cliente@test.com", 30, tmp)
        check("extender vencido parte de hoy",
              nuevo == (date.today() + timedelta(days=30)).isoformat())
        # 7b. Extender vigente → suma sobre el vencimiento futuro
        nuevo2 = auth.extender_vencimiento("cliente@test.com", 30, tmp)
        check("extender vigente suma al futuro",
              nuevo2 == (date.today() + timedelta(days=60)).isoformat())

        # 8. Desactivar / reactivar
        auth.actualizar_usuario("cliente@test.com", activo=False, ruta=tmp)
        u4, m4 = auth.verificar_credenciales("cliente@test.com", "secreta1", tmp)
        check("desactivado no entra", u4 is None and "desactivada" in m4)
        auth.actualizar_usuario("cliente@test.com", activo=True, ruta=tmp)
        u5, _ = auth.verificar_credenciales("cliente@test.com", "secreta1", tmp)
        check("reactivado entra", u5 is not None)

        # 9. Tokens de sesión
        tok = auth.crear_token_sesion("cliente@test.com", tmp)
        check("token restaura usuario",
              (auth.usuario_por_token(tok, tmp) or {}).get("email")
              == "cliente@test.com")
        check("token inválido rechazado",
              auth.usuario_por_token("token-falso", tmp) is None)
        auth.borrar_token(tok, tmp)
        check("token borrado no restaura", auth.usuario_por_token(tok, tmp) is None)

        # 9b. Desactivar borra sesiones
        tok2 = auth.crear_token_sesion("cliente@test.com", tmp)
        auth.actualizar_usuario("cliente@test.com", activo=False, ruta=tmp)
        check("desactivar invalida tokens", auth.usuario_por_token(tok2, tmp) is None)
        auth.actualizar_usuario("cliente@test.com", activo=True, ruta=tmp)

        # 10. Cambio de contraseña invalida sesiones
        tok3 = auth.crear_token_sesion("cliente@test.com", tmp)
        auth.cambiar_password("cliente@test.com", "nueva123", tmp)
        u6, _ = auth.verificar_credenciales("cliente@test.com", "nueva123", tmp)
        check("nueva contraseña funciona", u6 is not None)
        u7, _ = auth.verificar_credenciales("cliente@test.com", "secreta1", tmp)
        check("vieja contraseña ya no", u7 is None)
        check("cambio de clave invalida tokens",
              auth.usuario_por_token(tok3, tmp) is None)

        # 11. Cambiar plan
        auth.actualizar_usuario("cliente@test.com", plan="anual", ruta=tmp)
        check("plan actualizado",
              auth.obtener_usuario("cliente@test.com", tmp)["plan"] == "anual")
        try:
            auth.actualizar_usuario("cliente@test.com", plan="vip", ruta=tmp)
            check("rechaza plan inválido", False)
        except ValueError:
            check("rechaza plan inválido", True)

        # 12. Eliminar
        auth.eliminar_usuario("cliente@test.com", tmp)
        check("usuario eliminado",
              auth.obtener_usuario("cliente@test.com", tmp) is None)

        # 13. Hash distinto por salt
        auth.crear_usuario("a@b.com", "mismaclave", "A", ruta=tmp)
        auth.crear_usuario("c@d.com", "mismaclave", "C", ruta=tmp)
        ua, uc = auth.obtener_usuario("a@b.com", tmp), auth.obtener_usuario("c@d.com", tmp)
        check("misma clave → hashes distintos (salt)", ua["hash"] != uc["hash"])
    finally:
        for ext in ("", "-wal", "-shm"):
            try:
                os.remove(tmp + ext)
            except OSError:
                pass

    print(f"\n{len(OKS)} OK, {len(FALLOS)} fallos")
    if FALLOS:
        print("FALLARON:", FALLOS)
        sys.exit(1)


if __name__ == "__main__":
    main()
