"""
Parche #125 — Mostrar en modelo 3D exactamente los módulos dimensionados
=========================================================================
Modifica panel_grid_traces() en pages/9_🗺️_Vista_3D.py para respetar
el número real de paneles de Dimensionamiento (n_pan_target).

Antes: la cuadrícula llenaba toda la fachada sin importar N_paneles.
       Si se dimensionaron 24 módulos pero caben 60, el modelo mostraba 60.

Después:
  • Los primeros n_pan_target módulos se colorean con POA del mes.
  • Las posiciones restantes se muestran en gris oscuro (#2a2a3a).
  • El tooltip y el nombre de la traza muestran "24 módulos / 60 posibles".
  • Si n_pan_target ≥ capacidad (o no hay Dimensionamiento), mismo comportamiento
    que antes — fachada llena.
"""
import sys, pathlib, shutil, datetime, re

TARGET = pathlib.Path(
    "/var/www/bipv/calculadora-bipv/bipv_python/pages/9_🗺️_Vista_3D.py"
)
if not TARGET.exists():
    print(f"[ERROR] No encontrado: {TARGET}"); sys.exit(1)

src = TARGET.read_text(encoding="utf-8")

# ── Idempotencia ──────────────────────────────────────────────────────────────
if "n_capacity" in src and "color_ghost" in src:
    print("[OK] Parche #125 ya aplicado — sin cambios.")
    sys.exit(0)

ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = TARGET.with_suffix(f".py.bak_125_{ts}")
shutil.copy2(TARGET, bak)
print(f"[backup] {bak.name}")

# ── Reemplazar función panel_grid_traces ─────────────────────────────────────
OLD_FUNC = '''\
    def panel_grid_traces(w, h, pw, ph, gap, poa_val, poa_min, poa_max, n_pan_target):
        """
        Genera un Mesh3d con la cuadrícula de paneles en la fachada (Y=-0.01).
        Colorea todos los paneles con el POA del mes seleccionado.
        """
        n_cols = max(1, int(w / (pw + gap)))
        n_rows = max(1, int(h / (ph + gap)))

        # Ajustar dimensiones para que llenen la fachada uniformemente
        actual_pw = max(0.1, (w - gap * (n_cols - 1)) / n_cols)
        actual_ph = max(0.1, (h - gap * (n_rows - 1)) / n_rows)

        color = _color_poa(poa_val, poa_min, poa_max)

        all_x, all_y, all_z = [], [], []
        all_i, all_j, all_k = [], [], []
        face_colors = []
        vert = 0

        for row in range(n_rows):
            for col in range(n_cols):
                x0 = -w/2 + col * (actual_pw + gap)
                x1 = x0 + actual_pw
                z0 = row * (actual_ph + gap)
                z1 = z0 + actual_ph
                yp = -0.01   # ligeramente por delante de la fachada

                # 4 vértices del panel
                all_x += [x0, x1, x1, x0]
                all_y += [yp, yp, yp, yp]
                all_z += [z0, z0, z1, z1]

                # 2 triángulos
                all_i += [vert,   vert]
                all_j += [vert+1, vert+2]
                all_k += [vert+2, vert+3]
                face_colors += [color, color]
                vert += 4

        n_shown = n_rows * n_cols

        panels_mesh = go.Mesh3d(
            x=all_x, y=all_y, z=all_z,
            i=all_i, j=all_j, k=all_k,
            facecolor=face_colors,
            opacity=0.95,
            flatshading=True,
            showscale=False,
            name=f"Paneles BIPV ({n_shown} unid.)",
            hovertemplate=(
                f"<b>Paneles BIPV</b><br>"
                f"POA {mes_nombre}: {poa_val:.0f} kWh/m²<br>"
                f"Paneles visualizados: {n_shown}<br>"
                f"<extra></extra>"
            ),
        )'''

NEW_FUNC = '''\
    def panel_grid_traces(w, h, pw, ph, gap, poa_val, poa_min, poa_max, n_pan_target):
        """
        Genera un Mesh3d con la cuadrícula de paneles en la fachada (Y=-0.01).
        Colorea paneles instalados con POA del mes; posiciones vacías en gris.
        n_pan_target > 0 limita los módulos al número dimensionado (#125).
        """
        n_cols = max(1, int(w / (pw + gap)))
        n_rows = max(1, int(h / (ph + gap)))

        # Ajustar dimensiones para que llenen la fachada uniformemente
        actual_pw = max(0.1, (w - gap * (n_cols - 1)) / n_cols)
        actual_ph = max(0.1, (h - gap * (n_rows - 1)) / n_rows)

        n_capacity = n_rows * n_cols
        # Respetar el conteo real de módulos dimensionados (#125)
        n_active = n_capacity
        if n_pan_target and 0 < int(n_pan_target) < n_capacity:
            n_active = int(n_pan_target)

        color       = _color_poa(poa_val, poa_min, poa_max)
        color_ghost = "#2a2a3a"   # posiciones vacías — gris azulado oscuro

        all_x, all_y, all_z = [], [], []
        all_i, all_j, all_k = [], [], []
        face_colors = []
        vert = 0
        panel_count = 0

        for row in range(n_rows):
            for col in range(n_cols):
                x0 = -w/2 + col * (actual_pw + gap)
                x1 = x0 + actual_pw
                z0 = row * (actual_ph + gap)
                z1 = z0 + actual_ph
                yp = -0.01   # ligeramente por delante de la fachada

                c = color if panel_count < n_active else color_ghost

                # 4 vértices del panel
                all_x += [x0, x1, x1, x0]
                all_y += [yp, yp, yp, yp]
                all_z += [z0, z0, z1, z1]

                # 2 triángulos
                all_i += [vert,   vert]
                all_j += [vert+1, vert+2]
                all_k += [vert+2, vert+3]
                face_colors += [c, c]
                vert += 4
                panel_count += 1

        n_shown = n_active
        _ghost_label = (
            f" · {n_capacity - n_active} posiciones vacías"
            if n_active < n_capacity else ""
        )

        panels_mesh = go.Mesh3d(
            x=all_x, y=all_y, z=all_z,
            i=all_i, j=all_j, k=all_k,
            facecolor=face_colors,
            opacity=0.95,
            flatshading=True,
            showscale=False,
            name=f"Paneles BIPV ({n_shown} unid.{_ghost_label})",
            hovertemplate=(
                f"<b>Paneles BIPV</b><br>"
                f"POA {mes_nombre}: {poa_val:.0f} kWh/m²<br>"
                f"Módulos instalados: {n_shown}"
                + (f" / {n_capacity} posibles" if n_active < n_capacity else "")
                + "<br><extra></extra>"
            ),
        )'''

if OLD_FUNC in src:
    src = src.replace(OLD_FUNC, NEW_FUNC, 1)
    print("[✓] panel_grid_traces() actualizado con n_pan_target real.")
else:
    print("[ADVERTENCIA] No se encontró el bloque panel_grid_traces exacto.")
    print("  El parche puede ya estar aplicado, o la función cambió.")
    print("  Verifica manualmente en pages/9_🗺️_Vista_3D.py")

TARGET.write_text(src, encoding="utf-8")
print(f"\n[✓] Parche #125 aplicado en {TARGET.name}")
print("    pm2 restart streamlit-bipv")
