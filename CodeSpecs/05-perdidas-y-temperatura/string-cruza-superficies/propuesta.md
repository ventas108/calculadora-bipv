# Propuesta — Vista 3D: string que cruza dos superficies

**Estado:** validación

## Objetivo

Poder declarar en 🗺️ Vista 3D que los strings de un grupo tienen parte de sus
módulos en otra superficie, y que la energía publicada reste esa pérdida en
serie, hora a hora, una sola vez.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec para Vista 3D con
su PR»).

- **Dato nuevo en el grupo:** `cruce = {"uid": <otra superficie>, "modulos": k}`:
  en cada string del grupo, k de sus N serie módulos están en la otra
  superficie.
- **Validación (⚡ Diseño eléctrico):** 🔴 si la otra superficie no existe,
  no está activa o es la misma; si k no está entre 1 y N serie − 1; o si las
  dos superficies usan paneles distintos (un string es de un solo panel). El
  voltaje del string no cambia (mismos N serie módulos del mismo panel).
- **Módulos donde están:** la superficie de origen cuenta (N − k) × N
  paralelo módulos de ese grupo y la otra suma k × N paralelo. El área y la
  energía de cada superficie salen de sus módulos físicos.
- **Pérdida en serie:** hora a hora con diodos de bypass
  (`perdida_string_bypass`, Spec B), con la POA de las dos superficies y las
  fracciones (N − k)/N y k/N. La pérdida anual del string (ponderada por
  energía) L se aplica a los módulos del string en **las dos** superficies:
  PR de la superficie × (1 − L × módulos del string en ella ÷ módulos de la
  superficie). Se ve como «String que cruza» en el desglose.
- **Modos:** simplificado y bypass la usan (los dos toman el PR de la cadena
  por superficie). El **modo físico** no la modela todavía: con un string que
  cruza, no se prepara y lo explica (sin publicar números incompletos). La
  sección «🔀 6» deja fuera, con aviso, las superficies con strings que cruzan.
- Manual del Asistente con el caso de la esquina Este/Oeste.

## Alternativas descartadas

- Contar el string entero en la superficie de origen: su área podría pasar
  del área de la superficie y los k módulos de la otra usarían una POA que no
  es la suya.
- Aplicar la pérdida solo a la superficie de origen: la pérdida es del string
  completo; los módulos de la otra superficie también trabajan a la corriente
  del string.

## Fuera de alcance

- Modo físico con strings que cruzan (necesita dos geometrías y dos sombras
  3D por grupo): siguiente fase.
- Que la sección «🔀 6» (strings en paralelo en el mismo MPPT) cambie la
  energía oficial.
