# Spec — Modelo IV de paneles BIPV de capa fina (CIGS) sin parámetros de laboratorio

**Estado:** validación

## Alcance de la fase

Estimación del modelo de un diodo (SDM) desde la ficha técnica
(`calculos/modelo_iv.py`), que usan 🔬 Motor IV, 📊 Producción y el modo
físico de 🗺️ Vista 3D; dato nuevo en 📋 Catálogo de Paneles.

## Problema a resolver

El usuario (1-oct-2026) va a trabajar con paneles BIPV de capa fina en Vista
3D y preguntó cómo resolver la falta de I_L, I_o, Rs, Rsh y a_ref, que las
fichas no traen. Envió como ejemplo la ficha del MiaSolé FLEX-03N 1,7 m
(CIGS flexible, 70–90 W). Con esa ficha:

1. `estimar_sdm_desde_ficha` no reconoce «CIGS» ni «CIS» (el catálogo usa
   «CIS»): lo trata como silicio monocristalino (banda prohibida 1,12 eV en
   vez de 1,15 eV, factor de idealidad 1,05 en vez de 1,35, resistencia en
   paralelo de silicio). Las constantes de CIGS existen en
   `CONSTANTES_TECNOLOGIA` pero el estimador nunca llega a ellas.
2. La ficha no trae el número de celdas en serie (habitual en capa fina):
   la estimación devuelve `None` y Motor IV no funciona con ese panel.
3. No hay forma de usar el dato de rendimiento a baja irradiancia (200
   W/m²) que traen muchas fichas BIPV, que es lo que más distingue a la
   capa fina del silicio en fachadas y cielos nublados.

## Contexto

El SDM estimado reproduce la ficha en STC (validación ≤ 6 %). Para silicio
el método reproduce la referencia estándar internacional dentro de 0,1
puntos de PR. El ASP-ST1-T40 (CdTe) tiene parámetros de laboratorio propios.
«a-Si», «Thin Film» y «Otro» no tienen constantes: hoy se tratan como
silicio sin aviso.
