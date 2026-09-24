"""
Claves de session_state que caducan en cadena (#64 / #172).

Única fuente de verdad para invalidar resultados derivados cuando cambian las
entradas aguas arriba:

- Cambian las COORDENADAS del predio  → caduca TODO (TMY + POA + derivados).
- Cambia la GEOMETRÍA (tilt/azimuth/albedo) → el TMY del sitio sigue válido,
  pero caducan la POA y todos los derivados.
- Cambia el ÁREA o el TIPO de instalación → caducan producción, bypass,
  financiero y CO₂ (el recurso solar sigue válido; el nº de paneles no).
- Motor Óptico RECALCULA su propia POA (misma coordenada/geometría, otros
  parámetros ópticos) → caduca todo lo downstream de ESA POA: Producción,
  bypass monofacial, pérdida óhmica calculada, Financiero, CO₂ -- pero NO
  el estado multi-superficie (ver KEYS_DOWNSTREAM_MOTOR_OPTICO más abajo,
  que usa su propia POA independiente).

Sin esta limpieza, Financiero/Reporte leen E_ac_anual_kWh directamente y
entregarían TIR/payback calculados con el sol o la geometría de otro escenario.
"""
from typing import MutableMapping

# ── Estado propio del Motor Óptico: independiente del inversor ───────────────
# Fuente única para conservar la corrida óptica cuando solo cambia el inversor
# o N_serie. Cambios de sitio, geometría, panel o parámetros ópticos siguen
# invalidando estas claves mediante KEYS_DERIVADOS_POA.
ESTADO_MOTOR_OPTICO = (
    "motor_optico_ok",
    "motor_optico_result_df",
    "motor_optico_summary",
    "poa_efectiva_df",
    "poa_sin_termico_df",
    "poa_efectiva_anual_kWh_m2",
    "motor_optico_b0",
    "motor_optico_tau",
    "motor_optico_k_bipv",
    "motor_optico_noct",
    "motor_optico_coef_temp",
    "motor_optico_f_iam_dif",
    "motor_optico_k_soil_vert",
    "motor_optico_soiling_custom",
    "motor_optico_soiling_config",
)

# ── Derivados de la POA: producción y todo lo que cuelga de ella ─────────────
KEYS_DERIVADOS_POA = (
    # Motor Óptico (Página 5b) — estado, parámetros y POA corregidas
    # poa_efectiva_df    : POA tras IAM + soiling + térmico (visualización / Financiero)
    # poa_sin_termico_df : POA tras IAM + soiling SIN térmico (G_eff del SDM)
    # Ambas deben invalidarse juntas para evitar que Producción use la POA
    # antigua cuando cambian coordenadas o geometría.
    *ESTADO_MOTOR_OPTICO,
    # Producción (Página 6)
    "produccion_ok", "produccion_modo_iv", "E_ac_anual_kWh", "PR_sistema",
    "res_produccion", "res_produccion_base", "res_produccion_iv",
    # Bypass — resultados y flags (Página 5); si quedan vivos, Producción
    # re-aplica sombras viejas a la producción nueva. Debe coincidir con
    # KEYS_BYPASS_RESULTADO (nota de sincronización más abajo).
    "E_ac_anual_kWh_bypass",
    "bypass_ok", "bypass_result", "bypass_p_shade",
    "bypass_n_series_usado", "bypass_n_parallel_usado", "bypass_panel_usado",
    "bypass_horizonte_info", "bypass_horizonte_incluido",
    "kwh_bypass_anual",
    "bypass_modo_usado", "bypass_modo_agregacion_usado",
    "bypass_multisup_ok", "bypass_multisup_resultados",
    # Multi-superficie (Página 9)
    "E_ac_anual_kWh_multisup", "poa_df_multisup",
    "area_total_multisup", "multisup_desglose", "multisup_activo",
    # Pérdida óhmica de cableado calculada (Página 20, 7-sep-2026) -- la
    # vigencia (mismo panel/inversor/N_serie) ya se verifica en Producción
    # antes de aplicarla, pero también debe caducar aquí para no dejar un
    # cálculo de otro escenario vivo indefinidamente en session_state.
    "perdida_ohmica_unifilar",
    # ── A partir de aquí: agregado 17-sep-2026 (auditoría de invalidación
    # downstream de Motor Óptico). Colocado DESPUÉS de perdida_ohmica_unifilar
    # a propósito: test_pagina_perdida_ohmica.py busca esa clave dentro de los
    # primeros 2000 caracteres de esta tupla; agregar contenido ANTES la
    # empujaría fuera de esa ventana. La categoría real de cada clave está en
    # su propio comentario, no en su posición dentro de la tupla.
    #
    # Producción (Página 6) -- salidas de la simulación que faltaban en la
    # auditoría anterior (E_ac_anual_kWh/PR_sistema/res_produccion* ya
    # estaban arriba).
    "E_dc_anual_kWh", "Y_f_kWh_kWp", "df_mensual_produccion", "verificacion_jrc",
    # Diagnóstico real vs. simulado (Página 6, sección "#28"; consumido por
    # 📄 Reporte PDF) -- SOLO el lado DERIVADO de la simulación/POA (E_sim,
    # PR_esperado, PR_conv/corr -- estos dependen de HSP mensual, que sale de
    # la POA -- pérdida térmica, clasificación semáforo por mes). NO incluye
    # diag_real_kwh ni diag_total_real_kwh: son lecturas REALES que el
    # usuario tipea a mano (inversor/medidor bidireccional), independientes
    # de la POA -- se conservan para que el usuario no tenga que reescribirlas;
    # la comparación se recalcula sola la próxima vez que Producción corra.
    "df_diagnostico_real", "diag_meses_rojo", "diag_meses_amarillo",
    "diag_total_sim_kwh", "diag_total_stc_kwh", "diag_pr_conv_global",
    "diag_pr_corr_global", "diag_perdida_t_pct", "diag_perdida_t_kwh",
    "diag_gamma_pct",
    # Financiero cacheado (Página 7)
    "financiero_ok", "comp_financiero", "comp_financiero_p90",
    "metricas_financiero", "metricas_financiero_p90",
    # Impacto CO₂ (Página 12)
    "impacto_co2_ok", "co2_anual_t", "co2_total_t", "co2_total_prom_t",
    "co2_total_marg_t", "co2_arboles_equiv", "co2_hogares_equiv",
    "co2_km_vehiculo_equiv", "co2_valor_bonos_usd",
    # Multi-superficie (Página 9) -- origen de la energía publicada y datos
    # que solo existen con origen físico (Spec 05/publicacion-energia-
    # multisuperficie). Caducan junto con E_ac_anual_kWh_multisup.
    "multisup_origen", "multisup_perdida_bus_kWh", "_multisup_proyecto_fisico",
)

# Cambiar inversor/N_serie no cambia sitio, panel, geometría, IAM, soiling,
# NOCT ni POA. Sí caduca toda salida eléctrica, energética y financiera
# calculada con la configuración anterior.
KEYS_DERIVADOS_INVERSOR = tuple(
    k for k in KEYS_DERIVADOS_POA if k not in ESTADO_MOTOR_OPTICO
)


def invalidar_por_cambio_inversor(session_state: MutableMapping) -> list[str]:
    """Invalida resultados dependientes del inversor conservando Motor Óptico.

    Es idempotente, acepta ``st.session_state`` o un diccionario de prueba y
    retorna únicamente las claves que existían y fueron eliminadas.
    """
    eliminadas = [k for k in KEYS_DERIVADOS_INVERSOR if k in session_state]
    for k in eliminadas:
        session_state.pop(k, None)
    return eliminadas

# ── Resultado de bypass diodes MONOFACIAL (Página 5) — POA inconsistente ─────
# seleccionar_poa_bypass() (calculos/mismatch_bypass.py) devuelve G_eff=None
# cuando el Motor Óptico está activo pero falta poa_sin_termico_df -- un
# bypass_result calculado ANTES de esa inconsistencia no deja de mostrarse
# solo, ni bypass_ok se apaga solo. Sin esta caducidad explícita, Página 5
# seguiría mostrando el bypass anterior (btn_bypass deshabilitado, pero
# `if btn_bypass or bypass_ok` sigue leyendo bypass_result), y Producción
# --incluso visitada DIRECTAMENTE, sin pasar por Página 5-- seguiría restando
# kwh_bypass_anual / E_ac_anual_kWh_bypass de una POA que ya no es la vigente.
#
# Estas 12 claves son exactamente las que escribe la corrida MONOFACIAL del
# bypass (pages/5_🔀_Mismatch.py, sección "5. Bypass Diodes"): bypass_ok,
# bypass_result y sus insumos (p_shade, N_series/N_parallel/panel usados,
# horizonte, modo de alineación/agregación usados) más las energías que
# Producción deriva de ese resultado (E_ac_anual_kWh_bypass,
# kwh_bypass_anual -- ver pages/6_📊_Produccion.py:1064-1065).
#
# Subconjunto intencionalmente MÁS ESTRECHO que KEYS_DERIVADOS_POA: invalidar
# todo KEYS_DERIVADOS_POA aquí borraría también motor_optico_ok/summary y
# demás resultados válidos del Motor Óptico -- la POA sin térmico es lo que
# falta, no el Motor Óptico en sí.
#
# NO incluye bypass_multisup_ok / bypass_multisup_resultados a propósito:
# esas dos claves pertenecen a una corrida SEPARADA e independiente del
# bypass en modo multi-superficie (pages/9_🗺️_Vista_3D.py), con su propia
# fuente de POA (poa_df_multisup) y su propio ciclo de vida -- mezclarlas
# aquí las invalidaría cada vez que el bypass MONOFACIAL se recalcula, sin
# que exista evidencia de que comparten la misma inconsistencia. La
# coherencia de POA en modo multi-superficie queda como riesgo pendiente,
# sin corregir en este cambio (ver informe de esta ronda).
#
# Nota de sincronización (17-sep-2026): la sección "Bypass" de
# KEYS_DERIVADOS_POA (arriba) debe incluir estas mismas 10 claves (más las
# 2 de KEYS_BYPASS_MULTISUP_RESULTADO). Ya se desincronizaron una vez -- a
# KEYS_DERIVADOS_POA le faltaban bypass_horizonte_info,
# bypass_horizonte_incluido y bypass_modo_agregacion_usado, agregadas aquí
# en rondas posteriores sin reflejarse allá -- por lo que un cambio de
# coordenadas/geometría NO las invalidaba. test_keys_downstream_motor_optico_
# invariantes_arquitectonicos() (tests/test_seleccion_poa_bypass_pagina5.py)
# ahora vigila `set(KEYS_BYPASS_RESULTADO) <= set(KEYS_DERIVADOS_POA)` para
# que no vuelva a pasar en silencio.
KEYS_BYPASS_RESULTADO = (
    "bypass_ok",
    "bypass_result",
    "bypass_p_shade",
    "bypass_n_series_usado",
    "bypass_n_parallel_usado",
    "bypass_panel_usado",
    "bypass_horizonte_info",
    "bypass_horizonte_incluido",
    "bypass_modo_usado",
    "bypass_modo_agregacion_usado",
    "E_ac_anual_kWh_bypass",
    "kwh_bypass_anual",
)

# ── Bypass MULTI-SUPERFICIE (Página 9) — ciclo de vida separado ──────────────
# Deliberadamente NO forma parte de KEYS_BYPASS_RESULTADO (ver comentario
# arriba). Documentado aquí para que quede explícito qué claves existen y
# por qué NO se tocan desde la invalidación del bypass monofacial.
KEYS_BYPASS_MULTISUP_RESULTADO = (
    "bypass_multisup_ok",
    "bypass_multisup_resultados",
)

# ── Multi-superficie NO-bypass (Página 9) — POA propia, independiente ────────
# E_ac_anual_kWh_multisup / poa_df_multisup / area_total_multisup /
# multisup_desglose / multisup_activo se calculan íntegramente en
# pages/9_🗺️_Vista_3D.py a partir de una POA por superficie (geometría propia
# de cada superficie 3D), NUNCA de poa_sin_termico_df ni de poa_efectiva_df
# del Motor Óptico (auditado 17-sep-2026: pages/9_🗺️_Vista_3D.py no lee
# motor_optico_ok ni ninguna de las dos POA del Motor Óptico). Por eso se
# excluye de KEYS_DOWNSTREAM_MOTOR_OPTICO más abajo -- invalidarlo junto con
# el Motor Óptico borraría estado independiente sin justificación física.
#
# Nota: SÍ sigue formando parte de KEYS_DERIVADOS_POA (arriba), que se usa
# para cambios de COORDENADAS -- ahí sí depende del sitio, igual que poa_df.
KEYS_MULTISUP_ESTADO = (
    "E_ac_anual_kWh_multisup", "poa_df_multisup",
    "area_total_multisup", "multisup_desglose", "multisup_activo",
    "multisup_origen", "multisup_perdida_bus_kWh", "_multisup_proyecto_fisico",
)

# ── Downstream de Motor Óptico (Página 5b) — TODO lo que depende de SU POA ───
# Al recalcular la cascada óptica, Motor Óptico publica una poa_efectiva_df /
# poa_sin_termico_df NUEVAS -- cualquier resultado ya calculado con la POA
# ANTERIOR (Producción, bypass monofacial, pérdida óhmica, Financiero, CO₂)
# deja de ser válido en el mismo instante, sin que el usuario tenga que
# visitar cada página para notarlo.
#
# Derivada de KEYS_DERIVADOS_POA (fuente única) restándole el estado
# multi-superficie, que usa su propia POA independiente (ver
# KEYS_MULTISUP_ESTADO / KEYS_BYPASS_MULTISUP_RESULTADO arriba) -- así no se
# duplica la lista de claves "downstream" a mano, y cualquier clave que se
# agregue a KEYS_DERIVADOS_POA en el futuro queda automáticamente cubierta
# aquí también, salvo que sea multi-superficie.
KEYS_DOWNSTREAM_MOTOR_OPTICO = tuple(
    k for k in KEYS_DERIVADOS_POA
    if k not in KEYS_MULTISUP_ESTADO and k not in KEYS_BYPASS_MULTISUP_RESULTADO
)


def invalidar_downstream_motor_optico(session_state: MutableMapping) -> list[str]:
    """
    Invalida TODO resultado que depende de la POA del Motor Óptico: su
    propio estado (motor_optico_ok, poa_efectiva_df, poa_sin_termico_df,
    parámetros ópticos), Producción, bypass monofacial, pérdida óhmica
    calculada, Financiero e impacto CO₂ -- ver KEYS_DOWNSTREAM_MOTOR_OPTICO.

    Debe llamarse ANTES de publicar la nueva poa_efectiva_df/
    poa_sin_termico_df en pages/5b_🔆_Motor_Optico.py: esa misma página
    republica de inmediato sus propias claves con los valores recién
    calculados, así que invalidarlas aquí primero solo evita que un estado a
    medio camino sobreviva si el script se interrumpe entre la invalidación
    y la publicación -- lo que SÍ importa es que produccion_ok, bypass_ok,
    financiero_ok, impacto_co2_ok, etc. queden inválidos de inmediato.

    Deliberadamente NO toca el estado multi-superficie (Página 9): calcula
    su propia POA de forma independiente, no depende de la POA del Motor
    Óptico (ver KEYS_DOWNSTREAM_MOTOR_OPTICO).

    Acepta cualquier MutableMapping (session_state de Streamlit o un dict
    plano en pruebas). Es idempotente. Retorna las claves que existían y
    fueron eliminadas.
    """
    eliminadas = [k for k in KEYS_DOWNSTREAM_MOTOR_OPTICO if k in session_state]
    for k in eliminadas:
        session_state.pop(k, None)
    return eliminadas


# ── Recurso solar (Página 2) — POA y agregados; SIN tmy_df ───────────────────
KEYS_RECURSO_SOLAR_POA = (
    "recurso_solar_ok", "poa_df", "poa_anual_kWh_m2",
    "ganancia_bifacial_pct",
    # Verificación cruzada PVGIS vs PVWatts (6-sep-2026) -- depende del sitio
    # (lat/lon) Y de la geometría (tilt/azimuth), igual que poa_df; debe
    # caducar junto con él para no mostrar una comparación de otra
    # ubicación/orientación como si fuera la vigente.
    "pvwatts_cross_check",
)

# ── Recurso solar completo — incluye el TMY del sitio ────────────────────────
KEYS_RECURSO_SOLAR = KEYS_RECURSO_SOLAR_POA + (
    "tmy_df", "tmy_ciudad", "ghi_anual_kWh_m2", "t_media_anual",
    "zona_geo_coords",
)
