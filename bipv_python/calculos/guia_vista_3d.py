# -*- coding: utf-8 -*-
"""Guía paso a paso de 🗺️ Vista 3D (Spec 08-interfaz/guia-vista-3d, 3-oct-2026).

Se muestra al entrar a la página y resume, para un usuario que aprende, el
flujo multi-superficie con sombra 3D: sombra por string (Spec
05/sombra-por-string) y difusa en la sombra (Spec 05/difusa-sombra-por-string).
El manual del Asistente (sección 125) repite el mismo contenido.
"""
from __future__ import annotations

GUIA_TITULO = "📘 Cómo usar Vista 3D sin errores (paso a paso)"

RESUMEN = (
    "📘 ¿Primera vez aquí o cambiaste la escena? Abre «Cómo usar Vista 3D sin errores»: "
    "son 8 pasos. La sombra de balcones y vecinos se calcula por string y con la luz "
    "difusa del cielo: genera un punto por módulo con «🧮 Generar puntos» y pulsa «🌳 Calcular sombra»."
)

AYUDA_PUNTOS = (
    "✍️ Lo más seguro: «🧮 Generar un punto por módulo» (abajo, en cada superficie). Si los "
    "escribes a mano: **un punto por módulo** (una línea por módulo: x,y,z en **metros**), "
    "**0,3 m** delante de la fachada, a la altura del centro del módulo. Site Designer "
    "trabaja en milímetros: divide sus coordenadas entre 1000. Con un solo punto la app "
    "no sabe cuántos módulos quedan a la sombra y usa el promedio."
)

PASOS = (
    ("Antes de entrar",
     "Calcula el año típico en ☀️ **Recurso Solar** con la ubicación exacta del proyecto y "
     "elige el panel en 📐 Dimensionamiento. Sin año típico no se puede calcular la sombra."),
    ("Superficies",
     "Pestaña 🌞 Diagrama Solar → ⚙️ **Superficies BIPV**: agrega cada fachada o techo con su "
     "inclinación (fachada = 90°) y su azimut real (0 = N, 90 = E, 180 = S, 270 = O)."),
    ("Strings",
     "En «🔌 **Inversores** por superficie», elige para cada superficie el equipo, los módulos "
     "en serie y los strings en paralelo, y revisa los semáforos 🟢🟡🔴. Hazlo **antes** de "
     "generar los puntos: así cada punto queda ligado a su string."),
    ("Escena",
     "En «🌳 Sombra 3D por superficie», sube el JSON de **Site Designer** (File → Save Model "
     "File). Debe tener la misma ubicación del proyecto: si está a más de 0,1° la app la "
     "rechaza. El `northOffset` del archivo gira la escena hacia el norte real."),
    ("Puntos 3D",
     "Abre «🧮 Generar un punto por módulo» de cada superficie: escribe la **esquina** inferior "
     "izquierda del campo de módulos (vista desde afuera, en metros, X = Este, Y = Norte), las "
     "filas, las columnas, la orientación del módulo y si los strings van por columnas o por "
     "filas, y pulsa «🧮 Generar puntos». Filas × columnas debe ser igual a módulos en serie × "
     "strings. La app pone **un punto por módulo**, a 0,3 m de la superficie. Si escribes los "
     "puntos a mano: metros, 0,3 m delante del centro de cada módulo. Corrige toda línea en "
     "rojo y lee los avisos amarillos (punto dentro del edificio o pegado a él)."),
    ("Calcular sombra",
     "Pulsa «🌳 **Calcular sombra** de todas las superficies». La app calcula, hora a hora, "
     "cuántos módulos de **cada string** quedan a la sombra y cuánta luz pierden (**sombra por "
     "string**), y qué parte del **cielo** tapan balcones, aleros y vecinos (**luz difusa**)."),
    ("Revisar el estado",
     "Mira la tabla «Estado de la sombra por superficie»: cada superficie debe quedar en 🟢. "
     "Si aparece 🔴, lee las columnas «Motivo» y «Qué hacer», corrige y vuelve a calcular. "
     "La columna «Puntos» debe ser igual al número de módulos."),
    ("Comparar y adoptar",
     "Pulsa «🧪 Calcular **comparación física** (sin adoptar)», revisa la energía, el PR y las "
     "pérdidas de cada superficie y, si todo es coherente, «✅ **Adoptar** cálculo físico». "
     "Luego sigue con 💰 Financiero."),
)

ERRORES_FRECUENTES = (
    "Escribir las coordenadas en milímetros (como Site Designer): los puntos quedan a "
    "kilómetros del edificio y la sombra sale 0 %. Usa metros.",
    "Poner el punto sobre la fachada o dentro del edificio: la app avisa «está DENTRO del "
    "modelo» o «muy pegado»; sepáralo 0,3 m hacia afuera.",
    "Usar un solo punto por superficie: no se sabe cuántos módulos del string quedan a la "
    "sombra y la pérdida sale más baja. Escribe un punto por módulo.",
    "Subir una escena de otra ubicación: la app no la aplica. Fija en Site Designer la "
    "ubicación del proyecto y vuelve a exportar.",
    "Cambiar la escena, la orientación o el año típico y no recalcular: la sombra anterior "
    "caduca y el modo físico no la usa. Pulsa de nuevo «🌳 Calcular sombra».",
    "Abrir un proyecto guardado antes del 3-oct-2026 y esperar los cambios nuevos: hasta "
    "que vuelvas a calcular la sombra sigue el método anterior (promedio, sin difusa).",
    "Cambiar los módulos en serie o los strings en paralelo después de generar los puntos: la "
    "sombra por string ya no coincide y el modo físico lo avisa. Vuelve a generar los puntos y "
    "a calcular la sombra.",
    "Editar a mano los puntos generados: la app pierde a qué string pertenece cada punto y "
    "calcula la sombra por superficie. Si cambias algo, vuelve a generarlos.",
    "Olvidar los árboles: Site Designer no tiene transparencia, así que un árbol se "
    "comporta como un bloque sólido y da más sombra de la real.",
)


def guia_markdown() -> str:
    """Texto de la guía en Markdown (página y manual del Asistente)."""
    lineas = ["**Qué cambió (3-oct-2026):** la sombra de balcones, aleros y vecinos se calcula "
              "**por string** (cuántos módulos quedan a la sombra y cuánta luz pierden, para saber "
              "cuándo el diodo de bypass los puentea) y con la "
              "luz **difusa** del cielo que tapan. Un módulo a la sombra conserva la luz del resto "
              "del cielo.", "", "**Paso a paso:**"]
    for i, (titulo, texto) in enumerate(PASOS, 1):
        lineas.append(f"{i}. **{titulo}.** {texto}")
    lineas += ["", "**⚠️ Errores frecuentes:**"]
    lineas += [f"- {e}" for e in ERRORES_FRECUENTES]
    lineas += ["", "**✅ Valores esperados:** cielo visible 0,9–1,0 en fachadas con balcones; "
               "pérdida por sombra de 0 % a pocos % en módulos bien ubicados; si una superficie "
               "pierde más de 20 %, revisa que los puntos no estén dentro o debajo de un obstáculo."]
    return "\n".join(lineas)
