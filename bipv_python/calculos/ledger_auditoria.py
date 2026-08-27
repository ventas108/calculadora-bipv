# -*- coding: utf-8 -*-
"""Ledger de Auditoría — cadena de hashes por proyecto.

Registra, con integridad verificable, cada resultado "oficial" que sale de
la calculadora: para un banco/ITA (bancabilidad), como verificación
presupuestal informativa para un cliente, o como diagnóstico de un sistema
ya instalado. Res. CREG 174 de 2021, Art. 6, exige que los cálculos tengan
trazabilidad para determinar si son reales o actualizados -- este módulo
implementa esa trazabilidad de forma verificable, no solo declarativa.

NO es un log automático de cada cálculo de prueba: solo se sella cuando el
usuario lo pide explícitamente (botón "🔒 Sellar" o al generar el Reporte
PDF), para no llenar la cadena de ruido de cada ajuste de slider.

Cada eslabón encadena su hash con el del eslabón anterior del MISMO
proyecto (SHA-256 de todos sus campos + el hash anterior). Si alguien edita
un eslabón ya guardado por fuera de la app -- incluso un solo carácter de
la nota -- su hash deja de coincidir con el que usó el siguiente eslabón
como "hash_anterior": la ruptura es detectable recorriendo la cadena, sin
necesitar un respaldo externo ni ninguna dependencia nueva (solo la
librería estándar de Python).

Límite honesto: esto protege contra la edición silenciosa de UN eslabón.
No protege contra borrar el archivo completo y empezar de cero -- eso
requeriría un ancla externa (publicar el hash raíz en otro sistema), fuera
de alcance por ahora.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime

_DIR_LEDGER = os.path.join(os.path.dirname(__file__), "..", "datos", "ledger_auditoria")

# ── _hash_usuario/nombre_a_slug duplicadas de calculos.proyectos_manager ────
# (deliberado, no un descuido): ese módulo hace `import streamlit` a nivel de
# módulo, así que importarlo aquí arrastraría esa dependencia a un módulo que
# no tiene nada que ver con la UI -- y dejaría intestable en aislamiento
# justo la lógica de la cadena de hashes, la parte más sensible de todo este
# archivo. Son funciones puras y triviales; si algún día cambian en
# proyectos_manager.py, deben actualizarse aquí también.

def _hash_usuario(usuario: str) -> str:
    return hashlib.sha256((usuario or "").strip().lower().encode()).hexdigest()[:12]


def _nombre_a_slug(nombre: str) -> str:
    s = (nombre or "").lower().strip()
    for src, dst in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                     ("ñ", "n"), ("ü", "u"), ("à", "a"), ("â", "a"), ("ê", "e"),
                     ("î", "i"), ("ô", "o"), ("û", "u")]:
        s = s.replace(src, dst)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "proyecto"

GENESIS = "GENESIS"

TIPOS_VALIDOS = ("presupuesto_bancable", "presupuesto_informativo", "diagnostico_operacion",
                  "diagrama_unifilar")

TIPO_LABELS = {
    "presupuesto_bancable": "🏦 Presupuesto bancable (banco/ITA)",
    "presupuesto_informativo": "📋 Verificación presupuestal informativa",
    "diagnostico_operacion": "🔍 Diagnóstico de sistema en operación",
    "diagrama_unifilar": "⚡ Diagrama unifilar (diseño eléctrico)",
}


def _slug_proyecto(nombre_proyecto: str, usuario: str) -> str:
    return f"{_hash_usuario(usuario)}__{_nombre_a_slug(nombre_proyecto or 'proyecto')}"


def _ruta_ledger(nombre_proyecto: str, usuario: str) -> str:
    return os.path.join(_DIR_LEDGER, f"{_slug_proyecto(nombre_proyecto, usuario)}.json")


def _cargar(nombre_proyecto: str, usuario: str) -> list[dict]:
    ruta = _ruta_ledger(nombre_proyecto, usuario)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _escribir_atomico(ruta: str, eslabones: list[dict]) -> bool:
    """Temp-file + os.replace: un corte a mitad de escritura nunca deja el
    ledger truncado (mismo patrón que datos/diagnosticos/ y presupuesto)."""
    try:
        os.makedirs(_DIR_LEDGER, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_DIR_LEDGER, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(eslabones, f, ensure_ascii=False, indent=1, sort_keys=True)
            os.replace(tmp, ruta)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return True
    except OSError:
        return False


def _calcular_hash(proyecto: str, usuario: str, tipo: str, timestamp: str,
                    insumos: dict, resultados: dict, nota: str,
                    hash_anterior: str) -> str:
    """El hash cubre TODOS los campos del eslabón + el hash del anterior --
    alterar cualquier campo de un eslabón ya guardado (incluida la nota)
    rompe su propio hash y, en cadena, el de todos los que le siguen."""
    payload = json.dumps(
        {
            "proyecto": proyecto, "usuario": usuario, "tipo": tipo,
            "timestamp": timestamp, "insumos": insumos, "resultados": resultados,
            "nota": nota, "hash_anterior": hash_anterior,
        },
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sellar_resultado(nombre_proyecto: str, usuario: str, tipo: str,
                      insumos: dict, resultados: dict, nota: str = "") -> dict:
    """Agrega un eslabón nuevo al final de la cadena de este proyecto.

    Lanza ValueError si `tipo` no es uno de TIPOS_VALIDOS. Devuelve el
    eslabón creado (incluye "hash_propio", el que se imprime en el PDF como
    "ID de verificación") o {} si falló la escritura a disco -- el
    llamador debe avisar al usuario, no silenciar (misma política que el
    histórico de diagnóstico)."""
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"tipo debe ser uno de {TIPOS_VALIDOS}, recibido: {tipo!r}")

    eslabones = _cargar(nombre_proyecto, usuario)
    hash_anterior = eslabones[-1]["hash_propio"] if eslabones else GENESIS
    timestamp = datetime.now().isoformat(timespec="seconds")
    hash_propio = _calcular_hash(nombre_proyecto, usuario, tipo, timestamp,
                                  insumos, resultados, nota, hash_anterior)
    eslabon = {
        "id": len(eslabones) + 1,
        "proyecto": nombre_proyecto, "usuario": usuario, "tipo": tipo,
        "timestamp": timestamp, "insumos": insumos, "resultados": resultados,
        "nota": nota, "hash_anterior": hash_anterior, "hash_propio": hash_propio,
    }
    eslabones.append(eslabon)
    ok = _escribir_atomico(_ruta_ledger(nombre_proyecto, usuario), eslabones)
    return eslabon if ok else {}


def listar_eslabones(nombre_proyecto: str, usuario: str) -> list[dict]:
    return _cargar(nombre_proyecto, usuario)


def verificar_cadena(nombre_proyecto: str, usuario: str) -> dict:
    """Recorre la cadena completa recalculando cada hash desde sus datos.

    Devuelve {"integra": bool, "eslabones_verificados": int,
    "primer_eslabon_roto": int | None}."""
    eslabones = _cargar(nombre_proyecto, usuario)
    hash_anterior = GENESIS
    for i, e in enumerate(eslabones):
        if e.get("hash_anterior") != hash_anterior:
            return {"integra": False, "eslabones_verificados": i,
                    "primer_eslabon_roto": e.get("id", i + 1)}
        hash_recalculado = _calcular_hash(
            e.get("proyecto"), e.get("usuario"), e.get("tipo"), e.get("timestamp"),
            e.get("insumos"), e.get("resultados"), e.get("nota"), e.get("hash_anterior"),
        )
        if hash_recalculado != e.get("hash_propio"):
            return {"integra": False, "eslabones_verificados": i,
                    "primer_eslabon_roto": e.get("id", i + 1)}
        hash_anterior = e["hash_propio"]
    return {"integra": True, "eslabones_verificados": len(eslabones),
            "primer_eslabon_roto": None}


def exportar_cadena(nombre_proyecto: str, usuario: str, formato: str = "json") -> bytes:
    eslabones = _cargar(nombre_proyecto, usuario)
    if formato == "json":
        return json.dumps(eslabones, ensure_ascii=False, indent=2).encode("utf-8")
    if formato == "markdown":
        lineas = [f"# Ledger de auditoría — {nombre_proyecto}", ""]
        for e in eslabones:
            lineas.append(f"## Eslabón {e['id']} — {TIPO_LABELS.get(e['tipo'], e['tipo'])}")
            lineas.append(f"- Fecha: {e['timestamp']}")
            lineas.append(f"- Usuario: {e['usuario']}")
            lineas.append(f"- Nota: {e['nota'] or '(sin nota)'}")
            lineas.append(f"- Hash: `{e['hash_propio']}`")
            lineas.append(f"- Insumos: `{json.dumps(e['insumos'], ensure_ascii=False)}`")
            lineas.append(f"- Resultados: `{json.dumps(e['resultados'], ensure_ascii=False)}`")
            lineas.append("")
        return "\n".join(lineas).encode("utf-8")
    raise ValueError(f"Formato no soportado: {formato!r} (usa 'json' o 'markdown')")


def construir_snapshot_insumos(estado: dict) -> dict:
    """Consolida, desde session_state, los insumos que determinan un
    resultado de Producción/Financiero -- mismo principio que
    contexto_sesion() del Asistente, pero para dejarlos congelados dentro
    de un eslabón. Solo incluye claves verificadas contra el código real de
    las páginas (no se adivina ningún nombre de sesión)."""
    return {
        "ciudad": estado.get("tmy_ciudad"),
        "tipo_instalacion": estado.get("tipo_instalacion"),
        "panel": estado.get("panel_nombre_dim"),
        "inversor": estado.get("inversor_nombre_dim"),
        "n_paneles": estado.get("N_paneles_final"),
        "p_stc_kw": estado.get("P_stc_kW_sistema"),
        "degradacion_pct_usada": estado.get("tasa_degradacion_usada"),
        "fuente_degradacion": estado.get("fuente_degradacion"),
        "tarifa_cop_kwh": estado.get("tarifa_cop_kwh"),
        "tipo_cambio_cop_usd": estado.get("tipo_cambio"),
        "capex_usd": estado.get("presupuesto_capex_usd"),
        "capex_fuente": estado.get("presupuesto_fuente"),
    }


def construir_snapshot_resultados(estado: dict) -> dict:
    """Consolida los resultados clave que se certifican en este eslabón
    (E_ac, PR, indicadores financieros de calcular_metricas())."""
    metricas = estado.get("metricas_financiero") or {}
    return {
        "e_ac_anual_kwh": estado.get("E_ac_anual_kWh"),
        "pr_sistema": estado.get("PR_sistema"),
        "vpn_usd": metricas.get("vpn_usd"),
        "tir_pct": metricas.get("tir_pct"),
        "payback_simple_anos": metricas.get("payback_simple"),
        "lcoe_usd_kwh": metricas.get("lcoe_usd_kWh"),
    }
