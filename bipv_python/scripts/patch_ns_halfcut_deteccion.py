#!/usr/bin/env python3
"""
Parche: Task #67 — Detectar N_s incorrecto en paneles half-cut antes del Motor IV
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_ns_halfcut_deteccion.py
    pm2 restart streamlit-bipv

Cambios:
  1. calculos/modelo_iv.py — nueva función verificar_ns_halfcut(panel)
     • Calcula Voc/N_s y compara con rango por tecnología (Mono-Si, Poli-Si, CdTe, CIGS, a-Si)
     • Detecta tipo "ns_duplicado" (half-cells contadas individualmente) y "ns_mitad"
     • Detecta indicadores en nombre del modelo (half-cut, halfcut, hc)

  2. calculos/modelo_iv.py — estimar_sdm_desde_ficha()
     • Cuando N_s proviene del catálogo y verificar_ns_halfcut detecta duplicado,
       usa N_s_sugerido = N_s // 2 automáticamente
     • Agrega al dict de retorno: _ns_corregido, _ns_original, _N_s_usado, _ns_halfcut_info

  3. pages/3_Motor_IV.py — importar verificar_ns_halfcut

  4. pages/3_Motor_IV.py — _analizar_panel_motiv()
     • Cuando N_s está definido, llama verificar_ns_halfcut y agrega advertencia detallada

  5. pages/3_Motor_IV.py — auto-activación con estimación
     • Si _ns_corregido, muestra st.error con N_s original vs corregido y
       qué campo del Excel actualizar
"""
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
errors = []

def patch(ruta: Path, buscar: str, reemplazar: str, desc: str):
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

# ─── Archivo 1: modelo_iv.py ──────────────────────────────────────────────────
_iv = BASE / "calculos" / "modelo_iv.py"

print(f"\n[1] {_iv.name} — agregar verificar_ns_halfcut() + rangos Voc/celda")
patch(
    _iv,
    buscar=(
        'def tiene_sdm_completo(panel: dict) -> bool:\n'
        '    """True si el panel tiene todos los parámetros SDM calibrados y válidos."""\n'
        '    return all(panel.get(k) not in (None, 0, "", "nan") for k in _SDM_KEYS)'
    ),
    reemplazar=(
        'def tiene_sdm_completo(panel: dict) -> bool:\n'
        '    """True si el panel tiene todos los parámetros SDM calibrados y válidos."""\n'
        '    return all(panel.get(k) not in (None, 0, "", "nan") for k in _SDM_KEYS)\n'
        '\n'
        '\n'
        '# ── Rangos Voc/celda @ STC esperados por tecnología (V/celda) ─────────────────\n'
        '_VOC_POR_CELDA_RANGO = {\n'
        '    "Mono-Si":  (0.55, 0.76),\n'
        '    "Poli-Si":  (0.52, 0.70),\n'
        '    "CdTe":     (0.76, 1.20),\n'
        '    "CIGS":     (0.52, 0.80),\n'
        '    "a-Si":     (0.58, 0.90),\n'
        '}\n'
        '_VOC_POR_CELDA_DEFAULT = (0.48, 1.25)\n'
        '_HALFCUT_KEYWORDS = ("half-cut", "half cut", "halfcut", "half_cut", " hc ", "-hc-", "-hc ")\n'
        '\n'
        '\n'
        'def verificar_ns_halfcut(panel: dict) -> "dict | None":\n'
        '    """\n'
        '    Detecta si N_s en el catálogo es incorrecto para paneles half-cut.\n'
        '\n'
        '    Los paneles half-cut listan N_s como el total de semiceldas (p.ej. 144)\n'
        '    cuando De Soto necesita las celdas equivalentes en serie (p.ej. 72).\n'
        '\n'
        '    Retorna None si no hay problema, o dict con:\n'
        '        tipo, Voc_por_celda, rango_esperado, N_s_ingresado,\n'
        '        N_s_sugerido, es_halfcut_nombre, tecnologia, mensaje\n'
        '    """\n'
        '    Voc = float(panel.get("Voc_stc") or panel.get("Voc") or 0)\n'
        '    N_s = panel.get("N_s")\n'
        '    if not (Voc > 10 and N_s and float(N_s) > 0):\n'
        '        return None\n'
        '\n'
        '    N_s_f = float(N_s)\n'
        '    voc_per_cell = Voc / N_s_f\n'
        '\n'
        '    tec_raw = str(panel.get("tecnologia", "")).strip().lower()\n'
        '    _MAP = {\n'
        '        "mono-si": "Mono-Si", "mono si": "Mono-Si", "monocrystalline": "Mono-Si",\n'
        '        "monocristalino": "Mono-Si", "mono": "Mono-Si",\n'
        '        "poli-si": "Poli-Si", "poly-si": "Poli-Si", "policristalino": "Poli-Si",\n'
        '        "multicrystalline": "Poli-Si", "poly": "Poli-Si",\n'
        '        "cdte": "CdTe", "cd te": "CdTe",\n'
        '        "cigs": "CIGS", "cis": "CIGS",\n'
        '        "a-si": "a-Si", "asi": "a-Si", "amorphous": "a-Si",\n'
        '    }\n'
        '    tec_norm = _MAP.get(tec_raw, "")\n'
        '    rango = _VOC_POR_CELDA_RANGO.get(tec_norm, _VOC_POR_CELDA_DEFAULT)\n'
        '    r_min, r_max = rango\n'
        '\n'
        '    nombre_lower = str(panel.get("nombre", "")).lower()\n'
        '    es_halfcut_nombre = any(kw in nombre_lower for kw in _HALFCUT_KEYWORDS)\n'
        '\n'
        '    tipo = None\n'
        '    N_s_sug = int(N_s_f)\n'
        '\n'
        '    if voc_per_cell < r_min * 0.65:\n'
        '        tipo    = "ns_duplicado"\n'
        '        N_s_sug = max(1, int(round(N_s_f / 2)))\n'
        '    elif voc_per_cell > r_max * 1.40:\n'
        '        tipo    = "ns_mitad"\n'
        '        N_s_sug = int(round(N_s_f * 2))\n'
        '\n'
        '    if tipo is None and not es_halfcut_nombre:\n'
        '        return None\n'
        '\n'
        '    if tipo is None:\n'
        '        return {\n'
        '            "tipo": "nombre_halfcut_ok", "Voc_por_celda": round(voc_per_cell, 4),\n'
        '            "rango_esperado": rango, "N_s_ingresado": int(N_s_f),\n'
        '            "N_s_sugerido": int(N_s_f), "es_halfcut_nombre": True,\n'
        '            "tecnologia": tec_norm or tec_raw,\n'
        '            "mensaje": (\n'
        '                f"El nombre indica **half-cut** y N_s={int(N_s_f)} da "\n'
        '                f"Voc/celda = {voc_per_cell:.3f} V — dentro del rango esperado. N_s parece correcto."\n'
        '            ),\n'
        '        }\n'
        '\n'
        '    _desc = {\n'
        '        "ns_duplicado": (\n'
        '            f"N_s={int(N_s_f)} parece el conteo de **semiceldas** (half-cut). "\n'
        '            f"De Soto necesita celdas equivalentes en serie = N_s // 2 = **{N_s_sug}**."\n'
        '        ),\n'
        '        "ns_mitad": (\n'
        '            f"N_s={int(N_s_f)} es demasiado bajo para Voc={Voc:.1f} V. Sugerido: **{N_s_sug}**."\n'
        '        ),\n'
        '    }\n'
        '    return {\n'
        '        "tipo": tipo, "Voc_por_celda": round(voc_per_cell, 4),\n'
        '        "rango_esperado": rango, "N_s_ingresado": int(N_s_f),\n'
        '        "N_s_sugerido": N_s_sug, "es_halfcut_nombre": es_halfcut_nombre,\n'
        '        "tecnologia": tec_norm or tec_raw, "mensaje": _desc[tipo],\n'
        '    }'
    ),
    desc="verificar_ns_halfcut + rangos"
)

print(f"\n[2] {_iv.name} — estimar_sdm_desde_ficha: corregir N_s half-cut automáticamente")
patch(
    _iv,
    buscar=(
        '    # ── a_ref = n × Ns × Vt ───────────────────────────────────────────────────\n'
        '    if NsA:\n'
        '        a_ref = float(NsA) * Vt_ref\n'
        '        N_s_est = N_s or int(round(float(NsA) / const.get("n_mediana", 1.05)))\n'
        '    elif N_s:\n'
        '        n_typ = {"CdTe": 1.09, "Mono-Si": 1.05, "Poli-Si": 1.10}.get(tec_norm, 1.05)\n'
        '        a_ref = n_typ * float(N_s) * Vt_ref\n'
        '        N_s_est = int(N_s)\n'
        '    else:\n'
        '        N_s_est = max(int(round(Voc / 0.65)), 36)  # ≈ 0.65 V/cell c-Si\n'
        '        n_typ = 1.05\n'
        '        a_ref = n_typ * N_s_est * Vt_ref'
    ),
    reemplazar=(
        '    # ── a_ref = n × Ns × Vt ───────────────────────────────────────────────────\n'
        '    _ns_corregido     = False\n'
        '    _ns_original      = None\n'
        '    _ns_halfcut_info  = None\n'
        '\n'
        '    if NsA:\n'
        '        a_ref = float(NsA) * Vt_ref\n'
        '        N_s_est = N_s or int(round(float(NsA) / const.get("n_mediana", 1.05)))\n'
        '    elif N_s:\n'
        '        n_typ = {"CdTe": 1.09, "Mono-Si": 1.05, "Poli-Si": 1.10}.get(tec_norm, 1.05)\n'
        '        _hc = verificar_ns_halfcut(panel)\n'
        '        if _hc and _hc["tipo"] == "ns_duplicado":\n'
        '            _ns_original     = int(float(N_s))\n'
        '            N_s_est          = _hc["N_s_sugerido"]\n'
        '            _ns_corregido    = True\n'
        '            _ns_halfcut_info = _hc\n'
        '        else:\n'
        '            N_s_est = int(N_s)\n'
        '        a_ref = n_typ * N_s_est * Vt_ref\n'
        '    else:\n'
        '        N_s_est = max(int(round(Voc / 0.65)), 36)  # ≈ 0.65 V/cell c-Si\n'
        '        n_typ = 1.05\n'
        '        a_ref = n_typ * N_s_est * Vt_ref'
    ),
    desc="estimar_sdm: corregir N_s half-cut"
)

print(f"\n[3] {_iv.name} — return dict de estimar_sdm_desde_ficha: agregar campos _ns_*")
patch(
    _iv,
    buscar=(
        '    return {\n'
        '        "nombre":     panel.get("nombre", "Panel"),\n'
        '        "tecnologia": tec_norm,\n'
        '        "I_L_ref":    I_L,\n'
        '        "I_o_ref":    I_o,\n'
        '        "R_s":        R_s,\n'
        '        "R_sh_ref":   R_sh,\n'
        '        "a_ref":      a_ref,\n'
        '        "Tk_alfa":    float(Tk_alfa) if Tk_alfa else alpha_pct if "alpha_pct" in dir() else 0.05,\n'
        '        "Tk_gamma":   float(Tk_gamma) if Tk_gamma else -0.40,\n'
        '        "Voc_stc":    Voc,\n'
        '        "Isc_stc":    Isc,\n'
        '        "Pmax_stc":   Vmp * Imp,\n'
        '        "R_sh_base":  0.0,\n'
        '        "_estimado":  True,\n'
        '        "_metodo":    _metodo,\n'
        '        "_tec_norm":  tec_norm,\n'
        '    }'
    ),
    reemplazar=(
        '    return {\n'
        '        "nombre":            panel.get("nombre", "Panel"),\n'
        '        "tecnologia":        tec_norm,\n'
        '        "I_L_ref":           I_L,\n'
        '        "I_o_ref":           I_o,\n'
        '        "R_s":               R_s,\n'
        '        "R_sh_ref":          R_sh,\n'
        '        "a_ref":             a_ref,\n'
        '        "Tk_alfa":           float(Tk_alfa) if Tk_alfa else alpha_pct if "alpha_pct" in dir() else 0.05,\n'
        '        "Tk_gamma":          float(Tk_gamma) if Tk_gamma else -0.40,\n'
        '        "Voc_stc":           Voc,\n'
        '        "Isc_stc":           Isc,\n'
        '        "Pmax_stc":          Vmp * Imp,\n'
        '        "R_sh_base":         0.0,\n'
        '        "_estimado":         True,\n'
        '        "_metodo":           _metodo,\n'
        '        "_tec_norm":         tec_norm,\n'
        '        "_ns_corregido":     _ns_corregido,\n'
        '        "_ns_original":      _ns_original,\n'
        '        "_N_s_usado":        N_s_est,\n'
        '        "_ns_halfcut_info":  _ns_halfcut_info,\n'
        '    }'
    ),
    desc="return dict: campos _ns_*"
)

# ─── Archivo 2: Motor_IV.py ───────────────────────────────────────────────────
_mot_files = glob.glob(str(BASE / "pages" / "*Motor_IV*.py"))
if not _mot_files:
    print("❌  3_Motor_IV.py no encontrado"); raise SystemExit(1)
_mot = Path(_mot_files[0])

print(f"\n[4] {_mot.name} — importar verificar_ns_halfcut")
patch(
    _mot,
    buscar=(
        'from calculos.modelo_iv import (\n'
        '    resolver_curva_iv,\n'
        '    validar_sdm_vs_ficha,\n'
        '    tiene_sdm_completo,\n'
        '    estimar_sdm_desde_ficha,\n'
        ')'
    ),
    reemplazar=(
        'from calculos.modelo_iv import (\n'
        '    resolver_curva_iv,\n'
        '    validar_sdm_vs_ficha,\n'
        '    tiene_sdm_completo,\n'
        '    estimar_sdm_desde_ficha,\n'
        '    verificar_ns_halfcut,\n'
        ')'
    ),
    desc="importar verificar_ns_halfcut"
)

print(f"\n[5] {_mot.name} — _analizar_panel_motiv: check N_s half-cut")
patch(
    _mot,
    buscar=(
        '        if not _val("N_s", "NsA"):\n'
        '            advertencias.append(("N_s", "Número de celdas en serie — se estimará desde Voc/0.65 V"))\n'
        '        if not p.get("tecnologia"):'
    ),
    reemplazar=(
        '        if not _val("N_s", "NsA"):\n'
        '            advertencias.append(("N_s", "Número de celdas en serie — se estimará desde Voc/0.65 V"))\n'
        '        else:\n'
        '            _hc = verificar_ns_halfcut(p)\n'
        '            if _hc and _hc["tipo"] == "ns_duplicado":\n'
        '                _r = _hc["rango_esperado"]\n'
        '                advertencias.append((\n'
        '                    f"⚠️ N_s incorrecto (half-cut)",\n'
        '                    f"N_s={_hc[\'N_s_ingresado\']} da **Voc/celda = {_hc[\'Voc_por_celda\']:.3f} V** "\n'
        '                    f"(rango esperado {_r[0]:.2f}–{_r[1]:.2f} V para {_hc[\'tecnologia\']}).  "\n'
        '                    f"Correcto para SDM: N_s = **{_hc[\'N_s_sugerido\']}** "\n'
        '                    f"(semiceldas ÷ 2). Corrige `Ns (Celdas Serie)` en el Excel."\n'
        '                ))\n'
        '            elif _hc and _hc["tipo"] == "ns_mitad":\n'
        '                _r = _hc["rango_esperado"]\n'
        '                advertencias.append((\n'
        '                    f"⚠️ N_s incorrecto (muy bajo)",\n'
        '                    f"N_s={_hc[\'N_s_ingresado\']} da **Voc/celda = {_hc[\'Voc_por_celda\']:.3f} V** "\n'
        '                    f"(rango esperado {_r[0]:.2f}–{_r[1]:.2f} V para {_hc[\'tecnologia\']}).  "\n'
        '                    f"Valor sugerido: N_s = **{_hc[\'N_s_sugerido\']}**."\n'
        '                ))\n'
        '        if not p.get("tecnologia"):'
    ),
    desc="_analizar_panel_motiv: check N_s half-cut"
)

print(f"\n[6] {_mot.name} — auto-activación: aviso si N_s fue corregido")
patch(
    _mot,
    buscar=(
        '                st.warning(\n'
        '                    f"🟡 **Auto-activado con estimación** — Panel: **{_panel_nom_ss}** "\n'
        '                    f"(catálogo Excel). Parámetros SDM estimados por **{_metodo_est}** "\n'
        '                    f"desde ficha técnica. Resultados orientativos.{_adv_lines}"\n'
        '                )'
    ),
    reemplazar=(
        '                st.warning(\n'
        '                    f"🟡 **Auto-activado con estimación** — Panel: **{_panel_nom_ss}** "\n'
        '                    f"(catálogo Excel). Parámetros SDM estimados por **{_metodo_est}** "\n'
        '                    f"desde ficha técnica. Resultados orientativos.{_adv_lines}"\n'
        '                )\n'
        '                if _sdm_est.get("_ns_corregido"):\n'
        '                    _hci = _sdm_est.get("_ns_halfcut_info", {})\n'
        '                    st.error(\n'
        '                        f"🔺 **N_s corregido automáticamente (half-cut):**  \\n"\n'
        '                        f"El catálogo tiene N_s = **{_sdm_est[\'_ns_original\']}** "\n'
        '                        f"(Voc/celda = {_hci.get(\'Voc_por_celda\', 0):.3f} V, fuera del rango "\n'
        '                        f"{_hci.get(\'rango_esperado\', (0,0))[0]:.2f}–"\n'
        '                        f"{_hci.get(\'rango_esperado\', (0,0))[1]:.2f} V para "\n'
        '                        f"{_hci.get(\'tecnologia\', \'?\')}).  \\n"\n'
        '                        f"Se usó **N_s = {_sdm_est[\'_N_s_usado\']}** para el SDM.  \\n"\n'
        '                        f"⚠️ Corrige `Ns (Celdas Serie)` = **{_sdm_est[\'_N_s_usado\']}** "\n'
        '                        f"en `Catalogo_Paneles_FV` del Excel para que todos los motores sean consistentes."\n'
        '                    )'
    ),
    desc="auto-activación: aviso N_s corregido"
)

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
